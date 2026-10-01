from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class JobClassification:
    """
    Structured classification of a job posting.

    This object contains only deterministic classification data.
    """

    domain: str
    family: str
    category: str

    experience_level: str

    required_skills: list[str] = field(
        default_factory=list
    )

    preferred_skills: list[str] = field(
        default_factory=list
    )

    role_signals: list[str] = field(
        default_factory=list
    )

    confidence: float = 0.0

    classification_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "family": self.family,
            "category": self.category,
            "experience_level": self.experience_level,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "role_signals": self.role_signals,
            "confidence": self.confidence,
            "classification_version": (
                self.classification_version
            ),
        }