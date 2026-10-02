from __future__ import annotations

import re
from typing import Iterable, Optional

from backend.services.jobs.job_classification import JobClassification
from backend.services.jobs.role_taxonomy import (
    RoleClassification,
    classify_role,
    normalize_text,
    SOFTWARE_ENGINEERING,
    BACKEND,
    FRONTEND,
    FULL_STACK,
    AI_ML,
    DATA,
    DEVOPS_CLOUD,
    QA_AUTOMATION,
    CYBERSECURITY,
    MOBILE,
    DATABASE,
    IT_SUPPORT,
    EMBEDDED,
    PRODUCT_MANAGEMENT,
    BUSINESS_ANALYSIS,
    MARKETING_FAMILY,
    SALES_FAMILY,
    DESIGN_FAMILY,
    HR_FAMILY,
    FINANCE_FAMILY,
    OPERATIONS_FAMILY,
    CONTENT_FAMILY,
    CUSTOMER_SUCCESS_FAMILY,
    LEGAL_FAMILY,
    UNKNOWN_FAMILY,
    MARKETING,
    SALES,
    DESIGN,
    HUMAN_RESOURCES,
    FINANCE,
    OPERATIONS,
    CONTENT,
    CUSTOMER_SUCCESS,
    LEGAL,
    UNKNOWN,
)


# ============================================================
# VERSION
# ============================================================

CLASSIFICATION_VERSION = 3


# ============================================================
# CATEGORIES
# ============================================================

# ============================================================
# PUBLIC CATEGORY CONSTANTS
# ============================================================

ENGINEERING_CATEGORY = "engineering"
DATA_CATEGORY = "data"
AI_CATEGORY = "artificial_intelligence"
INFRASTRUCTURE_CATEGORY = "infrastructure"
QA_CATEGORY = "quality_assurance"
SECURITY_CATEGORY = "security"
PRODUCT_CATEGORY = "product"
BUSINESS_CATEGORY = "business"
DESIGN_CATEGORY = "design"
MARKETING_CATEGORY = "marketing"
SALES_CATEGORY = "sales"
OPERATIONS_CATEGORY = "operations"
CONTENT_CATEGORY = "content"
HR_CATEGORY = "human_resources"
FINANCE_CATEGORY = "finance"
CUSTOMER_SUCCESS_CATEGORY = "customer_success"
LEGAL_CATEGORY = "legal"
OTHER_CATEGORY = "other"


# Internal aliases
CATEGORY_ENGINEERING = ENGINEERING_CATEGORY
CATEGORY_DATA = DATA_CATEGORY
CATEGORY_AI = AI_CATEGORY
CATEGORY_INFRASTRUCTURE = INFRASTRUCTURE_CATEGORY
CATEGORY_QA = QA_CATEGORY
CATEGORY_SECURITY = SECURITY_CATEGORY
CATEGORY_PRODUCT = PRODUCT_CATEGORY
CATEGORY_BUSINESS = BUSINESS_CATEGORY
CATEGORY_DESIGN = DESIGN_CATEGORY
CATEGORY_MARKETING = MARKETING_CATEGORY
CATEGORY_SALES = SALES_CATEGORY
CATEGORY_OPERATIONS = OPERATIONS_CATEGORY
CATEGORY_CONTENT = CONTENT_CATEGORY
CATEGORY_HR = HR_CATEGORY
CATEGORY_FINANCE = FINANCE_CATEGORY
CATEGORY_CUSTOMER_SUCCESS = CUSTOMER_SUCCESS_CATEGORY
CATEGORY_LEGAL = LEGAL_CATEGORY
CATEGORY_OTHER = OTHER_CATEGORY


# ============================================================
# EXPERIENCE
# ============================================================

EXPERIENCE_LEVELS = {
    "intern",
    "fresher",
    "entry",
    "junior",
    "mid",
    "senior",
    "lead",
    "manager",
    "director",
    "unknown",
}


EXPERIENCE_PATTERNS = (
    (r"\bintern(ship)?\b", "intern"),
    (r"\bfresher\b", "fresher"),
    (r"\bentry[\s-]?level\b", "entry"),
    (r"\bgraduate\b", "entry"),
    (r"\bjunior\b", "junior"),
    (r"\bmid[\s-]?level\b", "mid"),
    (r"\bsenior\b", "senior"),
    (r"\blead\b", "lead"),
    (r"\bmanager\b", "manager"),
    (r"\bdirector\b", "director"),
)


def _normalize(value: Optional[str]) -> str:
    return normalize_text(value or "")


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        normalized = _normalize(value)

        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(value)

    return result


# ============================================================
# EXPERIENCE CLASSIFICATION
# ============================================================
def classify_experience(
    title: str,
    description: str = "",
    source_experience_level: Optional[str] = None,
) -> str:

    title_text = _normalize(title)
    description_text = _normalize(description)
    source = _normalize(source_experience_level or "")

    # --------------------------------------------------------
    # 1. Explicit fresher / entry-level signals
    # --------------------------------------------------------

    entry_pattern = (
        r"\b(entry[\s-]?level|fresher|graduate|new grad|"
        r"early career|campus hire)\b"
    )

    if re.search(entry_pattern, title_text):
        return "entry"

    if re.search(entry_pattern, description_text):
        return "entry"

    # --------------------------------------------------------
    # 2. Explicit internship in TITLE
    #
    # Title is a strong signal:
    # "Software Engineer Intern" -> intern
    # --------------------------------------------------------

    if re.search(r"\bintern(ship)?\b", title_text):
        return "intern"

    # --------------------------------------------------------
    # 3. Strong seniority signals in TITLE
    #
    # These must beat a bad source value such as:
    # source_experience_level = "internship"
    # --------------------------------------------------------

    if re.search(r"\bsenior\b", title_text):
        return "senior"

    if re.search(r"\blead\b", title_text):
        return "lead"

    if re.search(r"\bmanager\b", title_text):
        return "manager"

    if re.search(r"\bdirector\b", title_text):
        return "director"

    if re.search(r"\bmid[\s-]?level\b", title_text):
        return "mid"

    if re.search(r"\bjunior\b", title_text):
        return "junior"

    # --------------------------------------------------------
    # 4. Numeric professional experience
    #
    # This must beat source "internship".
    #
    # Example:
    # "3+ years of non-internship professional software
    # development experience"
    # -> mid
    # --------------------------------------------------------

    years = re.findall(
        r"(\d+)\s*\+?\s*(?:years?|yrs?)",
        description_text,
    )

    if years:
        maximum = max(int(value) for value in years)

        if maximum <= 1:
            return "entry"

        if maximum <= 3:
            return "mid"

        if maximum <= 6:
            return "senior"

        if maximum <= 10:
            return "lead"

        return "lead"

    # --------------------------------------------------------
    # 5. Strong seniority signals in DESCRIPTION
    #
    # Example:
    # "seasoned senior developer"
    # -> senior
    # --------------------------------------------------------

    if re.search(r"\bsenior\b", description_text):
        return "senior"

    if re.search(r"\blead\b", description_text):
        return "lead"

    if re.search(r"\bmanager\b", description_text):
        return "manager"

    if re.search(r"\bdirector\b", description_text):
        return "director"

    if re.search(r"\bmid[\s-]?level\b", description_text):
        return "mid"

    if re.search(r"\bjunior\b", description_text):
        return "junior"

    # --------------------------------------------------------
    # 6. Explicit internship ROLE in description
    #
    # Do NOT classify a job as intern merely because the word
    # "internship" appears somewhere in the JD.
    #
    # Examples that count:
    # "internship program"
    # "internship opportunity"
    # "intern position"
    # "as an intern"
    # --------------------------------------------------------

    internship_role_pattern = (
        r"\binternship\s+(?:program|opportunity|position|role|opening)\b"
        r"|\bintern\s+(?:position|role|opportunity)\b"
        r"|\bas\s+an?\s+intern\b"
    )

    if re.search(
        internship_role_pattern,
        description_text,
    ):
        return "intern"

    # --------------------------------------------------------
    # 7. Source experience is now only a FALLBACK
    #
    # This prevents:
    # source = "internship"
    # from incorrectly overriding:
    # title/description = senior SDE
    # --------------------------------------------------------

    if source:
        if source in EXPERIENCE_LEVELS:
            return source

        if "intern" in source:
            return "intern"

        if "entry" in source or "graduate" in source:
            return "entry"

        if "junior" in source:
            return "junior"

        if "mid" in source:
            return "mid"

        if "senior" in source:
            return "senior"

        if "lead" in source:
            return "lead"

        if "manager" in source:
            return "manager"

        if "director" in source:
            return "director"

    return "unknown"


# ============================================================
# SKILLS
# ============================================================

SKILL_ALIASES = {
    "Python": ("python",),
    "Java": ("java",),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript", "ts"),

    "React": (
        "react",
        "react.js",
        "reactjs",
    ),

    "Node.js": (
        "node.js",
        "nodejs",
        "node",
    ),

    "Express": (
        "express",
        "express.js",
    ),

    "FastAPI": (
        "fastapi",
        "fast api",
    ),

    "Angular": (
        "angular",
        "angular.js",
    ),

    "Vue": (
        "vue",
        "vue.js",
        "vuejs",
    ),

    "Next.js": (
        "next.js",
        "nextjs",
    ),

    "SQL": ("sql",),

    "PostgreSQL": (
        "postgresql",
        "postgres",
    ),

    "MySQL": ("mysql",),

    "MongoDB": (
        "mongodb",
        "mongo db",
    ),

    "Redis": ("redis",),

    "AWS": (
        "aws",
        "amazon web services",
    ),

    "Azure": ("azure",),

    "GCP": (
        "gcp",
        "google cloud",
    ),

    "Docker": ("docker",),

    "Kubernetes": (
        "kubernetes",
        "k8s",
    ),

    "Git": ("git",),

    "GitHub": ("github",),

    "Linux": ("linux",),

    "TensorFlow": ("tensorflow",),

    "PyTorch": ("pytorch",),

    "Scikit-learn": (
        "scikit-learn",
        "sklearn",
    ),

    "Pandas": ("pandas",),

    "NumPy": ("numpy",),

    "Machine Learning": (
        "machine learning",
    ),

    "Deep Learning": (
        "deep learning",
    ),

    "NLP": (
        "nlp",
        "natural language processing",
    ),

    "LLM": (
        "llm",
        "large language model",
        "large language models",
    ),

    "Generative AI": (
        "generative ai",
        "genai",
    ),

    "LangChain": ("langchain",),

    "LangGraph": ("langgraph",),

    "Spark": (
        "spark",
        "apache spark",
    ),

    "Kafka": (
        "kafka",
        "apache kafka",
    ),

    "Airflow": (
        "airflow",
        "apache airflow",
    ),

    "Tableau": ("tableau",),

    "Power BI": (
        "power bi",
        "powerbi",
    ),

    "Selenium": ("selenium",),

    "Cypress": ("cypress",),

    "Playwright": ("playwright",),

    "Jenkins": ("jenkins",),

    "Terraform": ("terraform",),

    "Ansible": ("ansible",),
}

def _extract_skill_mentions(text: str) -> list[str]:
    normalized = _normalize(text)

    found: list[str] = []

    for display_name, aliases in SKILL_ALIASES.items():

        for alias in aliases:
            alias_normalized = _normalize(alias)

            if re.search(
                rf"(?<![a-z0-9])"
                rf"{re.escape(alias_normalized)}"
                rf"(?![a-z0-9])",
                normalized,
            ):
                found.append(display_name)
                break

    return _unique(found)


# ============================================================
# SECTION EXTRACTION
# ============================================================

def _extract_section(
    text: str,
    section_keywords: tuple[str, ...],
) -> str:

    if not text:
        return ""

    pattern = (
        r"(?:"
        + "|".join(
            re.escape(keyword)
            for keyword in section_keywords
        )
        + r")"
        r"(.*?)(?="
        r"\n\s*(?:"
        r"requirements?|"
        r"qualifications?|"
        r"responsibilities|"
        r"preferred|"
        r"nice to have|"
        r"bonus|"
        r"about|"
        r"benefits|"
        r"what you.?ll do|"
        r"what we.?re looking for"
        r")"
        r"|$)"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return match.group(1) if match else ""


# ============================================================
# REQUIRED SKILLS
# ============================================================

def extract_required_skills(
    title: str,
    description: str,
    existing_skills: Optional[list[str]] = None,
) -> list[str]:

    text = f"{title}\n{description}"

    required_section = _extract_section(
        text,
        (
            "requirements",
            "required skills",
            "qualifications",
            "what you need",
            "must have",
            "minimum qualifications",
        ),
    )

    source = (
        required_section
        if required_section
        else text
    )

    skills = _extract_skill_mentions(source)

    if existing_skills:
        skills.extend(
            _extract_skill_mentions(
                "\n".join(str(skill) for skill in existing_skills)
            )
        )

    return _unique(skills)


# ============================================================
# PREFERRED SKILLS
# ============================================================

def extract_preferred_skills(
    title: str = "",
    description: str = "",
) -> list[str]:

    text = f"{title}\n{description}"

    preferred_section = _extract_section(
        text,
        (
            "preferred",
            "preferred qualifications",
            "nice to have",
            "nice-to-have",
            "bonus",
            "plus",
            "good to have",
        ),
    )

    if not preferred_section:
        return []

    return _unique(
        _extract_skill_mentions(preferred_section)
    )

# ============================================================
# CATEGORY MAPPING
# ============================================================

def _category_from_family(
    family: str,
    domain: str,
) -> str:

    # --------------------------------------------------------
    # Technology
    # --------------------------------------------------------

    technology_mapping = {
        SOFTWARE_ENGINEERING: CATEGORY_ENGINEERING,
        BACKEND: CATEGORY_ENGINEERING,
        FRONTEND: CATEGORY_ENGINEERING,
        FULL_STACK: CATEGORY_ENGINEERING,

        AI_ML: CATEGORY_AI,
        DATA: CATEGORY_DATA,

        DEVOPS_CLOUD: CATEGORY_INFRASTRUCTURE,
        QA_AUTOMATION: CATEGORY_QA,
        CYBERSECURITY: CATEGORY_SECURITY,

        MOBILE: CATEGORY_ENGINEERING,
        DATABASE: CATEGORY_DATA,
        IT_SUPPORT: CATEGORY_INFRASTRUCTURE,
        EMBEDDED: CATEGORY_ENGINEERING,
    }

    if family in technology_mapping:
        return technology_mapping[family]

    # --------------------------------------------------------
    # Business / non-technical
    # --------------------------------------------------------

    family_mapping = {
        PRODUCT_MANAGEMENT: CATEGORY_PRODUCT,
        BUSINESS_ANALYSIS: CATEGORY_BUSINESS,

        MARKETING_FAMILY: CATEGORY_MARKETING,
        SALES_FAMILY: CATEGORY_SALES,
        DESIGN_FAMILY: CATEGORY_DESIGN,
        HR_FAMILY: CATEGORY_HR,
        FINANCE_FAMILY: CATEGORY_FINANCE,
        OPERATIONS_FAMILY: CATEGORY_OPERATIONS,
        CONTENT_FAMILY: CATEGORY_CONTENT,
        CUSTOMER_SUCCESS_FAMILY: CATEGORY_CUSTOMER_SUCCESS,
        LEGAL_FAMILY: CATEGORY_LEGAL,
    }

    if family in family_mapping:
        return family_mapping[family]

    # --------------------------------------------------------
    # Domain fallback
    # --------------------------------------------------------

    domain_mapping = {
        MARKETING: CATEGORY_MARKETING,
        SALES: CATEGORY_SALES,
        DESIGN: CATEGORY_DESIGN,
        HUMAN_RESOURCES: CATEGORY_HR,
        FINANCE: CATEGORY_FINANCE,
        OPERATIONS: CATEGORY_OPERATIONS,
        CONTENT: CATEGORY_CONTENT,
        CUSTOMER_SUCCESS: CATEGORY_CUSTOMER_SUCCESS,
        LEGAL: CATEGORY_LEGAL,
    }

    return domain_mapping.get(
        domain,
        CATEGORY_OTHER,
    )


# ============================================================
# CONFIDENCE
# ============================================================

def _calculate_confidence(
    role: RoleClassification,
    required_skills: list[str],
    experience_level: str,
) -> float:

    score = 0.0

    if role.family != UNKNOWN_FAMILY:
        score += 0.50

    if role.domain != UNKNOWN:
        score += 0.20

    if required_skills:
        score += 0.15

    if experience_level != "unknown":
        score += 0.10

    if role.matched_signals:
        score += 0.05

    return round(
        min(score, 1.0),
        3,
    )


# ============================================================
# MAIN CLASSIFIER
# ============================================================

def classify_job(
    title: str,
    description: str = "",
    skills: Optional[list[str]] = None,
    experience_level: Optional[str] = None,
) -> JobClassification:

    title = title or ""
    description = description or ""
    skills = skills or []

    role: RoleClassification = classify_role(
        title=title,
        description=description,
        skills=skills,
    )

    classified_experience = classify_experience(
        title=title,
        description=description,
        source_experience_level=experience_level,
    )

    required_skills = extract_required_skills(
        title=title,
        description=description,
        existing_skills=skills,
    )

    preferred_skills = extract_preferred_skills(
        description=description,
    )

    required_normalized = {
        _normalize(skill)
        for skill in required_skills
    }

    preferred_skills = [
        skill
        for skill in preferred_skills
        if _normalize(skill) not in required_normalized
    ]

    category = _category_from_family(
        family=role.family,
        domain=role.domain,
    )

    confidence = _calculate_confidence(
        role=role,
        required_skills=required_skills,
        experience_level=classified_experience,
    )

    return JobClassification(
        domain=role.domain,
        family=role.family,
        category=category,
        experience_level=classified_experience,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        role_signals=list(role.matched_signals),
        confidence=confidence,
        classification_version=CLASSIFICATION_VERSION,
    )