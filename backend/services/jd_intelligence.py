import re
from typing import Any, Dict, List, Optional

from backend.models.schemas import (
    JDIntelligenceResult,
    JDExperienceRequirement,
    JDEducationRequirement,
)
ROLE_SIGNALS = {
    "ai": {
        "ai",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "generative ai",
        "llm",
        "nlp",
        "computer vision",
        "gpt",
    },
    "machine learning": {
        "machine learning",
        "deep learning",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "keras",
        "xgboost",
        "model training",
        "model evaluation",
        "model deployment",
    },
    "nlp": {
        "nlp",
        "natural language processing",
        "spacy",
        "nltk",
        "hugging face",
        "transformers",
        "sentence transformers",
        "llm",
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
    "cloud": {
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "cloud computing",
        "cloud architecture",
    },
    "backend": {
        "node.js",
        "express.js",
        "fastapi",
        "django",
        "flask",
        "spring boot",
        "rest api",
        "graphql",
        "backend development",
    },
    "frontend": {
        "react",
        "angular",
        "vue",
        "next.js",
        "html",
        "css",
        "bootstrap",
        "tailwind",
        "frontend development",
    },
    "full stack": {
        "full stack development",
        "react",
        "node.js",
        "express.js",
        "mongodb",
        "postgresql",
        "rest api",
    },
    "devops": {
        "docker",
        "kubernetes",
        "terraform",
        "jenkins",
        "github actions",
        "ci/cd",
    },
    "data": {
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "plotly",
        "data analysis",
        "data preprocessing",
        "feature engineering",
        "data visualization",
        "statistical modeling",
    },
}


# ============================================================
# DEGREE / EDUCATION TERMS
# ============================================================

DEGREE_TERMS = {
    "bachelor's degree",
    "bachelors degree",
    "bachelor degree",
    "b.tech",
    "btech",
    "b.e",
    "be degree",
    "b.sc",
    "bsc",
    "master's degree",
    "masters degree",
    "master degree",
    "m.tech",
    "mtech",
    "m.e",
    "me degree",
    "m.sc",
    "msc",
    "ph.d",
    "phd",
}


FIELD_TERMS = {
    "computer science",
    "computer science and engineering",
    "information technology",
    "information systems",
    "software engineering",
    "data science",
    "artificial intelligence",
    "machine learning",
    "electronics",
    "electrical engineering",
}


# ============================================================
# PREFERRED / REQUIRED LANGUAGE
# ============================================================

PREFERRED_MARKERS = [
    "preferred",
    "preferably",
    "nice to have",
    "nice-to-have",
    "good to have",
    "plus",
    "bonus",
    "desired",
    "would be a plus",
    "advantage",
]


REQUIRED_MARKERS = [
    "required",
    "must have",
    "must-have",
    "mandatory",
    "essential",
    "you have",
    "we require",
    "requirements",
]


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize(text: str) -> str:
    if not text:
        return ""

    value = str(text).lower()

    value = value.replace("\u2013", "-")
    value = value.replace("\u2014", "-")
    value = value.replace("\u2019", "'")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _canonical(value: str) -> str:
    value = _normalize(value)

    aliases = {
        "python programming": "python",
        "python development": "python",
        "machine-learning": "machine learning",
        "ml": "machine learning",
        "deep-learning": "deep learning",
        "deep learning techniques": "deep learning",
        "natural language processing": "nlp",
        "gen ai": "generative ai",
        "genai": "generative ai",
        "large language model": "llm",
        "large language models": "llm",
        "llms": "llm",
        "huggingface": "hugging face",
        "scikit learn": "scikit-learn",
        "restful api": "rest api",
        "restful apis": "rest api",
        "rest apis": "rest api",
        "fast api": "fastapi",
        "fast apis": "fastapi",
        "nodejs": "node.js",
        "node js": "node.js",
        "reactjs": "react",
        "react.js": "react",
        "react js": "react",
        "expressjs": "express.js",
        "express js": "express.js",
    }

    return aliases.get(value, value)


def _contains(term: str, text: str) -> bool:
    normalized_term = _normalize(term)
    normalized_text = _normalize(text)

    if not normalized_term or not normalized_text:
        return False

    pattern = (
        rf"(?<![a-z0-9])"
        rf"{re.escape(normalized_term)}"
        rf"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        normalized_text,
        flags=re.IGNORECASE,
    ) is not None


def _dedupe(values: List[str]) -> List[str]:
    result = []
    seen = set()

    for value in values:
        canonical = _canonical(value)

        if not canonical:
            continue

        if canonical in seen:
            continue

        seen.add(canonical)
        result.append(canonical)

    return result


# ============================================================
# SECTION DETECTION
# ============================================================

def _split_into_sections(
    job_description: str,
) -> Dict[str, str]:

    lines = [
        line.strip()
        for line in job_description.splitlines()
        if line.strip()
    ]

    sections: Dict[str, List[str]] = {
        "general": [],
        "requirements": [],
        "preferred": [],
        "responsibilities": [],
        "education": [],
        "experience": [],
    }

    current = "general"

    for line in lines:

        normalized = _normalize(line)

        if re.search(
            r"\b(responsibilities|what you.ll do|role responsibilities)\b",
            normalized,
        ):
            current = "responsibilities"
            continue

        if re.search(
            r"\b(required qualifications|requirements|must have|required skills)\b",
            normalized,
        ):
            current = "requirements"
            continue

        if re.search(
            r"\b(preferred qualifications|preferred skills|nice to have|bonus)\b",
            normalized,
        ):
            current = "preferred"
            continue

        if re.search(
            r"\b(education|educational qualification|academic qualification)\b",
            normalized,
        ):
            current = "education"
            continue

        if re.search(
            r"\b(experience|work experience|professional experience)\b",
            normalized,
        ):
            current = "experience"
            continue

        sections[current].append(line)

    return {
        key: "\n".join(value)
        for key, value in sections.items()
    }


# ============================================================
# ROLE TITLE
# ============================================================

def _extract_role_title(
    job_description: str,
) -> Optional[str]:

    patterns = [
        r"(?:job title|role|position|title)\s*[:\-]\s*([^\n]+)",
        r"(?:we are hiring|hiring for)\s+(?:a|an)?\s*([A-Za-z0-9 /&-]+)",
    ]

    normalized = job_description.strip()

    for pattern in patterns:
        match = re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        )

        if match:
            title = match.group(1).strip()

            if 2 <= len(title) <= 100:
                return title

    # Try common title patterns when the JD starts with a title.
    first_lines = [
        line.strip()
        for line in normalized.splitlines()
        if line.strip()
    ]

    if first_lines:
        first = first_lines[0]

        if (
            len(first) <= 80
            and any(
                keyword in first.lower()
                for keyword in [
                    "engineer",
                    "developer",
                    "scientist",
                    "analyst",
                    "architect",
                    "manager",
                    "designer",
                    "intern",
                ]
            )
        ):
            return first

    return None


# ============================================================
# SKILLS
# ============================================================

def _extract_known_skills(
    text: str,
) -> List[str]:

    if not text:
        return []

    # Keep this vocabulary intentionally controlled.
    skills = {
        "python",
        "java",
        "javascript",
        "typescript",
        "c",
        "c++",
        "c#",
        "go",
        "rust",

        "react",
        "angular",
        "vue",
        "next.js",
        "html",
        "css",
        "bootstrap",
        "tailwind",

        "node.js",
        "express.js",
        "fastapi",
        "django",
        "flask",
        "spring",
        "spring boot",
        "rest api",
        "graphql",

        "mongodb",
        "mysql",
        "postgresql",
        "sqlite",
        "redis",
        "oracle",
        "sql",

        "aws",
        "azure",
        "gcp",
        "google cloud",

        "docker",
        "kubernetes",
        "terraform",
        "jenkins",
        "github actions",
        "ci/cd",

        "git",
        "github",
        "gitlab",
        "bitbucket",

        "ai",
        "machine learning",
        "deep learning",
        "generative ai",
        "llm",
        "nlp",
        "computer vision",

        "tensorflow",
        "pytorch",
        "keras",
        "scikit-learn",
        "xgboost",

        "spacy",
        "nltk",
        "hugging face",
        "sentence transformers",
        "transformers",
        "openai",
        "groq",

        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "plotly",
        "jupyter notebook",

        "opencv",
        "dlib",

        "gpt",
        "vae",
        "gan",

        "postman",
        "supabase",
        "firebase",
    }

    found = []

    for skill in sorted(
        skills,
        key=len,
        reverse=True,
    ):
        if _contains(skill, text):
            found.append(skill)

    return _dedupe(found)


# ============================================================
# CONCEPTS
# ============================================================

def _extract_concepts(
    text: str,
) -> List[str]:

    concepts = {
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

    found = []

    for concept in sorted(
        concepts,
        key=len,
        reverse=True,
    ):
        if _contains(concept, text):
            found.append(concept)

    return _dedupe(found)


# ============================================================
# EXPERIENCE
# ============================================================

def _extract_experience(
    job_description: str,
) -> JDExperienceRequirement:

    text = _normalize(job_description)

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"minimum\s+of\s+(\d+(?:\.\d+)?)\s+years?",
        r"at\s+least\s+(\d+(?:\.\d+)?)\s+years?",
        r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s+years?",
    ]

    minimum_years = None
    maximum_years = None

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        if len(match.groups()) == 1:
            minimum_years = float(match.group(1))

        elif len(match.groups()) == 2:
            minimum_years = float(match.group(1))
            maximum_years = float(match.group(2))

        break

    experience_required = (
        minimum_years is not None
        or "professional experience" in text
        or "work experience" in text
        or "years of experience" in text
    )

    raw_text = None

    if experience_required:
        match = re.search(
            r"[^.\n]*(?:\d+\s*\+?\s*years?|professional experience|work experience)[^.\n]*",
            job_description,
            flags=re.IGNORECASE,
        )

        if match:
            raw_text = match.group(0).strip()

    return JDExperienceRequirement(
        required=experience_required,
        minimum_years=minimum_years,
        maximum_years=maximum_years,
        raw_text=raw_text,
    )


# ============================================================
# EDUCATION
# ============================================================

def _extract_education(
    job_description: str,
) -> JDEducationRequirement:

    normalized = _normalize(job_description)

    degrees = []

    for degree in sorted(
        DEGREE_TERMS,
        key=len,
        reverse=True,
    ):
        if _contains(degree, normalized):
            degrees.append(degree)

    degrees = _dedupe(degrees)

    fields = []

    for field in sorted(
        FIELD_TERMS,
        key=len,
        reverse=True,
    ):
        if _contains(field, normalized):
            fields.append(field)

    fields = _dedupe(fields)

    education_required = bool(
        degrees or fields
    )

    raw_text = None

    if education_required:

        match = re.search(
            r"[^.\n]*(?:degree|bachelor|master|b\.tech|m\.tech|computer science|information technology)[^.\n]*",
            job_description,
            flags=re.IGNORECASE,
        )

        if match:
            raw_text = match.group(0).strip()

    return JDEducationRequirement(
        required=education_required,
        degrees=degrees,
        fields=fields,
        raw_text=raw_text,
    )


# ============================================================
# REQUIRED VS PREFERRED
# ============================================================

def _extract_required_preferred_skills(
    job_description: str,
) -> Dict[str, List[str]]:

    sections = _split_into_sections(
        job_description
    )

    required_text = "\n".join(
        [
            sections["requirements"],
            sections["experience"],
            sections["general"],
        ]
    )

    preferred_text = sections["preferred"]

    required_skills = _extract_known_skills(
        required_text
    )

    preferred_skills = _extract_known_skills(
        preferred_text
    )

    # Explicit "preferred" mentions inside general text.
    lines = job_description.splitlines()

    for line in lines:

        normalized_line = _normalize(line)

        is_preferred = any(
            marker in normalized_line
            for marker in PREFERRED_MARKERS
        )

        if not is_preferred:
            continue

        line_skills = _extract_known_skills(
            line
        )

        preferred_skills.extend(
            line_skills
        )

        required_skills = [
            skill
            for skill in required_skills
            if skill not in line_skills
        ]

    preferred_skills = _dedupe(
        preferred_skills
    )

    required_skills = [
        skill
        for skill in _dedupe(required_skills)
        if skill not in preferred_skills
    ]

    return {
        "required": required_skills,
        "preferred": preferred_skills,
    }


# ============================================================
# RESPONSIBILITIES
# ============================================================

def _extract_responsibilities(
    job_description: str,
) -> List[str]:

    sections = _split_into_sections(
        job_description
    )

    text = sections["responsibilities"]

    if not text.strip():
        return []

    responsibilities = []

    for line in text.splitlines():

        value = line.strip()

        value = re.sub(
            r"^[\-\*\u2022\d\.\)\s]+",
            "",
            value,
        ).strip()

        if len(value) < 12:
            continue

        responsibilities.append(value)

    return responsibilities[:20]


# ============================================================
# ROLE SIGNALS
# ============================================================

def _extract_role_signals(
    job_description: str,
) -> List[str]:

    normalized = _normalize(
        job_description
    )

    signals = []

    for signal, terms in ROLE_SIGNALS.items():

        for term in terms:

            if _contains(
                term,
                normalized,
            ):
                signals.append(signal)
                break

    return _dedupe(signals)


# ============================================================
# MAIN JD INTELLIGENCE
# ============================================================

def analyze_job_description(
    job_description: str,
) -> JDIntelligenceResult:

    if not job_description or not job_description.strip():
        return JDIntelligenceResult()

    role_title = _extract_role_title(
        job_description
    )

    sections = _split_into_sections(
        job_description
    )

    skill_data = _extract_required_preferred_skills(
        job_description
    )

    required_skills = skill_data[
        "required"
    ]

    preferred_skills = skill_data[
        "preferred"
    ]

    technical_concepts = _extract_concepts(
        job_description
    )

    experience = _extract_experience(
        job_description
    )

    education = _extract_education(
        job_description
    )

    responsibilities = _extract_responsibilities(
        job_description
    )

    role_signals = _extract_role_signals(
        job_description
    )

    required_keywords = _dedupe(
        required_skills
        + technical_concepts
    )

    preferred_keywords = _dedupe(
        preferred_skills
    )

    return JDIntelligenceResult(
        role_title=role_title,

        required_skills=required_skills,

        preferred_skills=preferred_skills,

        technical_concepts=technical_concepts,

        experience=experience,

        education=education,

        responsibilities=responsibilities,

        role_signals=role_signals,

        required_keywords=required_keywords,

        preferred_keywords=preferred_keywords,

        total_required_items=len(
            required_keywords
        ),

        total_preferred_items=len(
            preferred_keywords
        ),
    )