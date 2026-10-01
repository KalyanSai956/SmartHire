import json
import logging
from typing import Dict

from backend.services.llm.base import (
    LLMProviderResponseError,
)
from backend.services.llm.user_gateway import (
    create_user_llm_gateway,
)


logger = logging.getLogger(
    "ats-resume-scorer"
)


# ============================================================
# PROMPTS
# ============================================================

RESUME_SYSTEM_PROMPT = (
    "You are a resume parser. "
    "Extract information from the resume "
    "and return ONLY a valid JSON object. "
    "No explanation, no markdown."
)


RESUME_USER_PROMPT = """Extract the following from this resume and return as JSON:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "linkedin": "LinkedIn URL if present, otherwise null",
  "github": "GitHub URL if present, otherwise null",
  "professional_summary": "the full text of the Summary, Profile, About Me, Objective, or Professional Summary section at the top of the resume. Copy the ENTIRE paragraph exactly as written. If no such section exists, return an empty string.",
  "skills": ["list", "of", "skills"],
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "duration_months": 0,
      "description": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "year": ""
    }}
  ],
  "certifications": ["list of certifications"],
  "projects": [
    {{
      "title": "project name",
      "description": "what the project does and how it was built",
      "technologies": ["tech", "used"]
    }}
  ],
  "action_verbs": ["strong action verbs used in bullet points, e.g. developed, implemented, designed"],
  "keywords": ["important keywords and phrases from the resume for ATS matching"]
}}

Important instructions:
- For duration_months, calculate the number of months between start_date and end_date. If end_date is "Present" or "Current", calculate from start_date to now.
- For skills, extract ALL technical and soft skills mentioned anywhere in the resume.
- For action_verbs, find verbs that start bullet points or describe achievements.
- For keywords, extract noun phrases and technical terms relevant to ATS matching.
- Return ONLY valid JSON.
- Do not use markdown code fences.
- Do not include any explanation.

Resume Text:
{raw_text}
"""


JD_SYSTEM_PROMPT = (
    "You are a job description parser. "
    "Extract information and return ONLY a valid JSON object. "
    "No explanation, no markdown."
)


JD_USER_PROMPT = """Extract the following from this job description and return as JSON:
{{
  "job_title": "",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "experience_required": "",
  "education_required": "",
  "key_responsibilities": ["list of responsibilities"],
  "keywords": ["important keywords and phrases for ATS matching"]
}}

Important instructions:
- required_skills: skills explicitly stated as required or must-have.
- preferred_skills: skills stated as preferred, nice-to-have, or bonus.
- keywords: extract ALL important terms an ATS system would match against,
  including skills, technologies, certifications, and domain terms.
- Return ONLY valid JSON.
- Do not use markdown code fences.
- Do not include any explanation.

Job Description Text:
{raw_text}
"""


# ============================================================
# RESUME PARSER
# ============================================================

async def parse_resume(
    raw_text: str,
    *,
    user_id: str,
    provider: str | None = None,
) -> Dict:
    """
    Parse a resume using the user's selected BYOK provider
    when available, otherwise fall back to SmartHire's
    platform provider.

    Usage is automatically recorded by LLMGateway.
    """

    gateway = await create_user_llm_gateway(
        user_id=user_id,
        feature="resume_parsing",
        provider=provider,
    )

    prompt = RESUME_USER_PROMPT.format(
        raw_text=raw_text
    )

    try:

        response = await gateway.generate_json(
            [
                {
                    "role": "system",
                    "content": RESUME_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.0,
            max_tokens=4096,
        )

        result = response.parsed_json

        if not isinstance(result, dict):
            raise LLMProviderResponseError(
                "Resume parser returned invalid JSON."
            )

        return _validate_resume_result(
            result
        )

    except Exception as exc:

        logger.warning(
            "Resume parser first attempt failed; "
            "retrying with strict JSON prompt. "
            "error=%s",
            exc,
        )

        strict_prompt = (
            "Your previous response was not valid JSON.\n\n"
            "Return ONLY the raw JSON object.\n"
            "No markdown.\n"
            "No code fences.\n"
            "No explanation.\n\n"
            + prompt
        )

        response = await gateway.generate_json(
            [
                {
                    "role": "system",
                    "content": RESUME_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": strict_prompt,
                },
            ],
            temperature=0.0,
            max_tokens=4096,
        )

        result = response.parsed_json

        if not isinstance(result, dict):
            raise ValueError(
                "LLM returned invalid resume JSON."
            )

        return _validate_resume_result(
            result
        )


# ============================================================
# JOB DESCRIPTION PARSER
# ============================================================

async def parse_job_description(
    raw_text: str,
    *,
    user_id: str,
    provider: str | None = None,
) -> Dict:
    """
    Parse a job description using the same unified
    LLM gateway used by resume analysis.
    """

    gateway = await create_user_llm_gateway(
        user_id=user_id,
        feature="jd_parsing",
        provider=provider,
    )

    prompt = JD_USER_PROMPT.format(
        raw_text=raw_text
    )

    try:

        response = await gateway.generate_json(
            [
                {
                    "role": "system",
                    "content": JD_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.0,
            max_tokens=2500,
        )

        result = response.parsed_json

        if not isinstance(result, dict):
            raise LLMProviderResponseError(
                "Job description parser returned invalid JSON."
            )

        return _validate_jd_result(
            result
        )

    except Exception as exc:

        logger.warning(
            "JD parser first attempt failed; "
            "retrying with strict JSON prompt. "
            "error=%s",
            exc,
        )

        strict_prompt = (
            "Your previous response was not valid JSON.\n\n"
            "Return ONLY the raw JSON object.\n"
            "No markdown.\n"
            "No code fences.\n"
            "No explanation.\n\n"
            + prompt
        )

        response = await gateway.generate_json(
            [
                {
                    "role": "system",
                    "content": JD_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": strict_prompt,
                },
            ],
            temperature=0.0,
            max_tokens=2500,
        )

        result = response.parsed_json

        if not isinstance(result, dict):
            raise ValueError(
                "LLM returned invalid job description JSON."
            )

        return _validate_jd_result(
            result
        )


# ============================================================
# VALIDATE JD RESULT
# ============================================================

def _validate_jd_result(
    result: dict,
) -> dict:

    defaults = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": "",
        "education_required": "",
        "key_responsibilities": [],
        "keywords": [],
    }

    for key, default in defaults.items():

        if (
            key not in result
            or result[key] is None
        ):
            result[key] = default

        if (
            isinstance(default, list)
            and not isinstance(
                result[key],
                list,
            )
        ):
            result[key] = default

    return result


# ============================================================
# VALIDATE RESUME RESULT
# ============================================================

def _validate_resume_result(
    result: dict,
) -> dict:

    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": [],
        "keywords": [],
    }

    for key, default in defaults.items():

        if (
            key not in result
            or result[key] is None
        ):
            result[key] = default

        if (
            isinstance(default, list)
            and not isinstance(
                result[key],
                list,
            )
        ):
            result[key] = default

    # --------------------------------------------------------
    # Validate experience
    # --------------------------------------------------------

    for exp in result.get(
        "experience",
        [],
    ):

        if not isinstance(
            exp,
            dict,
        ):
            continue

        exp.setdefault(
            "job_title",
            "",
        )

        exp.setdefault(
            "company",
            "",
        )

        exp.setdefault(
            "start_date",
            "",
        )

        exp.setdefault(
            "end_date",
            "",
        )

        exp.setdefault(
            "duration_months",
            0,
        )

        exp.setdefault(
            "description",
            "",
        )

        try:

            exp[
                "duration_months"
            ] = int(
                exp[
                    "duration_months"
                ]
            )

        except (
            ValueError,
            TypeError,
        ):

            exp[
                "duration_months"
            ] = 0

    # --------------------------------------------------------
    # Validate projects
    # --------------------------------------------------------

    for proj in result.get(
        "projects",
        [],
    ):

        if not isinstance(
            proj,
            dict,
        ):
            continue

        proj.setdefault(
            "title",
            "",
        )

        proj.setdefault(
            "description",
            "",
        )

        proj.setdefault(
            "technologies",
            [],
        )

        if not isinstance(
            proj["technologies"],
            list,
        ):
            proj["technologies"] = []

    return result