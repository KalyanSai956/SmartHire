import re
from typing import Dict, List, Any

import numpy as np
from backend.services.embedder import FastEmbedder as SentenceTransformer  # ONNX replacement, same .encode() API

from backend.models.schemas import (
    AdvancedATSResult,
    ATSKeywordAnalysis,
    ATSScoreBreakdown,
)


# ============================================================
# NORMALIZATION / ALIASES
# ============================================================

TECH_SYNONYMS = {
    # Frontend / Backend
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",

    "nodejs": "node.js",
    "node js": "node.js",

    "expressjs": "express.js",
    "express js": "express.js",

    # Databases
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "postgres": "postgresql",
    "postgre": "postgresql",

    # Machine Learning / AI
    "machine-learning": "machine learning",
    "machine learning techniques": "machine learning",
    "ml": "machine learning",

    "artificial intelligence": "ai",
    "artificial-intelligence": "ai",

    "deep-learning": "deep learning",
    "deep learning techniques": "deep learning",

    "natural language processing": "nlp",

    "generative artificial intelligence": "generative ai",
    "generative ai models": "generative ai",
    "generative ai model": "generative ai",
    "gen ai": "generative ai",
    "genai": "generative ai",

    "large language model": "llm",
    "large language models": "llm",
    "large-language-model": "llm",
    "large-language-models": "llm",
    "llms": "llm",

    # APIs
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",

    "fast api": "fastapi",
    "fast apis": "fastapi",

    # Python ecosystem
    "scikit learn": "scikit-learn",
    "scikit-learn library": "scikit-learn",

    "huggingface": "hugging face",

    # Statistics
    "statistical modelling": "statistical modeling",

    # Git
    "git hub": "github",

    # CI/CD
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",
    "ci cd": "ci/cd",

    # Docker
    "docker containerization": "docker",
    "containerization": "docker",

    # Common technical phrase variants
    "python programming": "python",
    "java programming": "java",
    "javascript programming": "javascript",
    "data structures and algorithms": "data structures and algorithms",
    "data structure and algorithms": "data structures and algorithms",
    "python programming": "python",
"python development": "python",

"deep learning techniques": "deep learning",

"on-premise": "on-premises",
"on premise": "on-premises",
"on premise deployments": "on-premises",
"on-premise deployments": "on-premises",

"generative ai model": "generative ai",
"generative ai models": "generative ai",
"generative ai model development": "generative ai",
"generative ai model developments": "generative ai",

"prompt engineering strategies": "prompt engineering",
}


# ============================================================
# ATOMIC TECHNICAL SKILLS
# ============================================================

TECH_SKILLS = {
    # Languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "go",
    "golang",
    "rust",
    "kotlin",
    "swift",
    "php",
    "ruby",
    "scala",

    # Frontend
    "react",
    "angular",
    "vue",
    "next.js",
    "html",
    "css",
    "bootstrap",
    "tailwind",
    "redux",

    # Backend
    "node.js",
    "express.js",
    "fastapi",
    "django",
    "flask",
    "spring",
    "spring boot",
    "rest api",
    "graphql",

    # Databases
    "mongodb",
    "mysql",
    "postgresql",
    "sqlite",
    "redis",
    "oracle",
    "sql",

    # Cloud
    "aws",
    "azure",
    "gcp",
    "google cloud",

    # DevOps
    "docker",
    "kubernetes",
    "terraform",
    "jenkins",
    "github actions",
    "ci/cd",

    # Version control
    "git",
    "github",
    "gitlab",
    "bitbucket",

    # AI / ML
    "ai",
    "machine learning",
    "deep learning",
    "generative ai",
    "llm",
    "nlp",
    "computer vision",

    # ML frameworks
    "tensorflow",
    "pytorch",
    "keras",
    "scikit-learn",
    "xgboost",

    # AI / NLP
    "spacy",
    "nltk",
    "hugging face",
    "sentence transformers",
    "transformers",
    "openai",
    "groq",
    "groq api",

    # Data
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "plotly",
    "jupyter notebook",

    # Computer vision
    "opencv",
    "dlib",

    # AI model families / techniques
    "gpt",
    "vae",
    "gan",

    # Other technical tools
    "postman",
    "supabase",
    "firebase",
}


# ============================================================
# TECHNICAL CONCEPTS
# ============================================================

TECH_CONCEPTS = {
    "data structures",
    "data structures and algorithms",
    "algorithms",

    "object oriented programming",
    "oop",

    "software architecture",
    "system design",
    "microservices",

    "api development",
    "backend development",
    "frontend development",
    "full stack development",

    "cloud computing",
    "cloud architecture",

    "model deployment",
    "model optimization",
    "model training",
    "model evaluation",

    "statistical modeling",
    "neural networks",
    "convolutional neural networks",
    "recurrent neural networks",

    "transformers",

    "prompt engineering",
    "prompt strategies",

    "speech recognition",
    "voice recognition",

    "chatbots",

    "recommendation systems",

    "data analysis",
    "data preprocessing",
    "feature engineering",
    "data visualization",

    "machine learning pipelines",
    "ml pipelines",
    "ai pipelines",

    "rag",
    "retrieval augmented generation",
    "vector databases",
    "semantic search",
    "embeddings",

    "generative models",

    "agile",
    "scrum",

    "on-premises",
    "production ai",
}


# ============================================================
# EDUCATION / HR / BOILERPLATE PHRASES
#
# These should NEVER become ATS keywords.
# ============================================================

EXCLUDED_PHRASES = {
    # Education
    "ph.d",
    "phd",
    "master's degree",
    "masters degree",
    "bachelor's degree",
    "bachelors degree",
    "bachelor degree",
    "related field",
    "computer science degree",
    "degree in computer science",

    # Experience requirements
    "years of experience",
    "year of experience",
    "minimum experience",
    "professional experience",

    # Generic recruitment language
    "job description",
    "job requirements",
    "required qualifications",
    "preferred qualifications",
    "qualifications",
    "responsibilities",
    "responsibility",
    "candidate",
    "candidates",
    "successful candidate",

    # Generic corporate language
    "fast paced environment",
    "fast-paced environment",
    "team environment",
    "business objectives",
    "business goals",
    "organizational goals",
    "best practices",
    "excellent communication skills",
    "strong communication skills",
    "problem solving skills",
    "analytical skills",
    "critical thinking",
    "creative thinking",
}


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "might",
    "must",
    "of",
    "on",
    "or",
    "our",
    "ours",
    "she",
    "should",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "under",
    "up",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "within",
    "would",
    "you",
    "your",

    "use",
    "uses",
    "used",
    "using",

    "build",
    "builds",
    "built",

    "develop",
    "develops",
    "developing",
    "developed",

    "create",
    "creates",
    "creating",
    "created",

    "work",
    "works",
    "working",

    "ensure",
    "ensures",
    "ensuring",

    "provide",
    "provides",
    "providing",

    "support",
    "supports",
    "supporting",

    "implement",
    "implements",
    "implementing",
    "implemented",
}


# ============================================================
# GENERIC TERMS
# ============================================================

GENERIC_TERMS = {
    "experience",
    "knowledge",
    "strong",
    "ability",
    "skills",
    "skill",
    "development",
    "developer",
    "developers",
    "application",
    "applications",
    "software",
    "engineering",
    "engineer",
    "engineers",
    "team",
    "teams",
    "environment",
    "systems",
    "system",
    "project",
    "projects",
    "requirements",
    "requirement",
    "scalable",
    "solutions",
    "solution",
    "users",
    "user",
    "process",
    "processes",
    "platform",
    "platforms",
    "role",
    "roles",
    "candidate",
    "candidates",
    "company",
    "organization",
    "organizations",
    "business",
    "businesses",
    "information",
    "details",
    "example",
    "examples",
    "workflow",
    "workflows",
    "objective",
    "objectives",
    "goal",
    "goals",
    "responsibility",
    "responsibilities",
    "qualification",
    "qualifications",
    "education",
    "degree",
    "degrees",
    "year",
    "years",
    "time",
    "times",
    "part",
    "parts",
    "various",
    "different",
    "multiple",
    "additional",
    "overall",
    "related",
    "relevant",
    "effective",
    "proper",
    "latest",
    "current",
    "quality",
    "excellence",
    "professional",
    "professionals",
    "seniority",
    "summary",
    "communication",
    "communications",
    "communicates",
    "collaboratively",
    "independently",
    "proactive",
    "mindset",
    "critical",
    "critically",
    "creative",
    "creatively",
    "innovative",
    "innovation",
    "opportunities",
    "advancements",
    "researchers",
    "stakeholders",
    "non-technical",
    "technical",
    "documentation",
    "specifications",
    "guides",
    "presentations",
    "best",
    "practices",
    "standards",
    "within",
    "closely",
    "multifunctional",
    "align",
    "alignment",
    "drives",
    "driving",
    "decisions",
    "decision",
    "insights",
    "accuracy",
    "performance",
    "efficiency",
    "capabilities",
    "approaches",
    "methodologies",
    "strategies",
    "outputs",
    "output",
    "products",
    "product",
    "needs",
    "need",
    "possess",
    "possesses",
    "familiar",
    "familiarity",
    "proficiency",
    "demonstrable",
    "clear",
    "concise",
    "diverse",
    "audiences",
    "apply",
    "applies",
    "applied",
    "handling",
    "formats",
    "sources",
}


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize(text: str) -> str:
    if not text:
        return ""

    value = str(text).lower()

    # Remove obvious education / HR phrases before matching.
    for phrase in sorted(
        EXCLUDED_PHRASES,
        key=len,
        reverse=True,
    ):
        value = value.replace(phrase, " ")

    # Normalize aliases.
    for alias, canonical in sorted(
        TECH_SYNONYMS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        value = value.replace(alias, canonical)

    # Normalize common punctuation.
    value = re.sub(r"[/|]", " ", value)
    value = re.sub(r"[,:;()\[\]{}]", " ", value)

    # Normalize apostrophes.
    value = value.replace("'", "")

    # Keep useful technical punctuation:
    # +, #, ., -, /
    value = re.sub(r"\s+", " ", value).strip()

    return value


def _canonical(term: str) -> str:
    if not term:
        return ""

    value = str(term).lower().strip()

    for alias, canonical in sorted(
        TECH_SYNONYMS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if value == alias:
            return canonical

    return value


def _term_present(term: str, text: str) -> bool:
    if not term or not text:
        return False

    normalized_term = _normalize(term)
    normalized_text = _normalize(text)

    if not normalized_term:
        return False

    pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"

    return re.search(
        pattern,
        normalized_text,
        flags=re.IGNORECASE,
    ) is not None


def _dedupe_terms(terms: List[str]) -> List[str]:
    result = []
    seen = set()

    for term in terms:
        canonical = _canonical(term)

        if not canonical:
            continue

        if canonical in seen:
            continue

        seen.add(canonical)
        result.append(canonical)

    return result


# ============================================================
# RESUME TEXT
# ============================================================

def _resume_text(resume_profile: Any) -> str:
    if resume_profile is None:
        return ""

    parts: List[str] = []

    contact = getattr(
        resume_profile,
        "contact",
        None,
    )

    if contact:
        for field in (
            "name",
            "email",
            "phone",
            "linkedin",
            "github",
            "portfolio",
        ):
            value = getattr(
                contact,
                field,
                None,
            )

            if value:
                parts.append(str(value))

    summary = getattr(
        resume_profile,
        "summary",
        None,
    )

    if summary:
        parts.append(str(summary))

    for education in getattr(
        resume_profile,
        "education",
        [],
    ) or []:
        for field in (
            "institution",
            "degree",
            "field_of_study",
            "location",
            "start_date",
            "end_date",
            "grade",
        ):
            value = getattr(
                education,
                field,
                None,
            )

            if value:
                parts.append(str(value))

    for experience in getattr(
        resume_profile,
        "experience",
        [],
    ) or []:

        for field in (
            "company",
            "role",
            "location",
            "start_date",
            "end_date",
        ):
            value = getattr(
                experience,
                field,
                None,
            )

            if value:
                parts.append(str(value))

        for bullet in getattr(
            experience,
            "bullets",
            [],
        ) or []:
            if bullet:
                parts.append(str(bullet))

    for project in getattr(
        resume_profile,
        "projects",
        [],
    ) or []:

        if getattr(project, "name", None):
            parts.append(str(project.name))

        for technology in getattr(
            project,
            "technologies",
            [],
        ) or []:
            if technology:
                parts.append(str(technology))

        if getattr(project, "description", None):
            parts.append(
                str(project.description)
            )

        for bullet in getattr(
            project,
            "bullets",
            [],
        ) or []:
            if bullet:
                parts.append(str(bullet))

    for skill in getattr(
        resume_profile,
        "skills",
        [],
    ) or []:
        if skill:
            parts.append(str(skill))

    for certification in getattr(
        resume_profile,
        "certifications",
        [],
    ) or []:

        for field in (
            "name",
            "issuer",
            "date",
            "url",
        ):
            value = getattr(
                certification,
                field,
                None,
            )

            if value:
                parts.append(str(value))

    for achievement in getattr(
        resume_profile,
        "achievements",
        [],
    ) or []:

        for field in (
            "title",
            "description",
            "date",
        ):
            value = getattr(
                achievement,
                field,
                None,
            )

            if value:
                parts.append(str(value))

    return " ".join(parts)


def _resume_section_text(
    resume_profile: Any,
    section: str,
) -> str:

    if resume_profile is None:
        return ""

    parts: List[str] = []

    if section == "experience":

        for item in getattr(
            resume_profile,
            "experience",
            [],
        ) or []:

            for field in (
                "company",
                "role",
                "location",
                "start_date",
                "end_date",
            ):
                value = getattr(
                    item,
                    field,
                    None,
                )

                if value:
                    parts.append(str(value))

            for bullet in getattr(
                item,
                "bullets",
                [],
            ) or []:
                if bullet:
                    parts.append(str(bullet))

    elif section == "projects":

        for item in getattr(
            resume_profile,
            "projects",
            [],
        ) or []:

            if getattr(item, "name", None):
                parts.append(str(item.name))

            for technology in getattr(
                item,
                "technologies",
                [],
            ) or []:
                if technology:
                    parts.append(str(technology))

            if getattr(item, "description", None):
                parts.append(
                    str(item.description)
                )

            for bullet in getattr(
                item,
                "bullets",
                [],
            ) or []:
                if bullet:
                    parts.append(str(bullet))

    elif section == "skills":

        for skill in getattr(
            resume_profile,
            "skills",
            [],
        ) or []:
            if skill:
                parts.append(str(skill))

    elif section == "summary":

        summary = getattr(
            resume_profile,
            "summary",
            None,
        )

        if summary:
            parts.append(str(summary))

    return " ".join(parts)


# ============================================================
# JD EXTRACTION
# ============================================================

def _extract_jd_skills(
    job_description: str,
) -> List[str]:

    normalized_jd = _normalize(
        job_description
    )

    found = []

    for skill in sorted(
        TECH_SKILLS,
        key=len,
        reverse=True,
    ):
        if _term_present(
            skill,
            normalized_jd,
        ):
            found.append(skill)

    return _dedupe_terms(found)


def _extract_jd_concepts(
    job_description: str,
) -> List[str]:

    normalized_jd = _normalize(
        job_description
    )

    found = []

    for concept in sorted(
        TECH_CONCEPTS,
        key=len,
        reverse=True,
    ):
        if _term_present(
            concept,
            normalized_jd,
        ):
            found.append(concept)

    return _dedupe_terms(found)


def _extract_jd_terms(
    job_description: str,
) -> List[str]:

    skills = _extract_jd_skills(
        job_description
    )

    concepts = _extract_jd_concepts(
        job_description
    )

    return _dedupe_terms(
        skills + concepts
    )


# ============================================================
# KEYWORD MATCHING
# ============================================================

def _keyword_match(
    job_description: str,
    resume_text: str,
) -> Dict[str, Any]:

    jd_skills = _extract_jd_skills(
        job_description
    )

    jd_concepts = _extract_jd_concepts(
        job_description
    )

    normalized_resume = _normalize(
        resume_text
    )

    matched_skills = [
        skill
        for skill in jd_skills
        if _term_present(
            skill,
            normalized_resume,
        )
    ]

    missing_skills = [
        skill
        for skill in jd_skills
        if skill not in matched_skills
    ]

    matched_concepts = [
        concept
        for concept in jd_concepts
        if _term_present(
            concept,
            normalized_resume,
        )
    ]

    missing_concepts = [
        concept
        for concept in jd_concepts
        if concept not in matched_concepts
    ]

    # Concrete skills are more important than concepts.
    total_weight = (
        len(jd_skills) * 2
        + len(jd_concepts)
    )

    matched_weight = (
        len(matched_skills) * 2
        + len(matched_concepts)
    )

    if total_weight == 0:
        match_percentage = 100
    else:
        match_percentage = round(
            matched_weight
            / total_weight
            * 100
        )

    required_keywords = _dedupe_terms(
        jd_skills + jd_concepts
    )

    matched_keywords = _dedupe_terms(
        matched_skills + matched_concepts
    )

    missing_keywords = _dedupe_terms(
        missing_skills + missing_concepts
    )

    return {
        "required_keywords": required_keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "total_keywords": len(
            required_keywords
        ),
        "match_percentage": max(
            0,
            min(100, match_percentage),
        ),
    }


# ============================================================
# SKILL MATCHING
# ============================================================
def _skill_match(
    job_description: str,
    resume_profile: Any,
    resume_text: str,
) -> Dict[str, Any]:

    jd_skills = _extract_jd_skills(
        job_description
    )

    if not jd_skills:
        return {
            "score": 100,
            "matched": [],
            "missing": [],
            "strong": [],
            "weak": [],
        }

    matched = []
    missing = []
    strong = []
    weak = []

    total_weight = 0
    achieved_weight = 0

    for skill in jd_skills:

        evidence = _technical_evidence_score(
            skill,
            resume_profile,
        )

        # Strong:
        # skill + project/experience evidence
        if evidence == 2:

            matched.append(skill)
            strong.append(skill)

            total_weight += 2
            achieved_weight += 2

        # Weak/moderate:
        # skill listed, but no supporting evidence
        elif evidence == 1:

            matched.append(skill)
            weak.append(skill)

            total_weight += 2
            achieved_weight += 1

        # Missing:
        # not listed and not demonstrated
        else:

            missing.append(skill)

            total_weight += 2

            # Controlled related evidence can provide
            # partial credit.
            if _related_technical_evidence(
                skill,
                resume_text,
            ):
                achieved_weight += 1

    if total_weight == 0:
        score = 100
    else:
        score = round(
            achieved_weight
            / total_weight
            * 100
        )

    return {
        "score": max(
            0,
            min(100, score),
        ),
        "matched": _dedupe_terms(
            matched
        ),
        "missing": _dedupe_terms(
            missing
        ),
        "strong": _dedupe_terms(
            strong
        ),
        "weak": _dedupe_terms(
            weak
        ),
    }
# ============================================================
# EVIDENCE ANALYSIS
# ============================================================

def _has_experience(
    resume_profile: Any,
) -> bool:
    """
    Determine whether the resume contains meaningful
    professional experience.
    """

    experience = getattr(
        resume_profile,
        "experience",
        [],
    ) or []

    for item in experience:
        role = getattr(item, "role", None)
        company = getattr(item, "company", None)
        bullets = getattr(item, "bullets", []) or []

        if role or company or bullets:
            return True

    return False


def _has_project_evidence(
    resume_profile: Any,
) -> bool:
    """
    Determine whether the resume contains meaningful
    project evidence.
    """

    projects = getattr(
        resume_profile,
        "projects",
        [],
    ) or []

    for item in projects:

        name = getattr(
            item,
            "name",
            None,
        )

        technologies = getattr(
            item,
            "technologies",
            [],
        ) or []

        description = getattr(
            item,
            "description",
            None,
        )

        bullets = getattr(
            item,
            "bullets",
            [],
        ) or []

        if (
            name
            or technologies
            or description
            or bullets
        ):
            return True

    return False


def _technical_evidence_score(
    term: str,
    resume_profile: Any,
) -> int:
    """
    Estimate how strongly a technical requirement is
    demonstrated by the resume.

    0 = no evidence
    1 = listed / weak evidence
    2 = supported by project or experience
    """

    resume_skills = [
        _canonical(str(skill))
        for skill in (
            getattr(
                resume_profile,
                "skills",
                [],
            )
            or []
        )
        if skill
    ]

    skill_text = " ".join(
        resume_skills
    )

    experience_text = _resume_section_text(
        resume_profile,
        "experience",
    )

    project_text = _resume_section_text(
        resume_profile,
        "projects",
    )

    # Strong evidence:
    # term appears in actual project or experience material.
    if (
        _term_present(term, project_text)
        or _term_present(term, experience_text)
    ):
        return 2

    # Moderate evidence:
    # term is explicitly listed as a skill.
    if _term_present(term, skill_text):
        return 1

    return 0


def _related_technical_evidence(
    term: str,
    text: str,
) -> bool:
    """
    Detect closely related technical evidence.

    This is deliberately controlled rather than using
    unrestricted semantic inference.
    """

    normalized_term = _canonical(term)

    evidence_groups = {
        "machine learning": {
            "machine learning",
            "scikit-learn",
            "tensorflow",
            "pytorch",
            "keras",
            "xgboost",
            "model training",
            "model evaluation",
            "model deployment",
        },

        "deep learning": {
            "deep learning",
            "tensorflow",
            "pytorch",
            "keras",
            "neural networks",
            "convolutional neural networks",
            "recurrent neural networks",
            "transformers",
        },

        "generative ai": {
            "generative ai",
            "llm",
            "gpt",
            "vae",
            "gan",
            "hugging face",
            "transformers",
            "prompt engineering",
            "rag",
        },

        "llm": {
            "llm",
            "gpt",
            "generative ai",
            "hugging face",
            "transformers",
            "rag",
        },

        "nlp": {
            "nlp",
            "spacy",
            "nltk",
            "sentence transformers",
            "transformers",
            "hugging face",
        },

        "computer vision": {
            "computer vision",
            "opencv",
            "dlib",
        },

        "data analysis": {
            "data analysis",
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn",
            "plotly",
        },

        "cloud computing": {
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "cloud computing",
        },

        "rest api": {
            "rest api",
            "fastapi",
            "express.js",
            "node.js",
            "graphql",
            "api development",
        },

        "data structures and algorithms": {
            "data structures",
            "data structures and algorithms",
            "algorithms",
        },

        "statistical modeling": {
            "statistical modeling",
            "machine learning",
            "data analysis",
            "numpy",
            "pandas",
            "scikit-learn",
        },

        "prompt engineering": {
            "prompt engineering",
            "prompt strategies",
            "generative ai",
            "llm",
            "gpt",
        },
    }

    related_terms = evidence_groups.get(
        normalized_term,
        set(),
    )

    if not related_terms:
        return False

    normalized_text = _normalize(text)

    for related in related_terms:

        if related == normalized_term:
            continue

        if _term_present(
            related,
            normalized_text,
        ):
            return True

    return False

# ============================================================
# EXPERIENCE MATCHING
# ============================================================

def _experience_match(
    job_description: str,
    resume_profile: Any,
) -> Dict[str, Any]:

    jd_terms = _extract_jd_terms(
        job_description
    )

    experience_text = _resume_section_text(
        resume_profile,
        "experience",
    )

    # IMPORTANT:
    # No professional experience does not mean
    # the candidate gets a hidden penalty.
    if not experience_text.strip():

        return {
            "score": None,
            "matched": [],
        }

    normalized_experience = _normalize(
        experience_text
    )

    matched = [
        term
        for term in jd_terms
        if _term_present(
            term,
            normalized_experience,
        )
    ]

    if not jd_terms:

        score = 100

    else:

        jd_skills = set(
            _extract_jd_skills(
                job_description
            )
        )

        total_weight = 0
        matched_weight = 0

        for term in jd_terms:

            weight = (
                2
                if term in jd_skills
                else 1
            )

            total_weight += weight

            if term in matched:
                matched_weight += weight

        score = (
            round(
                matched_weight
                / total_weight
                * 100
            )
            if total_weight
            else 100
        )

    return {
        "score": max(
            0,
            min(100, score),
        ),
        "matched": _dedupe_terms(
            matched
        ),
    }


# ============================================================
# PROJECT MATCHING
# ============================================================

def _project_match(
    job_description: str,
    resume_profile: Any,
) -> Dict[str, Any]:

    jd_terms = _extract_jd_terms(
        job_description
    )

    project_text = _resume_section_text(
        resume_profile,
        "projects",
    )

    if not project_text.strip():

        return {
            "score": 0,
            "matched": [],
        }

    normalized_projects = _normalize(
        project_text
    )

    matched = []
    related = []

    for term in jd_terms:

        # Direct project evidence
        if _term_present(
            term,
            normalized_projects,
        ):
            matched.append(term)

        # Controlled related evidence
        elif _related_technical_evidence(
            term,
            project_text,
        ):
            related.append(term)

    jd_skills = set(
        _extract_jd_skills(
            job_description
        )
    )

    total_weight = 0
    achieved_weight = 0

    for term in jd_terms:

        weight = (
            2
            if term in jd_skills
            else 1
        )

        total_weight += weight

        if term in matched:
            achieved_weight += weight

        elif term in related:
            # Related technical evidence receives
            # partial credit rather than full credit.
            achieved_weight += (
                weight * 0.5
            )

    if total_weight == 0:
        score = 100
    else:
        score = round(
            achieved_weight
            / total_weight
            * 100
        )

    return {
        "score": max(
            0,
            min(100, score),
        ),
        "matched": _dedupe_terms(
            matched
        ),
        "related": _dedupe_terms(
            related
        ),
    }

# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

_MODEL = None


def _get_embedding_model():

    global _MODEL

    if _MODEL is None:
        _MODEL = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    return _MODEL


def _semantic_similarity(
    resume_text: str,
    job_description: str,
    embedder: Any = None,
) -> int:

    if (
        not resume_text.strip()
        or not job_description.strip()
    ):
        return 0

    try:
        # Prefer the embedder supplied by the existing
        # analysis pipeline. This avoids loading another
        # SentenceTransformer model unnecessarily.
        model = embedder if embedder is not None else _get_embedding_model()

        resume_embedding = model.encode(
            resume_text[:8000],
            normalize_embeddings=True,
        )

        jd_embedding = model.encode(
            job_description[:8000],
            normalize_embeddings=True,
        )

        similarity = float(
            np.dot(
                resume_embedding,
                jd_embedding,
            )
        )

        similarity = max(
            0.0,
            min(1.0, similarity),
        )

        return round(
            similarity * 100
        )

    except Exception:
        return 0


# ============================================================
# EXPLANATION
# ============================================================

def _build_explanation(
    keyword_match: int,
    semantic_match: int,
    skills_match: int,
    experience_match: int,
    project_match: int,
    quality_score: int,
    missing_skills: List[str],
) -> List[str]:

    explanations: List[str] = []

    if keyword_match >= 80:

        explanations.append(
            "Resume covers most of the technical "
            "requirements identified in the job description."
        )

    elif keyword_match >= 50:

        explanations.append(
            "Resume covers several technical requirements, "
            "but some important JD requirements are missing."
        )

    else:

        explanations.append(
            "Resume covers a limited portion of the technical "
            "requirements identified in the job description."
        )

    if semantic_match >= 75:

        explanations.append(
            "Resume content is strongly aligned with the "
            "overall meaning of the job description."
        )

    elif semantic_match >= 50:

        explanations.append(
            "Resume has moderate semantic alignment with "
            "the job description."
        )

    else:

        explanations.append(
            "Resume has limited semantic alignment with "
            "the job description."
        )

    if skills_match >= 80:

        explanations.append(
            "Most required technical skills are represented "
            "in the resume."
        )

    elif skills_match >= 50:

        explanations.append(
            "Several required technical skills are represented, "
            "but additional skills could strengthen the match."
        )

    else:

        explanations.append(
            "A significant portion of the required technical "
            "skills is not represented in the resume."
        )

    if experience_match is None:

        explanations.append(
        "No professional experience was found. "
        "Project evidence is therefore weighted more heavily "
        "for this candidate."
    )

    elif experience_match >= 70:

        explanations.append(
        "Professional experience contains several "
        "job-relevant technical requirements."
    )

    elif experience_match > 0:

        explanations.append(
        "Some job-relevant technical evidence appears "
        "in the professional experience section."
    )

    else:

        explanations.append(
        "Professional experience does not contain clear "
        "evidence for the identified JD technical requirements."
    )

    if project_match >= 70:

        explanations.append(
            "Projects demonstrate strong evidence of relevant "
            "technical requirements."
        )

    elif project_match > 0:

        explanations.append(
            "Projects demonstrate some of the technical "
            "requirements from the job description."
        )

    else:

        explanations.append(
            "Projects do not contain clear evidence for the "
            "identified JD technical requirements."
        )

    if quality_score >= 80:

        explanations.append(
            "Resume quality is strong based on the resume "
            "intelligence analysis."
        )

    elif quality_score >= 60:

        explanations.append(
            "Resume quality is reasonable but has several "
            "areas that can be improved."
        )

    else:

        explanations.append(
            "Resume quality needs improvement before applying."
        )

    if missing_skills:

        preview = ", ".join(
            missing_skills[:8]
        )

        if len(missing_skills) > 8:
            preview += ", ..."

        explanations.append(
            "Important missing technical skills include: "
            f"{preview}."
        )

    return explanations


# ============================================================
# MAIN ATS CALCULATION
# ============================================================
def calculate_advanced_ats_score(
    resume_profile: Any,
    job_description: str = "",
    resume_quality: Any = None,
    resume_quality_score: int = None,
    embedder: Any = None,
) -> AdvancedATSResult:

    # ========================================================
    # RESUME TEXT
    # ========================================================

    resume_text = _resume_text(
        resume_profile
    )

    # ========================================================
    # RESUME QUALITY SCORE
    # ========================================================

    if resume_quality_score is not None:

        quality_score = int(
            resume_quality_score
        )

    elif resume_quality is not None:

        quality_score = int(
            getattr(
                resume_quality,
                "overall_score",
                0,
            )
        )

    else:

        quality_score = 0

    quality_score = max(
        0,
        min(100, quality_score),
    )

    # ========================================================
    # NO JD
    # ========================================================

    if not job_description.strip():

        return AdvancedATSResult(

            ats_score=quality_score,

            jd_match=0,

            score_breakdown=ATSScoreBreakdown(
                keyword_match=0,
                semantic_match=0,
                skills_match=0,
                experience_match=0,
                project_match=0,
                resume_quality=quality_score,
            ),

            keyword_analysis=ATSKeywordAnalysis(
                required_keywords=[],
                matched_keywords=[],
                missing_keywords=[],
                total_keywords=0,
                match_percentage=0,
            ),

            matched_skills=[],

            missing_skills=[],

            matched_experience_terms=[],

            matched_project_terms=[],

            explanation=[
                "No job description was provided.",
                "ATS score is based on resume quality only.",
            ],
        )

    # ========================================================
    # JD ANALYSIS
    # ========================================================

    keyword_data = _keyword_match(
        job_description,
        resume_text,
    )

    skill_data = _skill_match(
        job_description,
        resume_profile,
        resume_text,
    )

    experience_data = _experience_match(
        job_description,
        resume_profile,
    )

    project_data = _project_match(
        job_description,
        resume_profile,
    )

    semantic_match = _semantic_similarity(
        resume_text,
        job_description,
        embedder=embedder,
    )

    keyword_match = keyword_data[
        "match_percentage"
    ]

    skills_match = skill_data[
        "score"
    ]

    experience_match = experience_data[
        "score"
    ]

    project_match = project_data[
        "score"
    ]

    # ========================================================
    # CANDIDATE TYPE
    # ========================================================

    has_experience = _has_experience(
        resume_profile
    )

    has_projects = _has_project_evidence(
        resume_profile
    )

    # ========================================================
    # EVIDENCE-AWARE ATS SCORING
    # ========================================================

    if has_experience:

        # Experienced candidate:
        #
        # Experience is a meaningful part of the score.
        ats_score = round(
            keyword_match * 0.25
            + semantic_match * 0.20
            + skills_match * 0.20
            + (experience_match or 0) * 0.15
            + project_match * 0.10
            + quality_score * 0.10
        )

    else:

        # Fresher / student:
        #
        # No professional experience is NOT treated
        # as a missing requirement.
        #
        # Project evidence receives the weight instead.
        ats_score = round(
            keyword_match * 0.25
            + semantic_match * 0.20
            + skills_match * 0.20
            + project_match * 0.20
            + quality_score * 0.15
        )

    ats_score = max(
        0,
        min(100, ats_score),
    )

    # ========================================================
    # JOB MATCH
    # ========================================================

    if has_experience:

        jd_match = round(
            keyword_match * 0.35
            + semantic_match * 0.30
            + skills_match * 0.25
            + (experience_match or 0) * 0.10
        )

    else:

        # Fresher:
        #
        # Project evidence contributes to job matching
        # instead of absent professional experience.
        jd_match = round(
            keyword_match * 0.35
            + semantic_match * 0.30
            + skills_match * 0.20
            + project_match * 0.15
        )

    jd_match = max(
        0,
        min(100, jd_match),
    )

    # ========================================================
    # EXPLANATION
    # ========================================================

    explanations = _build_explanation(
        keyword_match=keyword_match,
        semantic_match=semantic_match,
        skills_match=skills_match,
        experience_match=experience_match,
        project_match=project_match,
        quality_score=quality_score,
        missing_skills=skill_data[
            "missing"
        ],
    )

    # ========================================================
    # FRESHER CONTEXT
    # ========================================================

    if not has_experience:

        explanations.insert(
            0,
            "Professional experience was not found. "
            "Project evidence is therefore weighted more "
            "heavily for this candidate.",
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return AdvancedATSResult(

        ats_score=ats_score,

        jd_match=jd_match,

        score_breakdown=ATSScoreBreakdown(

            keyword_match=keyword_match,

            semantic_match=semantic_match,

            skills_match=skills_match,

            experience_match=(
                experience_match
                if experience_match is not None
                else 0
            ),

            project_match=project_match,

            resume_quality=quality_score,
        ),

        keyword_analysis=ATSKeywordAnalysis(

            required_keywords=keyword_data[
                "required_keywords"
            ],

            matched_keywords=keyword_data[
                "matched_keywords"
            ],

            missing_keywords=keyword_data[
                "missing_keywords"
            ],

            total_keywords=keyword_data[
                "total_keywords"
            ],

            match_percentage=keyword_match,
        ),

        matched_skills=skill_data[
            "matched"
        ],

        missing_skills=skill_data[
            "missing"
        ],

        matched_experience_terms=experience_data[
            "matched"
        ],

        matched_project_terms=project_data[
            "matched"
        ],

        explanation=explanations,
    )
