from __future__ import annotations

import re
from typing import Any

EXPERIENCE_LIMITS = {
    "student": (0.0, 0.0),
    "fresher": (0.0, 0.0),
    "less than 1 year": (0.0, 1.0),
    "less than one year": (0.0, 1.0),
    "1–2 years": (1.0, 2.0),
    "1-2 years": (1.0, 2.0),
    "1 to 2 years": (1.0, 2.0),
    "2–5 years": (2.0, 5.0),
    "2-5 years": (2.0, 5.0),
    "2 to 5 years": (2.0, 5.0),
    "5+ years": (5.0, None),
    "5 plus years": (5.0, None),
}


def normalize_experience(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def profile_experience_range(value: Any) -> tuple[float, float | None]:
    text = normalize_experience(value)
    if text in EXPERIENCE_LIMITS:
        return EXPERIENCE_LIMITS[text]

    if "student" in text or "fresher" in text:
        return 0.0, 0.0

    if "less than" in text and "year" in text:
        return 0.0, 1.0

    match = re.search(r"(\d+(?:\.\d+)?)\s*[-to]+\s*(\d+(?:\.\d+)?)", text)
    if match:
        return float(match.group(1)), float(match.group(2))

    match = re.search(r"(\d+(?:\.\d+)?)\s*\+", text)
    if match:
        return float(match.group(1)), None

    match = re.search(r"(\d+(?:\.\d+)?)\s*years?", text)
    if match:
        years = float(match.group(1))
        return years, years

    return 0.0, None


def extract_job_experience_range(
    *,
    title: str = "",
    description: str = "",
    classified_level: str | None = None,
    source_level: str | None = None,
) -> tuple[float, float | None]:
    """
    Determine the minimum experience required by a job.

    Priority:
    1. Explicit classified experience level
    2. Source experience level
    3. Explicit years in title/description

    The classified/source level must take precedence over arbitrary
    year mentions inside a job description. For example, an internship
    description may mention experience requirements for preferred
    qualifications, but an explicitly classified 'intern' job should
    remain compatible with a fresher.
    """

    # ---------------------------------------------------------
    # 1. Explicit classified experience level
    # ---------------------------------------------------------

    classified = normalize_experience(
        classified_level
    )

    explicit_level_minimums = {
        "intern": 0.0,
        "internship": 0.0,
        "student": 0.0,
        "fresher": 0.0,
        "entry": 0.0,
        "entry level": 0.0,
        "entry-level": 0.0,
        "junior": 0.0,

        "mid": 2.0,
        "intermediate": 2.0,

        "senior": 5.0,
        "lead": 7.0,
        "manager": 5.0,
        "director": 10.0,
    }

    if classified in explicit_level_minimums:
        return explicit_level_minimums[classified], None

    # ---------------------------------------------------------
    # 2. Source experience level
    # ---------------------------------------------------------

    source = normalize_experience(
        source_level
    )

    if source in explicit_level_minimums:
        return explicit_level_minimums[source], None

    # ---------------------------------------------------------
    # 3. Only if no explicit level exists, inspect text
    # ---------------------------------------------------------

    text = (
        f"{title}\n"
        f"{description}"
    ).lower()

    range_patterns = (
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        r"(\d+(?:\.\d+)?)\s*\+\s*"
        r"(?:years?|yrs?)",

        r"minimum\s+(?:of\s+)?"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        r"at\s+least\s+"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",

        r"(\d+(?:\.\d+)?)\s*"
        r"(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience",
    )

    for pattern in range_patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        # Range: 1-2 years / 1 to 2 years
        if len(match.groups()) >= 2:
            return (
                float(match.group(1)),
                float(match.group(2)),
            )

        # Minimum: 2+ years / at least 2 years
        years = float(match.group(1))

        return years, None

    # ---------------------------------------------------------
    # 4. Unknown
    # ---------------------------------------------------------

    return 0.0, None

def experience_compatible(
    profile_experience: Any,
    *,
    job_title: str = "",
    job_description: str = "",
    job_experience_level: str | None = None,
    source_experience_level: str | None = None,
) -> bool:
    profile_min, profile_max = profile_experience_range(profile_experience)
    job_min, _job_max = extract_job_experience_range(
        title=job_title,
        description=job_description,
        classified_level=job_experience_level,
        source_level=source_experience_level,
    )

    if job_min <= profile_min:
        return True

    if profile_max is not None and job_min <= profile_max:
        return True

    return False


def experience_score(
    profile_experience: Any,
    *,
    job_title: str = "",
    job_description: str = "",
    job_experience_level: str | None = None,
    source_experience_level: str | None = None,
) -> float:
    if experience_compatible(
        profile_experience,
        job_title=job_title,
        job_description=job_description,
        job_experience_level=job_experience_level,
        source_experience_level=source_experience_level,
    ):
        profile_min, profile_max = profile_experience_range(profile_experience)
        job_min, _ = extract_job_experience_range(
            title=job_title,
            description=job_description,
            classified_level=job_experience_level,
            source_level=source_experience_level,
        )
        if profile_max is not None and job_min > profile_max:
            return 50.0
        if job_min > profile_min:
            return 85.0
        return 100.0

    return 0.0


def profile_experience_level(value: Any) -> str:
    text = normalize_experience(value)
    if text in {"student", "fresher", "less than 1 year", "less than one year"}:
        return "entry"
    if text in {"1-2 years", "1 to 2 years"}:
        return "entry"
    if text in {"2-5 years", "2 to 5 years"}:
        return "mid"
    if text in {"5+ years", "5 plus years"}:
        return "senior"
    return text or "unknown"
