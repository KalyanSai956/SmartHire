from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CareerProfile:
    """
    Structured representation of a candidate's career profile.

    This profile is deterministic and is built from resume content,
    existing role taxonomy classification, and extracted resume data.
    """

    domain: str
    primary_role: str
    role_family: str
    compatible_roles: list[str]

    experience_level: str

    skills: list[str]
    education: list[str]
    projects: list[str]

    target_roles: list[str]

    confidence: float

    matched_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "primary_role": self.primary_role,
            "role_family": self.role_family,
            "compatible_roles": self.compatible_roles,
            "experience_level": self.experience_level,
            "skills": self.skills,
            "education": self.education,
            "projects": self.projects,
            "target_roles": self.target_roles,
            "confidence": self.confidence,
            "matched_signals": self.matched_signals,
        }