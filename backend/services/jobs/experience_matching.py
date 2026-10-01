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
    text = f"{title}\n{description}\n{source_level or ''}".lower()

    range_patterns = (
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)",
        r"minimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"at\s+least\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
    )

    for pattern in range_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        if "to" in pattern or "-" in pattern:
            return float(match.group(1)), float(match.group(2))
        years = float(match.group(1))
        return years, None

    level = normalize_experience(classified_level or source_level)
    level_minimums = {
        "intern": 0.0,
        "fresher": 0.0,
        "entry": 0.0,
        "junior": 0.0,
        "mid": 2.0,
        "senior": 5.0,
        "lead": 7.0,
        "manager": 5.0,
        "director": 10.0,
    }

    if level in level_minimums:
        return level_minimums[level], None

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
