from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from backend.services.jobs.role_taxonomy import (
    BACKEND,
    DATA,
    DEVOPS_CLOUD,
    FRONTEND,
    FULL_STACK,
    AI_ML,
    SOFTWARE_ENGINEERING,
    TECHNOLOGY,
    UNKNOWN,
    TECH_FAMILIES,
    RoleClassification,
    classify_role,
    classify_resume,
)


# ============================================================
# GATE RESULT
# ============================================================

@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str
    resume_classification: RoleClassification
    job_classification: RoleClassification


# ============================================================
# FAMILY COMPATIBILITY
# ============================================================

# Closely related technology families.
TECH_FAMILY_COMPATIBILITY: dict[str, set[str]] = {
    BACKEND: {
        BACKEND,
        SOFTWARE_ENGINEERING,
        FULL_STACK,
        AI_ML,
        DATA,
        DEVOPS_CLOUD,
    },

    FRONTEND: {
        FRONTEND,
        SOFTWARE_ENGINEERING,
        FULL_STACK,
    },

    FULL_STACK: {
        FULL_STACK,
        SOFTWARE_ENGINEERING,
        BACKEND,
        FRONTEND,
    },

    AI_ML: {
        AI_ML,
        SOFTWARE_ENGINEERING,
        DATA,
        BACKEND,
        FULL_STACK,
    },

    DATA: {
        DATA,
        AI_ML,
        SOFTWARE_ENGINEERING,
        BACKEND,
    },

    DEVOPS_CLOUD: {
        DEVOPS_CLOUD,
        SOFTWARE_ENGINEERING,
        BACKEND,
    },

    SOFTWARE_ENGINEERING: {
        SOFTWARE_ENGINEERING,
        BACKEND,
        FRONTEND,
        FULL_STACK,
        AI_ML,
        DATA,
        DEVOPS_CLOUD,
    },
}


def _allowed_tech_families(
    resume_family: str,
) -> set[str]:
    """
    Return related technical families.

    If we don't recognize the specific family but know the resume is
    technical, allow all technical families rather than accidentally
    hiding legitimate engineering jobs.
    """

    if resume_family in TECH_FAMILY_COMPATIBILITY:
        return TECH_FAMILY_COMPATIBILITY[resume_family]

    return TECH_FAMILIES


# ============================================================
# JOB GATE
# ============================================================

def evaluate_job(
    *,
    resume_classification: RoleClassification,
    job_title: str,
    job_description: str = "",
    job_skills: Iterable[str] | None = None,
) -> GateResult:

    job_classification = classify_role(
        title=job_title,
        description=job_description,
        skills=job_skills,
    )

    # --------------------------------------------------------
    # UNKNOWN JOB
    # --------------------------------------------------------

    if job_classification.domain == UNKNOWN:
        return GateResult(
            allowed=False,
            reason="Job role could not be classified safely.",
            resume_classification=resume_classification,
            job_classification=job_classification,
        )

    # --------------------------------------------------------
    # TECHNICAL RESUME
    # --------------------------------------------------------

    if resume_classification.domain == TECHNOLOGY:

        if job_classification.domain != TECHNOLOGY:
            return GateResult(
                allowed=False,
                reason=(
                    "Technical resume cannot be matched to "
                    "a non-technical role."
                ),
                resume_classification=resume_classification,
                job_classification=job_classification,
            )

        allowed_families = _allowed_tech_families(
            resume_classification.family
        )

        if job_classification.family not in allowed_families:
            return GateResult(
                allowed=False,
                reason=(
                    f"Job family '{job_classification.family}' "
                    f"is outside the compatible technical role "
                    f"families for '{resume_classification.family}'."
                ),
                resume_classification=resume_classification,
                job_classification=job_classification,
            )

        return GateResult(
            allowed=True,
            reason="Technical domain and compatible role family.",
            resume_classification=resume_classification,
            job_classification=job_classification,
        )

    # --------------------------------------------------------
    # NON-TECHNICAL RESUME
    # --------------------------------------------------------

    if resume_classification.domain != UNKNOWN:

        if job_classification.domain == TECHNOLOGY:
            return GateResult(
                allowed=False,
                reason=(
                    "Non-technical resume cannot be matched "
                    "to a technical role."
                ),
                resume_classification=resume_classification,
                job_classification=job_classification,
            )

        # Same career family gets through.
        if (
            job_classification.family
            == resume_classification.family
        ):
            return GateResult(
                allowed=True,
                reason="Matching non-technical role family.",
                resume_classification=resume_classification,
                job_classification=job_classification,
            )

        # Same broad non-tech domain can still be useful.
        if (
            job_classification.domain
            == resume_classification.domain
        ):
            return GateResult(
                allowed=True,
                reason="Matching non-technical career domain.",
                resume_classification=resume_classification,
                job_classification=job_classification,
            )

        return GateResult(
            allowed=False,
            reason=(
                f"Job family '{job_classification.family}' "
                f"does not match resume family "
                f"'{resume_classification.family}'."
            ),
            resume_classification=resume_classification,
            job_classification=job_classification,
        )

    # --------------------------------------------------------
    # UNKNOWN RESUME
    # --------------------------------------------------------

    # We fail closed rather than recommending random jobs.
    return GateResult(
        allowed=False,
        reason="Resume career domain could not be classified.",
        resume_classification=resume_classification,
        job_classification=job_classification,
    )


# ============================================================
# BATCH FILTER
# ============================================================

def filter_jobs_for_resume(
    *,
    jobs: list[dict[str, Any]],
    resume_text: str,
    resume_skills: Iterable[str] | None = None,
    target_roles: Iterable[str] | None = None,
) -> tuple[list[dict[str, Any]], RoleClassification, dict[str, int]]:

    resume_classification = classify_resume(
        resume_text=resume_text,
        resume_skills=resume_skills,
        target_roles=target_roles,
    )

    allowed_jobs: list[dict[str, Any]] = []

    statistics = {
        "input": len(jobs),
        "allowed": 0,
        "rejected_domain": 0,
        "rejected_role": 0,
        "rejected_unknown": 0,
    }

    for job in jobs:

        title = job.get("title") or ""
        description = job.get("description") or ""
        skills = job.get("skills") or []

        result = evaluate_job(
            resume_classification=resume_classification,
            job_title=title,
            job_description=description,
            job_skills=skills,
        )

        if result.allowed:
            job_copy = dict(job)

            job_copy["_role_gate"] = {
                "domain": result.job_classification.domain,
                "family": result.job_classification.family,
                "confidence": result.job_classification.confidence,
                "matched_signals": list(
                    result.job_classification.matched_signals
                ),
            }

            allowed_jobs.append(job_copy)
            statistics["allowed"] += 1
            continue

        reason = result.reason.lower()

        if "could not be classified" in reason:
            statistics["rejected_unknown"] += 1
        elif "non-technical" in reason or "technical" in reason:
            statistics["rejected_domain"] += 1
        else:
            statistics["rejected_role"] += 1

    return (
        allowed_jobs,
        resume_classification,
        statistics,
    )