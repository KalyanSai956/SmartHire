"""
Resume Grammar & Spelling Checker
---------------------------------
LanguageTool-based grammar/spelling checker with:
- Technical vocabulary filtering
- Proper-name/entity filtering
- Resume-aware filtering
- Correct LanguageTool 6.x attribute handling
- Severity classification
- Safe fallback when LanguageTool is unavailable
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ============================================================================
# TECHNICAL / RESUME VOCABULARY
# ============================================================================

IGNORED_WORDS: Set[str] = {
    # Programming languages
    "python",
    "javascript",
    "typescript",
    "java",
    "kotlin",
    "swift",
    "golang",
    "go",
    "rust",
    "ruby",
    "php",
    "scala",
    "perl",
    "dart",
    "r",
    "c",
    "cpp",
    "c++",
    "csharp",
    "c#",
    "html",
    "css",
    "scss",
    "sass",
    "sql",
    "nosql",
    "bash",
    "shell",
    "powershell",

    # JS ecosystem
    "node",
    "nodejs",
    "node.js",
    "react",
    "reactjs",
    "react.js",
    "next",
    "nextjs",
    "next.js",
    "vite",
    "webpack",
    "babel",
    "npm",
    "npx",
    "yarn",
    "pnpm",
    "jsx",
    "tsx",
    "js",
    "ts",

    # Backend / frameworks
    "fastapi",
    "flask",
    "django",
    "express",
    "expressjs",
    "spring",
    "springboot",
    "spring-boot",
    "nestjs",
    "nest.js",
    "laravel",
    "dotnet",
    ".net",

    # AI / ML
    "ai",
    "ml",
    "aiml",
    "llm",
    "llms",
    "nlp",
    "rag",
    "generative",
    "transformer",
    "transformers",
    "bert",
    "gpt",
    "gemini",
    "groq",
    "openai",
    "anthropic",
    "claude",
    "sentence-transformers",
    "sentencetransformers",
    "spacy",
    "spaCy",
    "tensorflow",
    "pytorch",
    "torch",
    "keras",
    "scikit-learn",
    "sklearn",
    "numpy",
    "pandas",
    "matplotlib",
    "opencv",
    "dlib",

    # Databases
    "mongodb",
    "mongo",
    "mongoose",
    "postgresql",
    "postgres",
    "mysql",
    "sqlite",
    "redis",
    "supabase",
    "firebase",
    "dynamodb",
    "cassandra",
    "elasticsearch",
    "neo4j",
    "prisma",

    # Cloud / DevOps
    "aws",
    "azure",
    "gcp",
    "docker",
    "dockerfile",
    "kubernetes",
    "k8s",
    "helm",
    "terraform",
    "jenkins",
    "github",
    "gitlab",
    "bitbucket",
    "github-actions",
    "ci",
    "cd",
    "cicd",
    "devops",
    "vercel",
    "netlify",
    "nginx",

    # APIs / tools
    "api",
    "apis",
    "rest",
    "restful",
    "graphql",
    "http",
    "https",
    "json",
    "xml",
    "yaml",
    "yml",
    "jwt",
    "oauth",
    "oauth2",
    "cors",
    "sdk",
    "cli",
    "ui",
    "ux",
    "url",
    "uri",

    # Libraries / tools
    "streamlit",
    "langchain",
    "languagechain",
    "language-tool",
    "languagetool",
    "beautifulsoup",
    "bs4",
    "playwright",
    "selenium",
    "pytest",
    "uvicorn",
    "pydantic",
    "celery",
    "rabbitmq",
    "kafka",

    # General technical terms
    "backend",
    "frontend",
    "fullstack",
    "full-stack",
    "middleware",
    "microservices",
    "microservice",
    "repository",
    "repositories",
    "runtime",
    "deployment",
    "deployments",
    "authentication",
    "authorization",
    "middleware",
    "endpoint",
    "endpoints",
    "webhook",
    "webhooks",
    "database",
    "databases",
    "codebase",
    "codebases",
    "debugging",
    "debugger",
    "refactoring",
    "scalability",
    "scalable",
    "containerization",
    "containerized",
    "virtualenv",
    "venv",
    "requirements",
    "requirements.txt",
    "readme",
    "README",
    "markdown",
    "regex",
    "regexp",
    "tokenizer",
    "tokenization",
    "embedding",
    "embeddings",
    "vector",
    "vectors",
    "vectorstore",
    "vector-store",
    "semantic",
    "semantics",
    "prompt",
    "prompts",
    "inference",
    "fine-tuning",
    "finetuning",
    "pipeline",
    "pipelines",
    "workflow",
    "workflows",
    "agent",
    "agents",
    "agentic",
    "chatbot",
    "chatbots",
    "dashboard",
    "dashboards",
    "streaming",
    "async",
    "asyncio",
    "asynchronous",
    "synchronous",
    "multithreading",
    "multiprocessing",

    # Resume-specific
    "ats",
    "cv",
    "resumé",
    "resume",
    "resumes",
    "btech",
    "b.tech",
    "cse",
    "cgpa",
    "sgpa",
    "gpa",
    "intern",
    "internship",
    "internships",
    "projects",
    "project",
    "certifications",
    "certification",
    "coursework",
    "course",
    "skills",
    "skillset",
    "experience",
    "achievements",
    "achievement",
}


# ============================================================================
# COMMON PROPER NAMES / ENTITIES
# ============================================================================
#
# These are intentionally limited to names/organizations that commonly appear
# in resumes and are not useful grammar corrections.
#
# Additional proper nouns can be detected contextually below.
#

KNOWN_ENTITIES: Set[str] = {
    # Universities / education
    "university",
    "college",
    "institute",
    "school",

    # Common locations / countries
    "india",
    "andhra",
    "pradesh",
    "telangana",
    "hyderabad",
    "tirupati",
    "chennai",
    "bangalore",
    "bengaluru",
    "mumbai",
    "delhi",
    "pune",
    "anantapur",
    "vijayawada",
    "visakhapatnam",
    "vizag",

    # Major companies / organizations
    "google",
    "microsoft",
    "amazon",
    "apple",
    "meta",
    "netflix",
    "infosys",
    "cognizant",
    "accenture",
    "tcs",
    "wipro",
    "ibm",
    "oracle",
    "adobe",
    "salesforce",
    "linkedin",
    "ltimindtree",
}


# ============================================================================
# LANGUAGE TOOL
# ============================================================================

_LANGUAGE_TOOL = None
_LANGUAGE_TOOL_STATUS = "not_initialized"


def _load_language_tool():
    """
    Load LanguageTool lazily.

    This avoids loading the Java-based LanguageTool server during module
    import and makes the service easier to start.
    """
    global _LANGUAGE_TOOL
    global _LANGUAGE_TOOL_STATUS

    if _LANGUAGE_TOOL is not None:
        return _LANGUAGE_TOOL

    try:
        import language_tool_python

        logger.info("Loading LanguageTool...")

        _LANGUAGE_TOOL = language_tool_python.LanguageTool("en-US")

        _LANGUAGE_TOOL_STATUS = "available"

        logger.info("LanguageTool loaded successfully.")

        return _LANGUAGE_TOOL

    except Exception as exc:
        _LANGUAGE_TOOL_STATUS = "unavailable"

        logger.exception(
            "Unable to load LanguageTool: %s",
            exc,
        )

        return None


# ============================================================================
# LANGUAGE TOOL MATCH COMPATIBILITY
# ============================================================================

def _get_match_offset(match: Any) -> int:
    """
    LanguageTool versions use slightly different attribute names.
    """
    return int(
        getattr(match, "offset", 0) or 0
    )


def _get_match_error_length(match: Any) -> int:
    """
    New language-tool-python:
        error_length

    Older versions:
        errorLength
    """
    return int(
        getattr(
            match,
            "error_length",
            getattr(match, "errorLength", 0),
        )
        or 0
    )


def _get_match_rule_id(match: Any) -> str:
    """
    New language-tool-python:
        rule_id

    Older versions:
        ruleId
    """
    return str(
        getattr(
            match,
            "rule_id",
            getattr(match, "ruleId", ""),
        )
        or ""
    )


def _get_match_issue_type(match: Any) -> str:
    """
    New language-tool-python:
        rule_issue_type

    Older versions:
        ruleIssueType
    """
    return str(
        getattr(
            match,
            "rule_issue_type",
            getattr(match, "ruleIssueType", ""),
        )
        or ""
    )


def _get_match_message(match: Any) -> str:
    return str(
        getattr(match, "message", "")
        or ""
    )


def _get_match_replacements(match: Any) -> List[str]:
    replacements = getattr(
        match,
        "replacements",
        [],
    )

    if not replacements:
        return []

    return [
        str(item)
        for item in replacements[:5]
        if item
    ]


# ============================================================================
# TOKEN / TEXT HELPERS
# ============================================================================

def _normalize_word(word: str) -> str:
    """
    Normalize a token for dictionary comparisons.
    """
    return (
        word.strip()
        .lower()
        .replace("’", "'")
    )


def _is_technical_token(word: str) -> bool:
    """
    Determine whether a token is clearly technical.

    IMPORTANT:
    We intentionally do not ignore every capitalized word.
    A misspelled technical term such as 'Javascrpt' should still be detected.
    """

    if not word:
        return True

    normalized = _normalize_word(word)

    # Exact dictionary
    if normalized in IGNORED_WORDS:
        return True

    if normalized in KNOWN_ENTITIES:
        return True

    # URLs / emails
    if "@" in word:
        return True

    if re.search(
        r"(https?://|www\.|\.com\b|\.org\b|\.in\b|\.io\b|\.dev\b)",
        word,
        re.IGNORECASE,
    ):
        return True

    # File extensions
    if re.fullmatch(
        r"[A-Za-z0-9_-]+\.(py|js|jsx|ts|tsx|java|cpp|c|h|css|html|json|yaml|yml|md|txt|pdf)",
        word,
        re.IGNORECASE,
    ):
        return True

    # Package names / version-like values
    if re.search(r"\d+\.\d+", word):
        return True

    # CamelCase / PascalCase technical identifiers
    if re.search(r"[a-z][A-Z]", word):
        return True

    # Obvious code identifiers
    if "_" in word:
        return True

    # CLI flags
    if word.startswith("--"):
        return True

    return False


def _is_all_caps(word: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", word)

    return bool(
        letters
        and len(letters) >= 2
        and letters.isupper()
    )


def _is_title_case(word: str) -> bool:
    """
    True for:
        Pasupuleti
        Tirupati
        Microsoft

    False for:
        repsitary
        regrssion
        compatibity
    """
    if not word:
        return False

    letters = re.sub(r"[^A-Za-z]", "", word)

    if not letters:
        return False

    return (
        letters[0].isupper()
        and letters[1:].islower()
    )


def _looks_like_person_or_entity(
    text: str,
    full_text: str,
    offset: int,
) -> bool:
    """
    Resume-aware proper noun heuristic.

    This is deliberately conservative. It mainly protects:
    - names
    - cities
    - universities
    - companies
    - project names
    - section/entity labels

    We do NOT ignore lowercase misspellings.
    """

    word = text.strip()

    if not word:
        return False

    normalized = _normalize_word(word)

    # Explicit entity dictionary.
    if normalized in KNOWN_ENTITIES:
        return True

    # Technical terms should be handled separately.
    if _is_technical_token(word):
        return True

    # All-uppercase abbreviations are normally technical/resume entities.
    if _is_all_caps(word):
        return True

    # Only apply proper-noun heuristic to title-case words.
    if not _is_title_case(word):
        return False

    before = full_text[max(0, offset - 100):offset]
    after = full_text[
        offset + len(word):
        min(len(full_text), offset + len(word) + 100)
    ]

    context = f"{before} {after}".lower()

    # Contact/header context.
    header_keywords = (
        "email",
        "phone",
        "mobile",
        "contact",
        "linkedin",
        "github",
        "address",
    )

    if any(keyword in context for keyword in header_keywords):
        return True

    # Education/entity context.
    education_keywords = (
        "university",
        "college",
        "institute",
        "school",
        "education",
        "bachelor",
        "degree",
        "b.tech",
        "btech",
        "master",
        "m.tech",
        "mtech",
    )

    if any(keyword in context for keyword in education_keywords):
        return True

    # Experience/company context.
    experience_keywords = (
        "company",
        "organization",
        "worked at",
        "interned at",
        "internship at",
        "experience",
        "developer at",
        "engineer at",
    )

    if any(keyword in context for keyword in experience_keywords):
        return True

    # Location context.
    location_keywords = (
        "location",
        "located",
        "based in",
        "from",
        "city",
        "state",
        "address",
    )

    if any(keyword in context for keyword in location_keywords):
        return True

    return False


def _is_inside_email_or_url(
    full_text: str,
    offset: int,
    length: int,
) -> bool:
    """
    Ignore grammar matches inside email addresses and URLs.
    """

    start = max(0, offset - 150)
    end = min(len(full_text), offset + length + 150)

    surrounding = full_text[start:end]

    if re.search(
        r"\S+@\S+",
        surrounding,
    ):
        return True

    if re.search(
        r"https?://\S+|www\.\S+",
        surrounding,
        re.IGNORECASE,
    ):
        return True

    return False


# ============================================================================
# RULE CLASSIFICATION
# ============================================================================

def _is_style_or_format_rule(
    rule_id: str,
    issue_type: str,
) -> bool:
    """
    Detect LanguageTool rules that are mostly formatting/style rather than
    genuine spelling mistakes.
    """

    rule = rule_id.upper()

    style_rules = {
        "PROBLEM_SOLVE_HYPHEN",
        "EN_SPLIT_WORDS_HYPHEN",
        "EN_COMPOUNDS_MULTI_FACTOR",
        "FILE_EXTENSIONS_CASE",
        "NODE_JS",
        "MORFOLOGIK_RULE_EN_US",
    }

    # Explicit formatting rules.
    if rule in {
        "PROBLEM_SOLVE_HYPHEN",
        "EN_SPLIT_WORDS_HYPHEN",
        "EN_COMPOUNDS_MULTI_FACTOR",
        "FILE_EXTENSIONS_CASE",
        "NODE_JS",
    }:
        return True

    # Grammar issue types should not automatically become critical.
    if issue_type.lower() in {
        "typographical",
        "style",
        "duplication",
    }:
        return True

    return False


def _classify_error(
    match: Any,
    error_text: str,
) -> str:
    """
    Classify a LanguageTool match as:
        critical = genuine spelling mistake
        moderate = genuine grammar problem
        minor = style / punctuation / formatting
    """

    rule_id = _get_match_rule_id(match)
    issue_type = _get_match_issue_type(match)

    rule_upper = rule_id.upper()
    issue_lower = issue_type.lower()

    # ================================================================
    # 1. STYLE / FORMATTING RULES
    # ================================================================
    #
    # LanguageTool sometimes labels these as "misspelling", even though
    # they are not actual spelling mistakes.
    #

    style_rules = {
        "PROBLEM_SOLVE_HYPHEN",
        "EN_COMPOUNDS_MULTI_FACTOR",
        "EN_SPLIT_WORDS_HYPHEN",
        "FILE_EXTENSIONS_CASE",
        "NODE_JS",
    }

    if rule_upper in style_rules:
        return "minor"

    # Generic formatting/style rules
    if any(
        keyword in rule_upper
        for keyword in (
            "HYPHEN",
            "COMPOUND",
            "PUNCTUATION",
            "WHITESPACE",
            "TYPOGRAPH",
            "CASE",
        )
    ):
        return "minor"

    # ================================================================
    # 2. TRUE SPELLING MISTAKES
    # ================================================================
    if issue_lower == "misspelling":
        return "critical"

    if "MORFOLOGIK" in rule_upper:
        return "critical"

    # ================================================================
    # 3. GRAMMAR
    # ================================================================
    if issue_lower == "grammar":
        return "moderate"

    # ================================================================
    # 4. STYLE / TYPOGRAPHY
    # ================================================================
    if issue_lower in {
        "typographical",
        "style",
        "punctuation",
        "duplication",
    }:
        return "minor"

    # ================================================================
    # 5. SAFE DEFAULT
    # ================================================================
    return "moderate"


# ============================================================================
# MATCH CONVERSION
# ============================================================================

def _build_error(
    match: Any,
    resume_text: str,
) -> Optional[Dict[str, Any]]:
    """
    Convert LanguageTool match into frontend-friendly structure.
    """

    offset = _get_match_offset(match)
    length = _get_match_error_length(match)

    if length <= 0:
        return None

    error_text = resume_text[
        offset:offset + length
    ].strip()

    if not error_text:
        return None

    rule_id = _get_match_rule_id(match)
    issue_type = _get_match_issue_type(match)
    message = _get_match_message(match)
    replacements = _get_match_replacements(match)

    # ------------------------------------------------------------------
    # Technical vocabulary
    # ------------------------------------------------------------------
    if _is_technical_token(error_text):
        logger.debug(
            "Ignoring technical token: %r",
            error_text,
        )
        return None

    # ------------------------------------------------------------------
    # Email / URL
    # ------------------------------------------------------------------
    if _is_inside_email_or_url(
        resume_text,
        offset,
        length,
    ):
        logger.debug(
            "Ignoring match inside email/URL: %r",
            error_text,
        )
        return None

    # ------------------------------------------------------------------
    # Proper names / entities
    # ------------------------------------------------------------------
    if _looks_like_person_or_entity(
        error_text,
        resume_text,
        offset,
    ):
        logger.debug(
            "Ignoring probable entity: %r",
            error_text,
        )
        return None

    severity = _classify_error(
        match,
        error_text,
    )

    return {
        "error_text": error_text,
        "message": message,
        "suggestions": replacements,
        "severity": severity,
        "rule_id": rule_id,
        "issue_type": issue_type,
        "offset": offset,
        "length": length,
    }


# ============================================================================
# DEFAULT FALLBACK
# ============================================================================

def get_default_grammar_results() -> Dict[str, Any]:
    """
    Safe result when LanguageTool is unavailable.

    IMPORTANT:
    This must NOT look like perfect grammar.
    """

    return {
        "total_errors": 0,
        "critical_errors": [],
        "moderate_errors": [],
        "minor_errors": [],

        # None means "not measured".
        "grammar_score": None,
        "penalty_applied": 0.0,
        "error_free_percentage": None,

        "_component_status": "unavailable",
        "_note": "Grammar checking unavailable.",
    }


# ============================================================================
# MAIN CHECKER
# ============================================================================

async def check_resume_grammar(
    resume_text: str,
) -> Dict[str, Any]:
    """
    Check resume text using LanguageTool.

    Returns:
        {
            total_errors,
            critical_errors,
            moderate_errors,
            minor_errors,
            grammar_score,
            penalty_applied,
            error_free_percentage,
            _component_status
        }
    """

    if not resume_text or not resume_text.strip():
        return {
            "total_errors": 0,
            "critical_errors": [],
            "moderate_errors": [],
            "minor_errors": [],
            "grammar_score": None,
            "penalty_applied": 0.0,
            "error_free_percentage": None,
            "_component_status": "available",
            "_note": "No resume text supplied.",
        }

    tool = _load_language_tool()

    if tool is None:
        logger.warning(
            "Grammar checker unavailable."
        )

        return get_default_grammar_results()

    try:
        logger.info(
            "Grammar check text length: %d",
            len(resume_text),
        )

        matches = tool.check(resume_text)

        logger.info(
            "LanguageTool raw matches: %d",
            len(matches),
        )

        critical_errors: List[Dict[str, Any]] = []
        moderate_errors: List[Dict[str, Any]] = []
        minor_errors: List[Dict[str, Any]] = []

        seen = set()

        for match in matches:
            offset = _get_match_offset(match)
            length = _get_match_error_length(match)

            error_text = resume_text[
                offset:offset + length
            ].strip()

            logger.debug(
                "LT match: text=%r rule=%s issue=%s",
                error_text,
                _get_match_rule_id(match),
                _get_match_issue_type(match),
            )

            error = _build_error(
                match,
                resume_text,
            )

            if error is None:
                continue

            # Prevent duplicate entries.
            dedupe_key = (
                error["error_text"].lower(),
                error["rule_id"],
                error["offset"],
            )

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)

            severity = error["severity"]

            if severity == "critical":
                critical_errors.append(error)

            elif severity == "moderate":
                moderate_errors.append(error)

            else:
                minor_errors.append(error)

        total_errors = (
            len(critical_errors)
            + len(moderate_errors)
            + len(minor_errors)
        )

        # ---------------------------------------------------------------
        # Grammar score
        # ---------------------------------------------------------------
        #
        # Critical = 4 points
        # Moderate = 2 points
        # Minor = 0.5 points
        #
        # Cap penalty at 100.
        #

        penalty = (
            len(critical_errors) * 4.0
            + len(moderate_errors) * 2.0
            + len(minor_errors) * 0.5
        )

        penalty = min(
            100.0,
            penalty,
        )

        grammar_score = max(
            0.0,
            100.0 - penalty,
        )

        # A simple error-free percentage based on sentence/word volume.
        # This is not used as a word-level accuracy metric.
        word_count = max(
            1,
            len(
                re.findall(
                    r"\b[\w'-]+\b",
                    resume_text,
                )
            ),
        )

        error_free_percentage = max(
            0.0,
            min(
                100.0,
                100.0
                - (
                    total_errors
                    / word_count
                    * 100.0
                ),
            ),
        )

        result = {
            "total_errors": total_errors,

            "critical_errors": critical_errors,
            "moderate_errors": moderate_errors,
            "minor_errors": minor_errors,

            "grammar_score": round(
                grammar_score,
                2,
            ),

            "penalty_applied": round(
                penalty,
                2,
            ),

            "error_free_percentage": round(
                error_free_percentage,
                2,
            ),

            "_component_status": "available",
            "_note": "Grammar checked with LanguageTool.",
        }

        logger.info(
            "Grammar checker status: available"
        )

        logger.info(
            "Grammar checker final total: %d",
            total_errors,
        )

        logger.info(
            "Critical errors: %d",
            len(critical_errors),
        )

        logger.info(
            "Moderate errors: %d",
            len(moderate_errors),
        )

        logger.info(
            "Minor errors: %d",
            len(minor_errors),
        )

        return result

    except Exception as exc:
        logger.exception(
            "Grammar checking failed: %s",
            exc,
        )

        return get_default_grammar_results()


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

def generate_grammar_recommendations(
    grammar_results: Dict[str, Any],
) -> List[str]:
    """
    Convert grammar errors into resume recommendations.
    """

    recommendations: List[str] = []

    status = grammar_results.get(
        "_component_status"
    )

    if status != "available":
        return recommendations

    total_errors = int(
        grammar_results.get(
            "total_errors",
            0,
        )
        or 0
    )

    if total_errors == 0:
        return recommendations

    critical = grammar_results.get(
        "critical_errors",
        [],
    )

    moderate = grammar_results.get(
        "moderate_errors",
        [],
    )

    minor = grammar_results.get(
        "minor_errors",
        [],
    )

    # ---------------------------------------------------------------
    # Critical
    # ---------------------------------------------------------------

    if critical:
        recommendations.append(
            f"Fix {len(critical)} spelling error(s) before submitting your resume."
        )

        for error in critical[:5]:
            text = error.get(
                "error_text",
                "",
            )

            suggestions = error.get(
                "suggestions",
                [],
            )

            if suggestions:
                recommendations.append(
                    f"Replace '{text}' with '{suggestions[0]}'."
                )
            else:
                recommendations.append(
                    f"Review the spelling of '{text}'."
                )

    # ---------------------------------------------------------------
    # Moderate
    # ---------------------------------------------------------------

    if moderate:
        recommendations.append(
            f"Review {len(moderate)} grammar issue(s) for clearer writing."
        )

        for error in moderate[:3]:
            text = error.get(
                "error_text",
                "",
            )

            suggestions = error.get(
                "suggestions",
                [],
            )

            if suggestions:
                recommendations.append(
                    f"Review '{text}' — consider '{suggestions[0]}'."
                )
            else:
                recommendations.append(
                    f"Review the grammar around '{text}'."
                )

    # ---------------------------------------------------------------
    # Minor
    # ---------------------------------------------------------------

    if minor:
        recommendations.append(
            f"Consider {len(minor)} minor formatting/style improvement(s)."
        )

    return recommendations


# ============================================================================
# STRENGTHS
# ============================================================================

def generate_grammar_strengths(
    grammar_results: Dict[str, Any],
) -> List[str]:
    """
    Generate positive grammar-related resume feedback.

    IMPORTANT:
    Never call an unavailable checker "error-free".
    """

    strengths: List[str] = []

    if (
        grammar_results.get("_component_status")
        != "available"
    ):
        return strengths

    total_errors = int(
        grammar_results.get(
            "total_errors",
            0,
        )
        or 0
    )

    critical = int(
        len(
            grammar_results.get(
                "critical_errors",
                [],
            )
        )
    )

    moderate = int(
        len(
            grammar_results.get(
                "moderate_errors",
                [],
            )
        )
    )

    minor = int(
        len(
            grammar_results.get(
                "minor_errors",
                [],
            )
        )
    )

    if total_errors == 0:
        strengths.append(
            "Error-free grammar and spelling"
        )

    elif critical == 0:
        strengths.append(
            "No major spelling errors detected"
        )

    if moderate == 0:
        strengths.append(
            "Strong grammatical consistency"
        )

    if minor == 0:
        strengths.append(
            "Clean formatting and style"
        )

    return strengths


# ============================================================================
# CLEANUP
# ============================================================================

def close_language_tool() -> None:
    """
    Close LanguageTool server cleanly.
    """

    global _LANGUAGE_TOOL
    global _LANGUAGE_TOOL_STATUS

    if _LANGUAGE_TOOL is None:
        return

    try:
        _LANGUAGE_TOOL.close()

    except Exception as exc:
        logger.warning(
            "Unable to close LanguageTool cleanly: %s",
            exc,
        )

    finally:
        _LANGUAGE_TOOL = None
        _LANGUAGE_TOOL_STATUS = "not_initialized"


# ============================================================================
# OPTIONAL HEALTH CHECK
# ============================================================================

def grammar_checker_status() -> Dict[str, Any]:
    """
    Return current grammar checker status.
    """

    return {
        "status": _LANGUAGE_TOOL_STATUS,
        "available": _LANGUAGE_TOOL is not None,
    }