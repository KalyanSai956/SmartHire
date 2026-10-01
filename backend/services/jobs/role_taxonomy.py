from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


# ============================================================
# DOMAIN TYPES
# ============================================================

TECHNOLOGY = "technology"

MARKETING = "marketing"
SALES = "sales"
DESIGN = "design"
HUMAN_RESOURCES = "human_resources"
FINANCE = "finance"
OPERATIONS = "operations"
LEGAL = "legal"
CUSTOMER_SUCCESS = "customer_success"
CONTENT = "content"

UNKNOWN = "unknown"


# ============================================================
# ROLE FAMILIES
# ============================================================

SOFTWARE_ENGINEERING = "software_engineering"
BACKEND = "backend"
FRONTEND = "frontend"
FULL_STACK = "full_stack"
AI_ML = "ai_ml"
DATA = "data"
DEVOPS_CLOUD = "devops_cloud"
QA_AUTOMATION = "qa_automation"
CYBERSECURITY = "cybersecurity"
MOBILE = "mobile"
DATABASE = "database"
IT_SUPPORT = "it_support"
EMBEDDED = "embedded"

MARKETING_FAMILY = "marketing"
SALES_FAMILY = "sales"
DESIGN_FAMILY = "design"
HR_FAMILY = "human_resources"
FINANCE_FAMILY = "finance"
OPERATIONS_FAMILY = "operations"
CONTENT_FAMILY = "content"
CUSTOMER_SUCCESS_FAMILY = "customer_success"
LEGAL_FAMILY = "legal"

PRODUCT_MANAGEMENT = "product_management"
BUSINESS_ANALYSIS = "business_analysis"

UNKNOWN_FAMILY = "unknown"


TECH_FAMILIES = {
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
}


NON_TECH_FAMILIES = {
    MARKETING_FAMILY,
    SALES_FAMILY,
    DESIGN_FAMILY,
    HR_FAMILY,
    FINANCE_FAMILY,
    OPERATIONS_FAMILY,
    CONTENT_FAMILY,
    CUSTOMER_SUCCESS_FAMILY,
    LEGAL_FAMILY,
    PRODUCT_MANAGEMENT,
    BUSINESS_ANALYSIS,
}


@dataclass(frozen=True)
class RoleClassification:
    domain: str
    family: str
    confidence: float
    matched_signals: tuple[str, ...] = ()

    @property
    def is_technical(self) -> bool:
        return self.domain == TECHNOLOGY


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()

    # Normalize common technology spellings.
    replacements = {
        "node.js": "nodejs",
        "node js": "nodejs",
        "react.js": "react",
        "react js": "react",
        "next.js": "nextjs",
        "next js": "nextjs",
        "vue.js": "vue",
        "vue js": "vue",
        "c++": "cpp",
        "c#": "csharp",
        ".net": "dotnet",
        "machine-learning": "machine learning",
        "deep-learning": "deep learning",
        "artificial-intelligence": "artificial intelligence",
        "full-stack": "full stack",
        "front-end": "frontend",
        "back-end": "backend",
        "dev-ops": "devops",
        "quality-assurance": "quality assurance",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _contains_any(text: str, signals: Iterable[str]) -> list[str]:
    normalized = normalize_text(text)

    matched = []

    for signal in signals:
        signal_normalized = normalize_text(signal)

        if not signal_normalized:
            continue

        # Word/phrase boundary matching prevents things like:
        # "sales" accidentally matching unrelated text.
        pattern = rf"(?<![a-z0-9]){re.escape(signal_normalized)}(?![a-z0-9])"

        if re.search(pattern, normalized):
            matched.append(signal)

    return matched


# ============================================================
# TECHNOLOGY ROLE SIGNALS
# ============================================================

TECH_ROLE_SIGNALS: dict[str, tuple[str, ...]] = {
    BACKEND: (
        "backend engineer",
        "backend developer",
        "back end engineer",
        "back end developer",
        "server side engineer",
        "server-side engineer",
        "api engineer",
        "api developer",
        "python backend",
        "java backend",
        "nodejs backend",
        "django developer",
        "fastapi developer",
        "spring boot developer",
    ),

    FRONTEND: (
        "frontend engineer",
        "frontend developer",
        "front end engineer",
        "front end developer",
        "ui engineer",
        "ui developer",
        "react developer",
        "react engineer",
        "angular developer",
        "vue developer",
        "web developer",
    ),

    FULL_STACK: (
        "full stack engineer",
        "full stack developer",
        "fullstack engineer",
        "fullstack developer",
        "mern developer",
        "mean stack developer",
        "software engineer full stack",
    ),

    AI_ML: (
        "ai engineer",
        "ai developer",
        "artificial intelligence engineer",
        "machine learning engineer",
        "machine learning developer",
        "ml engineer",
        "ml developer",
        "deep learning engineer",
        "computer vision engineer",
        "nlp engineer",
        "nlp developer",
        "generative ai engineer",
        "genai engineer",
        "llm engineer",
        "data scientist",
        "applied scientist",
        "research engineer",
    ),

    DATA: (
        "data engineer",
        "data engineering",
        "analytics engineer",
        "data analyst",
        "data scientist",
        "business intelligence developer",
        "bi developer",
        "etl developer",
        "data platform engineer",
    ),

    DEVOPS_CLOUD: (
        "devops engineer",
        "devops developer",
        "site reliability engineer",
        "sre",
        "cloud engineer",
        "cloud developer",
        "platform engineer",
        "infrastructure engineer",
        "cloud architect",
        "devsecops engineer",
        "release engineer",
        "build engineer",
    ),

    QA_AUTOMATION: (
        "qa engineer",
        "qa automation engineer",
        "automation engineer",
        "test automation engineer",
        "software test engineer",
        "quality assurance engineer",
        "sdet",
        "software development engineer in test",
    ),

    CYBERSECURITY: (
        "cybersecurity engineer",
        "security engineer",
        "security analyst",
        "information security",
        "application security",
        "cloud security",
        "security operations",
        "soc analyst",
    ),

    MOBILE: (
        "android developer",
        "android engineer",
        "ios developer",
        "ios engineer",
        "mobile developer",
        "mobile engineer",
        "flutter developer",
        "react native developer",
    ),

    DATABASE: (
        "database administrator",
        "database engineer",
        "database developer",
        "sql developer",
        "data base administrator",
    ),

    IT_SUPPORT: (
        "it support",
        "technical support engineer",
        "support engineer",
        "system administrator",
        "systems administrator",
        "network administrator",
        "network engineer",
        "desktop support",
    ),

    EMBEDDED: (
        "embedded engineer",
        "embedded software engineer",
        "embedded developer",
        "firmware engineer",
        "firmware developer",
        "embedded systems engineer",
    ),

    SOFTWARE_ENGINEERING: (
        "software engineer",
        "software developer",
        "software development engineer",
        "application developer",
        "application engineer",
        "programmer",
        "developer",
        "engineering intern",
        "software intern",
        "sde",
    ),
}


# ============================================================
# NON-TECH ROLE SIGNALS
# ============================================================

NON_TECH_ROLE_SIGNALS: dict[str, tuple[str, ...]] = {
    MARKETING_FAMILY: (
        "marketing manager",
        "marketing specialist",
        "digital marketing",
        "growth marketing",
        "product marketing",
        "marketing associate",
        "marketing coordinator",
        "seo specialist",
        "seo content",
        "brand marketing",
        "performance marketing",
        "marketing intern",
    ),

    SALES_FAMILY: (
        "sales representative",
        "sales executive",
        "sales manager",
        "account executive",
        "business development representative",
        "business development executive",
        "bdr",
        "sales development representative",
        "sdr",
        "inside sales",
        "field sales",
        "account manager",
    ),

    DESIGN_FAMILY: (
        "visual designer",
        "graphic designer",
        "product designer",
        "ux designer",
        "ui designer",
        "ux/ui designer",
        "interaction designer",
        "creative designer",
        "brand designer",
        "design intern",
    ),

    HR_FAMILY: (
        "human resources",
        "hr manager",
        "hr specialist",
        "hr associate",
        "recruiter",
        "recruitment specialist",
        "talent acquisition",
        "people operations",
        "people partner",
    ),

    FINANCE_FAMILY: (
        "financial analyst",
        "finance analyst",
        "accountant",
        "accounting",
        "financial controller",
        "finance manager",
        "investment analyst",
        "tax analyst",
        "audit associate",
    ),

    OPERATIONS_FAMILY: (
        "operations manager",
        "operations analyst",
        "operations associate",
        "program coordinator",
        "operations specialist",
        "business operations",
        "grocery operations",
        "supply chain",
        "procurement",
    ),

    CONTENT_FAMILY: (
        "content writer",
        "content marketer",
        "content specialist",
        "copywriter",
        "technical writer",
        "content strategist",
        "editor",
        "content associate",
        "seo writer",
    ),

    CUSTOMER_SUCCESS_FAMILY: (
        "customer success",
        "customer success manager",
        "customer support",
        "customer service",
        "client success",
        "customer experience",
    ),

    LEGAL_FAMILY: (
        "legal counsel",
        "legal associate",
        "legal analyst",
        "attorney",
        "lawyer",
        "compliance officer",
        "legal intern",
    ),

    PRODUCT_MANAGEMENT: (
        "product manager",
        "product management",
        "associate product manager",
        "apm",
        "product owner",
    ),

    BUSINESS_ANALYSIS: (
        "business analyst",
        "business analysis",
        "business intelligence analyst",
    ),
}


# ============================================================
# TECH SKILLS
# ============================================================

TECH_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "cpp",
    "csharp",
    "go",
    "golang",
    "rust",
    "php",
    "ruby",
    "kotlin",
    "swift",

    "react",
    "angular",
    "vue",
    "nextjs",
    "nodejs",
    "express",
    "fastapi",
    "django",
    "flask",
    "spring",
    "spring boot",

    "html",
    "css",
    "bootstrap",

    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "oracle",

    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",

    "git",
    "github",
    "linux",

    "machine learning",
    "deep learning",
    "artificial intelligence",
    "computer vision",
    "natural language processing",
    "nlp",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "pandas",
    "numpy",
    "langchain",
    "langgraph",
    "openai",
    "groq",

    "selenium",
    "playwright",
    "cypress",

    "cybersecurity",
    "networking",
    "rest api",
    "graphql",
}


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_role(
    title: str | None,
    description: str | None = None,
    skills: Iterable[str] | None = None,
) -> RoleClassification:
    """
    Classify a job/resume role.

    Title is intentionally weighted much more heavily than description.
    This prevents a job such as "Content Marketer" from becoming technical
    merely because its description contains words like Python or analytics.
    """

    title_text = normalize_text(title)
    description_text = normalize_text(description)

    skills_text = " ".join(
        normalize_text(skill)
        for skill in (skills or [])
        if skill
    )

    # --------------------------------------------------------
    # 1. TITLE-FIRST CLASSIFICATION
    # --------------------------------------------------------

    tech_candidates: list[tuple[str, int, list[str]]] = []
    nontech_candidates: list[tuple[str, int, list[str]]] = []

    for family, signals in TECH_ROLE_SIGNALS.items():
        matched = _contains_any(title_text, signals)

        if matched:
            score = max(len(signal.split()) for signal in matched) * 20
            tech_candidates.append((family, score, matched))

    for family, signals in NON_TECH_ROLE_SIGNALS.items():
        matched = _contains_any(title_text, signals)

        if matched:
            score = max(len(signal.split()) for signal in matched) * 20
            nontech_candidates.append((family, score, matched))

    # Explicit title classification wins.
    if tech_candidates or nontech_candidates:
        all_candidates = [
            (TECHNOLOGY, family, score, signals)
            for family, score, signals in tech_candidates
        ] + [
            (UNKNOWN, family, score, signals)
            for family, score, signals in nontech_candidates
        ]

        all_candidates.sort(key=lambda item: item[2], reverse=True)

        domain, family, score, signals = all_candidates[0]

        if domain == TECHNOLOGY:
            return RoleClassification(
                domain=TECHNOLOGY,
                family=family,
                confidence=min(1.0, 0.75 + score / 200),
                matched_signals=tuple(signals),
            )

        return RoleClassification(
            domain=family,
            family=family,
            confidence=min(1.0, 0.75 + score / 200),
            matched_signals=tuple(signals),
        )

    # --------------------------------------------------------
    # 2. DESCRIPTION / SKILL CLASSIFICATION
    # --------------------------------------------------------

    combined_text = f"{title_text} {description_text} {skills_text}"

    tech_skill_matches = []

    for skill in TECH_SKILLS:
        if skill in combined_text:
            tech_skill_matches.append(skill)

    tech_family_candidates: list[tuple[str, int, list[str]]] = []

    for family, signals in TECH_ROLE_SIGNALS.items():
        matched = _contains_any(combined_text, signals)

        if matched:
            tech_family_candidates.append(
                (
                    family,
                    len(matched),
                    matched,
                )
            )

    if tech_family_candidates:
        tech_family_candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        family, score, signals = tech_family_candidates[0]

        return RoleClassification(
            domain=TECHNOLOGY,
            family=family,
            confidence=min(
                0.90,
                0.55
                + (len(tech_skill_matches) * 0.03)
                + (score * 0.05),
            ),
            matched_signals=tuple(
                signals + tech_skill_matches[:8]
            ),
        )

    # --------------------------------------------------------
    # 3. NON-TECH DESCRIPTION CLASSIFICATION
    # --------------------------------------------------------

    nontech_candidates = []

    for family, signals in NON_TECH_ROLE_SIGNALS.items():
        matched = _contains_any(combined_text, signals)

        if matched:
            nontech_candidates.append(
                (
                    family,
                    len(matched),
                    matched,
                )
            )

    if nontech_candidates:
        nontech_candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        family, score, signals = nontech_candidates[0]

        return RoleClassification(
            domain=family,
            family=family,
            confidence=min(
                0.90,
                0.55 + score * 0.08,
            ),
            matched_signals=tuple(signals),
        )

    # --------------------------------------------------------
    # 4. TECH SKILL-ONLY FALLBACK
    # --------------------------------------------------------

    if len(tech_skill_matches) >= 2:
        return RoleClassification(
            domain=TECHNOLOGY,
            family=SOFTWARE_ENGINEERING,
            confidence=min(
                0.85,
                0.50 + len(tech_skill_matches) * 0.04,
            ),
            matched_signals=tuple(tech_skill_matches[:10]),
        )

    return RoleClassification(
        domain=UNKNOWN,
        family=UNKNOWN_FAMILY,
        confidence=0.0,
        matched_signals=(),
    )


# ============================================================
# RESUME CLASSIFICATION
# ============================================================

def classify_resume(
    resume_text: str,
    resume_skills: Iterable[str] | None = None,
    target_roles: Iterable[str] | None = None,
) -> RoleClassification:
    """
    Build a career-domain classification from resume content.

    Target roles are deliberately considered first because they represent
    the candidate's intended career direction.
    """

    target_roles_text = " ".join(
        str(role)
        for role in (target_roles or [])
        if role
    )

    if target_roles_text.strip():
        target_classification = classify_role(
            title=target_roles_text,
            description=resume_text,
            skills=resume_skills,
        )

        if target_classification.domain != UNKNOWN:
            return target_classification

    return classify_role(
        title="",
        description=resume_text,
        skills=resume_skills,
    )