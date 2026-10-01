import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.api.auth import get_current_user
from backend.models.schemas import (
    CareerProfileResponse,
    CareerProfileUpdate,
    OnboardingProgressUpdate,
)
from backend.services.llm.quota import (
    FreeQuotaExceededError,
    require_free_quota,
)
from backend.api.dependencies import (
    profile_resume_rate_limit,
)
logger = logging.getLogger("ats_resume_scorer")

router = APIRouter(
    prefix="/api/v1/profile",
    tags=["Profile"],
)


def _clean_list(values):
    result = []
    seen = set()

    for value in values or []:
        cleaned = str(value).strip()

        if not cleaned:
            continue

        key = cleaned.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return result


def _profile_response(
    user_id: str,
    profile: dict,
) -> CareerProfileResponse:
    return CareerProfileResponse(
        user_id=user_id,
        username=profile.get("username") or "",
        career_interests=profile.get("career_interests") or [],
        specializations=profile.get("specializations") or [],
        skills=profile.get("skills") or [],
        target_roles=profile.get("target_roles") or [],
        experience=profile.get("experience") or "",
        graduation_year=profile.get("graduation_year"),
        resume_filename=profile.get("resume_filename"),
        onboarding_step=int(
    profile.get("onboarding_step", 1)
    or 1
),
onboarding_completed=bool(
    profile.get("onboarding_completed", False)
),
    )


@router.get(
    "",
    response_model=CareerProfileResponse,
)
async def get_profile(
    user_id: str = Depends(get_current_user),
):
    """
    Return the authenticated user's career profile.
    """

    from backend.database.supabase_db import get_user_profile

    profile = await get_user_profile(user_id)

    if profile is None:
       return CareerProfileResponse(
    user_id=user_id,
    username="",
    career_interests=[],
    specializations=[],
    skills=[],
    target_roles=[],
    experience="",
    graduation_year=None,
    resume_filename=None,
    onboarding_step=1,
    onboarding_completed=False,
)

    return _profile_response(
        user_id,
        profile,
    )


@router.put(
    "",
    response_model=CareerProfileResponse,
)
async def update_profile(
    data: CareerProfileUpdate,
    user_id: str = Depends(get_current_user),
):
    """
    Create or update the authenticated user's career profile.
    """

    username = data.username.strip()
    experience = data.experience.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required.",
        )

    if len(username) < 2:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 2 characters.",
        )

    career_interests = _clean_list(
        data.career_interests
    )

    specializations = _clean_list(
        data.specializations
    )

    skills = _clean_list(
        data.skills
    )

    target_roles = _clean_list(
        data.target_roles
    )

    if not career_interests:
        raise HTTPException(
            status_code=400,
            detail="Please add at least one career interest.",
        )

    if not specializations:
        raise HTTPException(
            status_code=400,
            detail="Please add at least one specialization.",
        )

    if not skills:
        raise HTTPException(
            status_code=400,
            detail="Please add at least one skill.",
        )

    if not target_roles:
        raise HTTPException(
            status_code=400,
            detail="Please add at least one target role.",
        )

    if data.graduation_year is not None:
        if (
            data.graduation_year < 1950
            or data.graduation_year > 2100
        ):
            raise HTTPException(
                status_code=400,
                detail="Please enter a valid graduation year.",
            )

    from backend.database.supabase_db import (
        upsert_user_profile,
    )

    profile = await upsert_user_profile(
        user_id=user_id,
        username=username,
        career_interests=career_interests,
        specializations=specializations,
        skills=skills,
        target_roles=target_roles,
        experience=experience,
        graduation_year=data.graduation_year,
        onboarding_completed=False,
    )

    if profile is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save your career profile.",
        )

    return _profile_response(
        user_id,
        profile,
    )
@router.patch(
    "/onboarding-progress",
    response_model=CareerProfileResponse,
)
async def save_onboarding_progress(
    data: OnboardingProgressUpdate,
    user_id: str = Depends(get_current_user),
):
    """
    Save incomplete onboarding progress.

    This endpoint intentionally accepts partial profile data
    because users can leave onboarding before completing it.
    """

    if data.step < 1 or data.step > 7:
        raise HTTPException(
            status_code=400,
            detail="Onboarding step must be between 1 and 7.",
        )

    if data.graduation_year is not None:
        if (
            data.graduation_year < 1950
            or data.graduation_year > 2100
        ):
            raise HTTPException(
                status_code=400,
                detail="Please enter a valid graduation year.",
            )

    if data.username is not None:
        username = data.username.strip()

        if username and len(username) < 2:
            raise HTTPException(
                status_code=400,
                detail="Username must contain at least 2 characters.",
            )

        data.username = username

    from backend.database.supabase_db import (
        save_onboarding_progress as save_progress,
    )

    try:
        profile = await save_progress(
            user_id=user_id,
            step=data.step,
            username=data.username,
            career_interests=data.career_interests,
            specializations=data.specializations,
            skills=data.skills,
            target_roles=data.target_roles,
            experience=data.experience,
            graduation_year=data.graduation_year,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if profile is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save onboarding progress.",
        )

    return _profile_response(
        user_id,
        profile,
    )

@router.post(
    "/resume",
    response_model=CareerProfileResponse,
)
async def upload_profile_resume(
    resume: UploadFile = File(
        ...,
        description="Resume file — PDF or DOCX, max 5 MB",
    ),
    user_id: str = Depends(
    profile_resume_rate_limit
),
):
    """
    Parse and save the user's latest resume.
    """

    filename = resume.filename or "resume"

    allowed_extensions = {
        ".pdf",
        ".docx",
    }

    extension = ""

    if "." in filename:
        extension = (
            "."
            + filename.rsplit(
                ".",
                1,
            )[1].lower()
        )

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX resume files are supported.",
        )

    file_bytes = await resume.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded resume is empty.",
        )

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Resume must be smaller than 5 MB.",
        )

    try:
        from backend.services.resume_parser import (
            parse_resume_file,
        )

        resume_text, _metadata = parse_resume_file(
            file_bytes,
            filename,
        )

    except Exception as exc:
        logger.exception(
            "Profile resume parsing failed"
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not read or parse the resume: "
                f"{exc}"
            ),
        )

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text was found in the resume.",
        )

    from backend.database.supabase_db import (
        update_profile_resume,
    )

    profile = await update_profile_resume(
        user_id=user_id,
        filename=filename,
        resume_text=resume_text,
    )

    if profile is None:
        raise HTTPException(
            status_code=500,
            detail="Could not save the resume.",
        )

    return _profile_response(
        user_id,
        profile,
    )


@router.post(
    "/complete",
    response_model=CareerProfileResponse,
)
async def complete_onboarding(
    user_id: str = Depends(get_current_user),
):
    """
    Mark onboarding as completed.

    A complete career profile and resume must exist.
    """

    from backend.database.supabase_db import (
        get_user_profile,
        mark_onboarding_completed,
    )

    profile = await get_user_profile(user_id)

    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="Career profile has not been created yet.",
        )

    if not profile.get("username"):
        raise HTTPException(
            status_code=400,
            detail="Username is required.",
        )

    if not profile.get("career_interests"):
        raise HTTPException(
            status_code=400,
            detail="At least one career interest is required.",
        )

    if not profile.get("specializations"):
        raise HTTPException(
            status_code=400,
            detail="At least one specialization is required.",
        )

    if not profile.get("skills"):
        raise HTTPException(
            status_code=400,
            detail="At least one skill is required.",
        )

    if not profile.get("target_roles"):
        raise HTTPException(
            status_code=400,
            detail="At least one target role is required.",
        )

    if not profile.get("experience"):
        raise HTTPException(
            status_code=400,
            detail="Experience level is required.",
        )

    if not profile.get("graduation_year"):
        raise HTTPException(
            status_code=400,
            detail="Graduation year is required.",
        )

    if not profile.get("resume_text"):
        raise HTTPException(
            status_code=400,
            detail="Please upload your resume before completing onboarding.",
        )

    updated = await mark_onboarding_completed(
        user_id
    )

    if updated is None:
        raise HTTPException(
            status_code=500,
            detail="Could not complete onboarding.",
        )

    return _profile_response(
        user_id,
        updated,
    )