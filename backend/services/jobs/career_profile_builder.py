from __future__ import annotations

import re
from typing import Iterable

from backend.services.jobs.career_profile import CareerProfile
from backend.services.jobs.role_taxonomy import (
    AI_ML,
    BACKEND,
    DATA,
    DEVOPS_CLOUD,
    FRONTEND,
    FULL_STACK,
    SOFTWARE_ENGINEERING,
    UNKNOWN,
    RoleClassification,
    classify_resume,
)


# ============================================================
# ROLE DISPLAY NAMES
# ============================================================

ROLE_DISPLAY_NAMES: dict[str, str] = {
    SOFTWARE_ENGINEERING: "Software Engineer",
    BACKEND: "Backend Engineer",
    FRONTEND: "Frontend Engineer",
    FULL_STACK: "Full Stack Developer",
    AI_ML: "AI/ML Engineer",
    DATA: "Data Engineer",
    DEVOPS_CLOUD: "DevOps / Cloud Engineer",
}


# ============================================================
# COMPATIBLE CAREER ROLES
# ============================================================

COMPATIBLE_ROLES: dict[str, list[str]] = {
    BACKEND: [
        "Backend Engineer",
        "Software Engineer",
        "Full Stack Developer",
        "API Developer",
        "Python Developer",
    ],

    FRONTEND: [
        "Frontend Engineer",
        "Software Engineer",
        "Full Stack Developer",
        "React Developer",
        "Web Developer",
    ],

    FULL_STACK: [
        "Full Stack Developer",
        "Software Engineer",
        "Backend Engineer",
        "Frontend Engineer",
        "Web Developer",
    ],

    AI_ML: [
        "AI Engineer",
        "Machine Learning Engineer",
        "AI/ML Engineer",
        "Software Engineer",
        "Data Scientist",
    ],

    DATA: [
        "Data Engineer",
        "Data Analyst",
        "Data Scientist",
        "Analytics Engineer",
        "Software Engineer",
    ],

    DEVOPS_CLOUD: [
        "DevOps Engineer",
        "Cloud Engineer",
        "Site Reliability Engineer",
        "Platform Engineer",
        "Software Engineer",
    ],

    SOFTWARE_ENGINEERING: [
        "Software Engineer",
        "Backend Engineer",
        "Frontend Engineer",
        "Full Stack Developer",
        "Application Developer",
    ],
}


# ============================================================
# EXPERIENCE LEVEL
# ============================================================

EXPERIENCE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        "intern",
        (
            "intern",
            "internship",
            "interned",
        ),
    ),
    (
        "fresher",
        (
            "fresher",
            "recent graduate",
            "recently graduated",
            "new graduate",
            "entry level",
            "entry-level",
            "graduate",
        ),
    ),
    (
        "senior",
        (
            "senior engineer",
            "senior developer",
            "senior software",
            "staff engineer",
            "principal engineer",
            "lead engineer",
            "tech lead",
            "technical lead",
        ),
    ),
]


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()

    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _detect_experience_level(
    resume_text: str,
) -> str:

    text = _normalize_text(resume_text)

    # Explicit experience-year detection.
    year_matches = re.findall(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        text,
    )

    if year_matches:
        years = max(float(value) for value in year_matches)

        if years >= 5:
            return "senior"

        if years >= 2:
            return "mid"

        if years > 0:
            return "entry"

    # Explicit phrases.
    for level, patterns in EXPERIENCE_PATTERNS:

        for pattern in patterns:

            if pattern in text:
                return level

    return "unknown"


# ============================================================
# SKILL EXTRACTION
# ============================================================

SKILL_ALIASES: dict[str, str] = {
    "node.js": "Node.js",
    "node js": "Node.js",
    "nodejs": "Node.js",

    "react.js": "React",
    "react js": "React",
    "react": "React",

    "next.js": "Next.js",
    "nextjs": "Next.js",

    "typescript": "TypeScript",
    "javascript": "JavaScript",

    "python": "Python",
    "java": "Java",

    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",

    "express": "Express.js",
    "express.js": "Express.js",

    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",

    "redis": "Redis",

    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",

    "docker": "Docker",
    "kubernetes": "Kubernetes",

    "terraform": "Terraform",

    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "natural language processing": "NLP",
    "nlp": "NLP",

    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",

    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",

    "pandas": "Pandas",
    "numpy": "NumPy",

    "git": "Git",
    "github": "GitHub",

    "sql": "SQL",
    "graphql": "GraphQL",

    "rest api": "REST API",
    "rest apis": "REST API",

    "langchain": "LangChain",
    "langgraph": "LangGraph",

    "openai": "OpenAI",
    "groq": "Groq",

    "selenium": "Selenium",
    "playwright": "Playwright",
}


def _extract_skills(
    resume_text: str,
    resume_skills: Iterable[str] | None = None,
) -> list[str]:

    text = _normalize_text(resume_text)

    found: dict[str, str] = {}

    # Explicit skills supplied by the resume pipeline.
    for skill in resume_skills or []:

        if not skill:
            continue

        normalized = _normalize_text(skill)

        if normalized in SKILL_ALIASES:
            canonical = SKILL_ALIASES[normalized]
        else:
            canonical = str(skill).strip()

        if canonical:
            found[canonical.lower()] = canonical

    # Extract known skills from resume text.
    for alias, canonical in SKILL_ALIASES.items():

        if alias in text:
            found[canonical.lower()] = canonical

    return sorted(
        found.values(),
        key=lambda value: value.lower(),
    )


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

EDUCATION_PATTERNS = (
    "b.tech",
    "btech",
    "b.e",
    "be ",
    "bachelor of technology",
    "bachelor of engineering",
    "bachelor's degree",
    "computer science",
    "information technology",
    "master of technology",
    "m.tech",
    "mtech",
    "mca",
    "master of computer applications",
    "mba",
    "bca",
    "b.sc",
    "bsc",
)


def _extract_education(
    resume_text: str,
) -> list[str]:

    text = _normalize_text(resume_text)

    education: list[str] = []

    for pattern in EDUCATION_PATTERNS:

        if pattern in text:

            display = pattern.strip()

            if display not in education:
                education.append(display)

    return education


# ============================================================
# PROJECT EXTRACTION
# ============================================================

PROJECT_MARKERS = (
    "project",
    "projects",
    "built",
    "developed",
    "developed an",
    "developed a",
    "created",
    "implemented",
)


def _extract_projects(
    resume_text: str,
) -> list[str]:

    lines = resume_text.splitlines()

    projects: list[str] = []

    inside_project_section = False

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            continue

        normalized = _normalize_text(line)

        # Start of project section.
        if normalized in {
            "projects",
            "project",
            "academic projects",
            "personal projects",
            "technical projects",
        }:
            inside_project_section = True
            continue

        # Stop at common following sections.
        if normalized in {
            "experience",
            "work experience",
            "education",
            "skills",
            "certifications",
            "achievements",
            "internships",
        }:
            inside_project_section = False
            continue

        if inside_project_section:

            cleaned = line.lstrip("-•* ").strip()

            if len(cleaned) >= 4:

                if cleaned not in projects:
                    projects.append(cleaned)

    return projects[:15]


# ============================================================
# PRIMARY ROLE
# ============================================================

def _primary_role(
    classification: RoleClassification,
) -> str:

    return ROLE_DISPLAY_NAMES.get(
        classification.family,
        "Technology Professional"
        if classification.domain == "technology"
        else "Professional",
    )


# ============================================================
# CAREER PROFILE BUILDER
# ============================================================

def build_career_profile(
    *,
    resume_text: str,
    resume_skills: Iterable[str] | None = None,
    target_roles: Iterable[str] | None = None,
) -> CareerProfile:

    classification = classify_resume(
        resume_text=resume_text,
        resume_skills=resume_skills,
        target_roles=target_roles,
    )

    skills = _extract_skills(
        resume_text=resume_text,
        resume_skills=resume_skills,
    )

    education = _extract_education(
        resume_text=resume_text,
    )

    projects = _extract_projects(
        resume_text=resume_text,
    )

    experience_level = _detect_experience_level(
        resume_text=resume_text,
    )

    targets = [
        str(role).strip()
        for role in (target_roles or [])
        if role and str(role).strip()
    ]

    compatible_roles = COMPATIBLE_ROLES.get(
        classification.family,
        [],
    )

    # Put explicitly selected target roles first.
    merged_roles: list[str] = []

    for role in targets + compatible_roles:

        if role not in merged_roles:
            merged_roles.append(role)

    return CareerProfile(
        domain=classification.domain,
        primary_role=_primary_role(classification),
        role_family=classification.family,
        compatible_roles=merged_roles,
        experience_level=experience_level,
        skills=skills,
        education=education,
        projects=projects,
        target_roles=targets,
        confidence=classification.confidence,
        matched_signals=list(
            classification.matched_signals
        ),
    )