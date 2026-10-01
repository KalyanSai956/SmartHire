from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional

MATCHER_VERSION = "2.0"

ROLE_WEIGHT = 0.30
REQUIRED_SKILL_WEIGHT = 0.30
SEMANTIC_WEIGHT = 0.20
EXPERIENCE_WEIGHT = 0.10
PREFERRED_SKILL_WEIGHT = 0.05
FRESHNESS_WEIGHT = 0.05


def _normalize(value: Any) -> str:
    value = str(value or "").lower().strip()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9+#.\s-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _normalize_skill(value: Any) -> str:
    value = _normalize(value)

    aliases = {
        "js": "javascript",
        "javascript js": "javascript",
        "ts": "typescript",
        "py": "python",
        "node": "node.js",
        "nodejs": "node.js",
        "reactjs": "react",
        "react.js": "react",
        "nextjs": "next.js",
        "next js": "next.js",
        "postgres": "postgresql",
        "mongo": "mongodb",
        "scikit learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "nlp": "natural language processing",
        "aws cloud": "aws",
        "gcp cloud": "gcp",
    }

    return aliases.get(value, value)


def _unique_skills(values: Optional[List[Any]]) -> List[str]:
    result = []
    seen = set()

    for value in values or []:
        normalized = _normalize_skill(value)

        if not normalized:
            continue

        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result


def _filter_known_skills(values: Optional[List[Any]]) -> List[str]:
    from backend.services.jobs.job_classifier import _extract_skill_mentions

    text = "\n".join(
        str(value)
        for value in values or []
        if value is not None
    )

    return _unique_skills(
        _extract_skill_mentions(text)
    )


def _skill_match(
    resume_skills: Optional[List[Any]],
    job_skills: Optional[List[Any]],
) -> Dict[str, Any]:
    resume = _filter_known_skills(resume_skills)
    job = _filter_known_skills(job_skills)

    if not job:
        return {
            "score": 0.0,
            "matched": [],
            "missing": [],
        }

    matched = []
    missing = []

    resume_set = set(resume)

    for skill in job:
        if skill in resume_set:
            matched.append(skill)
        else:
            missing.append(skill)

    score = (len(matched) / len(job)) * 100

    return {
        "score": round(score, 1),
        "matched": matched,
        "missing": missing,
    }


def _role_score(
    resume_family: Optional[str],
    job_family: Optional[str],
    resume_domain: Optional[str],
    job_domain: Optional[str],
) -> float:
    resume_family = _normalize(resume_family)
    job_family = _normalize(job_family)
    resume_domain = _normalize(resume_domain)
    job_domain = _normalize(job_domain)

    if not resume_family or not job_family:
        return 0.0

    if resume_family == job_family:
        return 100.0

    compatibility = {
        "software_engineering": {
            "software_engineering",
            "backend",
            "frontend",
            "full_stack",
            "ai_ml",
            "data",
            "devops_cloud",
            "qa_automation",
            "cybersecurity",
            "mobile",
            "database",
            "it_support",
            "embedded",
        },
        "backend": {
            "backend",
            "software_engineering",
            "full_stack",
            "ai_ml",
            "data",
            "devops_cloud",
        },
        "frontend": {
            "frontend",
            "software_engineering",
            "full_stack",
        },
        "full_stack": {
            "full_stack",
            "software_engineering",
            "backend",
            "frontend",
        },
        "ai_ml": {
            "ai_ml",
            "software_engineering",
            "data",
            "backend",
            "full_stack",
        },
        "data": {
            "data",
            "ai_ml",
            "software_engineering",
            "backend",
        },
        "devops_cloud": {
            "devops_cloud",
            "software_engineering",
            "backend",
        },
    }

    if job_family in compatibility.get(resume_family, set()):
        return 85.0

    if resume_domain and job_domain and resume_domain == job_domain:
        return 65.0

    return 0.0


def _experience_rank(value: Optional[str]) -> int:
    value = _normalize(value)

    if not value:
        return 0

    if any(term in value for term in ["intern", "fresher", "entry", "graduate", "junior"]):
        return 0

    if "mid" in value or "associate" in value:
        return 1

    if any(term in value for term in ["senior", "lead", "principal", "staff", "manager"]):
        return 2

    return 1


def _extract_years(value: Optional[str]) -> Optional[float]:
    if not value:
        return None

    text = _normalize(value)

    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text)

    if not matches:
        return None

    try:
        return float(matches[0])
    except ValueError:
        return None


def _experience_score(
    resume_experience_level: Optional[str],
    job_experience_level: Optional[str],
) -> float:
    resume = _normalize(resume_experience_level)
    job = _normalize(job_experience_level)

    if not job:
        return 100.0

    resume_rank = _experience_rank(resume)
    job_rank = _experience_rank(job)

    if resume_rank >= job_rank:
        return 100.0

    if job_rank == resume_rank + 1:
        return 65.0

    return 25.0


def _freshness_score(posted_at: Optional[Any]) -> float:
    if not posted_at:
        return 50.0

    try:
        if isinstance(posted_at, datetime):
            date_value = posted_at
        else:
            text = str(posted_at).replace("Z", "+00:00")
            date_value = datetime.fromisoformat(text)

        if date_value.tzinfo is None:
            date_value = date_value.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_days = max(0, (now - date_value).total_seconds() / 86400)

    except Exception:
        return 50.0

    if age_days <= 3:
        return 100.0

    if age_days <= 7:
        return 95.0

    if age_days <= 14:
        return 90.0

    if age_days <= 30:
        return 75.0

    return 50.0


def _semantic_score(value: Any) -> float:
    try:
        similarity = float(value or 0)
    except (TypeError, ValueError):
        similarity = 0.0

    if similarity <= 1:
        similarity *= 100

    return max(0.0, min(100.0, similarity))


def _build_reasons(
    role_score: float,
    required_score: float,
    semantic_score: float,
    experience_score: float,
    preferred_score: float,
    freshness_score: float,
    matched_required: List[str],
    missing_required: List[str],
) -> List[str]:
    reasons = []

    if role_score >= 90:
        reasons.append("Your career profile closely matches this role.")
    elif role_score >= 70:
        reasons.append("Your career profile is compatible with this role.")

    if required_score >= 80:
        reasons.append("Most required skills are already present in your resume.")
    elif required_score >= 50:
        reasons.append("Your resume covers several of the required skills.")

    if semantic_score >= 80:
        reasons.append("The job description is strongly aligned with your resume.")
    elif semantic_score >= 65:
        reasons.append("The job description has meaningful overlap with your resume.")

    if experience_score >= 90:
        reasons.append("Your experience level aligns with the role.")

    if preferred_score >= 70:
        reasons.append("You also match several preferred skills.")

    if freshness_score >= 95:
        reasons.append("This is a recently posted opportunity.")

    if missing_required:
        reasons.append(
            f"{len(missing_required)} required skill(s) are not currently detected in your resume."
        )

    if not reasons:
        reasons.append("The recommendation is based on your resume and job requirements.")

    return reasons[:5]


def calculate_job_match(
    *,
    semantic_similarity: float,
    resume_skills: Optional[List[Any]] = None,
    job_skills: Optional[List[Any]] = None,
    resume_text: str = "",
    job_title: str = "",
    resume_family: Optional[str] = None,
    job_family: Optional[str] = None,
    resume_domain: Optional[str] = None,
    job_domain: Optional[str] = None,
    required_skills: Optional[List[Any]] = None,
    preferred_skills: Optional[List[Any]] = None,
    resume_experience_level: Optional[str] = None,
    job_experience_level: Optional[str] = None,
    posted_at: Optional[Any] = None,
) -> Dict[str, Any]:
    resume_skill_list = _filter_known_skills(resume_skills)

    required = _filter_known_skills(required_skills)

    preferred = _filter_known_skills(preferred_skills)

    all_job_skills = _filter_known_skills(job_skills)

    if not required:
        required = all_job_skills

    resume_set = set(resume_skill_list)

    matched_required = [
        skill for skill in required
        if skill in resume_set
    ]

    missing_required = [
        skill for skill in required
        if skill not in resume_set
    ]

    matched_preferred = [
        skill for skill in preferred
        if skill in resume_set
    ]

    missing_preferred = [
        skill for skill in preferred
        if skill not in resume_set
    ]

    required_score = (
        (len(matched_required) / len(required)) * 100
        if required
        else 100.0
    )

    preferred_score = (
        (len(matched_preferred) / len(preferred)) * 100
        if preferred
        else 100.0
    )

    role_score = _role_score(
        resume_family=resume_family,
        job_family=job_family,
        resume_domain=resume_domain,
        job_domain=job_domain,
    )

    semantic_score = _semantic_score(semantic_similarity)

    experience_score = _experience_score(
        resume_experience_level=resume_experience_level,
        job_experience_level=job_experience_level,
    )

    freshness_score = _freshness_score(posted_at)

    match_score = (
        role_score * ROLE_WEIGHT
        + required_score * REQUIRED_SKILL_WEIGHT
        + semantic_score * SEMANTIC_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + preferred_score * PREFERRED_SKILL_WEIGHT
        + freshness_score * FRESHNESS_WEIGHT
    )

    match_score = max(0.0, min(100.0, match_score))

    matched_skills = sorted(
        set(matched_required + matched_preferred)
    )

    missing_skills = sorted(
        set(missing_required + missing_preferred)
    )

    reasons = _build_reasons(
        role_score=role_score,
        required_score=required_score,
        semantic_score=semantic_score,
        experience_score=experience_score,
        preferred_score=preferred_score,
        freshness_score=freshness_score,
        matched_required=matched_required,
        missing_required=missing_required,
    )

    return {
        "matcher_version": MATCHER_VERSION,
        "match_score": round(match_score, 1),
        "role_score": round(role_score, 1),
        "required_skill_score": round(required_score, 1),
        "semantic_score": round(semantic_score, 1),
        "experience_score": round(experience_score, 1),
        "preferred_skill_score": round(preferred_score, 1),
        "freshness_score": round(freshness_score, 1),
        "matched_skills": matched_skills,
        "missing_required_skills": sorted(missing_required),
        "missing_preferred_skills": sorted(missing_preferred),
        "missing_skills": missing_skills,
        "match_reasons": reasons,
    }