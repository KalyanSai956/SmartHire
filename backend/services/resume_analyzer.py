import logging
import spacy

from backend.services.embedder import FastEmbedder as SentenceTransformer  # ONNX replacement, same .encode() API
from typing import Dict, List, Optional

from backend.services.groq_parser import (
    parse_resume,
    parse_job_description,
)

from backend.services.jd_matcher import compare_resume_with_jd

from backend.services.feedback_engine import (
    analyze_issues,
    generate_issues_summary,
)

from backend.services.ats_scorer import (
    calculate_overall_score,
    validate_skills_with_projects,
)



async def analyze_full_resume(
    resume_text: str,
    nlp: spacy.Language,
    embedder: SentenceTransformer,
    job_description: Optional[str] = None,
    *,
    user_id: str,
    provider: Optional[str] = None,
) -> Dict:

    logger = logging.getLogger("ats_resume_scorer")

    # ------------------------------------------------------------------
    # 1. Parse resume
    # ------------------------------------------------------------------

    parsed_resume = await parse_resume(
        resume_text,
        user_id=user_id,
        provider=provider,
    )

    logger.info(
        "Groq parsed summary: %s",
        parsed_resume.get(
            "professional_summary",
            "",
        )[:100],
    )

    logger.info(
        "Groq parsed skills count: %s",
        len(
            parsed_resume.get(
                "skills",
                [],
            )
        ),
    )

    logger.info(
        "Groq parsed experience count: %s",
        len(
            parsed_resume.get(
                "experience",
                [],
            )
        ),
    )

    # ------------------------------------------------------------------
    # 2. Extract structured data
    # ------------------------------------------------------------------

    skills = parsed_resume.get(
        "skills",
        [],
    )

    projects = parsed_resume.get(
        "projects",
        [],
    )

    keywords = parsed_resume.get(
        "keywords",
        [],
    )

    action_verbs = parsed_resume.get(
        "action_verbs",
        [],
    )

    experience_months = sum(
        int(
            e.get(
                "duration_months",
                0,
            )
        )
        for e in parsed_resume.get(
            "experience",
            [],
        )
        if isinstance(e, dict)
    )

    # ------------------------------------------------------------------
    # 3. Contact information
    # ------------------------------------------------------------------

    contact_info = {
        "email": parsed_resume.get("email"),
        "phone": parsed_resume.get("phone"),
        "linkedin": parsed_resume.get("linkedin"),
        "github": parsed_resume.get("github"),
        "portfolio": None,
    }

    # ------------------------------------------------------------------
    # 4. Validate skills
    # ------------------------------------------------------------------

    skill_validation = validate_skills_with_projects(
        skills=skills,
        projects=projects,
        experience_entries=parsed_resume.get(
            "experience",
            [],
        ),
        embedder=embedder,
    )

    # ------------------------------------------------------------------
    # 5. JD comparison
    # ------------------------------------------------------------------

    jd_comparison_result = None
    jd_keywords = None

    if job_description and job_description.strip():

        cleaned_jd = job_description.strip()

        parsed_jd = await parse_job_description(
            cleaned_jd,
            user_id=user_id,
            provider=provider,
        )

        jd_keywords = list(
            set(
                parsed_jd.get("keywords", [])
                + parsed_jd.get("required_skills", [])
                + parsed_jd.get("preferred_skills", [])
            )
        )

        jd_comparison_result = compare_resume_with_jd(
            resume_text=resume_text,
            resume_keywords=keywords,
            resume_skills=skills,
            jd_text=cleaned_jd,
            jd_keywords=jd_keywords,
            embedder=embedder,
            nlp=nlp,
        )

    # ------------------------------------------------------------------
    # 7. Location/privacy analysis
    # ------------------------------------------------------------------

    from backend.utils.file_utils import (
        get_default_location_results,
    )

    location_results = (
        get_default_location_results()
    )

    # ------------------------------------------------------------------
    # 8. Calculate ATS score
    # ------------------------------------------------------------------

    scores = calculate_overall_score(
    text=resume_text,
    parsed_resume=parsed_resume,
    skills=skills,
    keywords=keywords,
    action_verbs=action_verbs,
    skill_validation_results=skill_validation,
    location_results=location_results,
    jd_keywords=jd_keywords,
    experience_months=experience_months,
)

    # ------------------------------------------------------------------
    # 9. Detailed feedback
    # ------------------------------------------------------------------

    detailed_feedback = analyze_issues(
        resume_text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        projects=projects,
        action_verbs=action_verbs,
        skill_validation=skill_validation,
        scores=scores,
        contact_info=contact_info,
    )

    issues_summary = generate_issues_summary(
        detailed_feedback
    )

    # ------------------------------------------------------------------
    # 10. Skill validation details
    # ------------------------------------------------------------------

    validated_raw = skill_validation.get(
        "validated_skills",
        [],
    )

    unvalidated_raw = skill_validation.get(
        "unvalidated_skills",
        [],
    )

    total_skills = (
        len(validated_raw)
        + len(unvalidated_raw)
    )

    val_pct = round(
        (
            len(validated_raw)
            / total_skills
            * 100
        )
        if total_skills > 0
        else 0,
        1,
    )

    skill_validation_details = {
        "validated": [
            {
                "skill": item["skill"],
                "projects": item.get(
                    "projects",
                    [],
                ),
            }
            for item in validated_raw
        ],

        "unvalidated": unvalidated_raw,

        "total": total_skills,

        "validated_count": len(
            validated_raw
        ),

        "validated_percentage": val_pct,

        "validation_pct": val_pct,
    }

    # ------------------------------------------------------------------
    # 11. Return complete analysis
    # ------------------------------------------------------------------

    return {
        "ATS_score": scores[
            "overall_score"
        ],

        "ats_score": scores[
            "overall_score"
        ],

        "component_scores": {
            "formatting": scores[
                "formatting_score"
            ],

            "keywords": scores[
                "keywords_score"
            ],

            "content": scores[
                "content_score"
            ],

            "skill_validation": scores[
                "skill_validation_score"
            ],

            "ats_compatibility": scores[
                "ats_compatibility_score"
            ],
        },

        # --------------------------------------------------------------
        # Existing feedback
        # --------------------------------------------------------------

        "issues_summary": issues_summary,

        "detailed_feedback": detailed_feedback,

        # --------------------------------------------------------------
        # JD matching
        # --------------------------------------------------------------

        "jd_match_analysis": (
            jd_comparison_result
        ),

        "jd_comparison": (
            jd_comparison_result
        ),

        # --------------------------------------------------------------
        # Skills / keywords
        # --------------------------------------------------------------

        "skills": skills,

        "matched_keywords": (
            jd_comparison_result[
                "matched_keywords"
            ]
            if jd_comparison_result
            else list(
                keywords[:20]
            )
        ),

        "missing_keywords": (
            jd_comparison_result[
                "missing_keywords"
            ]
            if jd_comparison_result
            else []
        ),

        # --------------------------------------------------------------
        # Strengths
        # --------------------------------------------------------------

        "strengths": _generate_strengths(
    parsed_resume,
    skills,
    projects,
    action_verbs,
    skill_validation,
    scores,
),

        "interpretation": scores.get(
            "overall_interpretation",
            "",
        ),

        # --------------------------------------------------------------
        # Skill validation
        # --------------------------------------------------------------

        "skill_validation_details": (
            skill_validation_details
        ),

        "experience_months": (
            experience_months
        ),
    }


def _generate_strengths(
    parsed_resume: Dict,
    skills: List,
    projects: List,
    action_verbs: List,
    skill_validation: Dict,
    scores: Dict,
) -> List[str]:

    """Generate strengths based on actual resume analysis."""

    strengths = []

    if parsed_resume.get(
        "experience"
    ):
        strengths.append(
            "Has a dedicated Experience section"
        )

    if (
        parsed_resume.get("projects")
        or len(projects) > 0
    ):
        strengths.append(
            "Includes a Projects section showcasing applied skills"
        )

    if parsed_resume.get(
        "education"
    ):
        strengths.append(
            "Education section is present"
        )

    if parsed_resume.get(
        "skills"
    ):
        strengths.append(
            "Clear Skills section with listed technologies"
        )

    if parsed_resume.get(
        "professional_summary",
        "",
    ).strip():

        strengths.append(
            "Professional Summary provides a quick overview"
        )

    if len(skills) >= 8:
        strengths.append(
            f"Strong skill set — {len(skills)} skills detected"
        )

    if len(action_verbs) >= 5:
        strengths.append(
            f"Uses {len(action_verbs)} strong action verbs in bullet points"
        )

    validated = skill_validation.get(
        "validated_skills",
        [],
    )

    if len(validated) >= 3:
        strengths.append(
            f"{len(validated)} skills are backed by project/experience evidence"
        )

    if scores.get(
        "formatting_score",
        0,
    ) >= 16:

        strengths.append(
            "Well-formatted and ATS-friendly structure"
        )

    if scores.get(
        "content_score",
        0,
    ) >= 20:

        strengths.append(
            "Content quality is high with measurable achievements"
        )

    return strengths