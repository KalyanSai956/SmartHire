from fastapi import APIRouter, Depends

from backend.api.auth import get_current_user

from backend.database.supabase_db import (
    get_user_llm_credentials,
    get_user_platform_token_usage,
    get_user_byok_token_usage,
)

from backend.services.llm.quota import (
    get_quota_status,
    get_token_quota_status,
)


router = APIRouter(
    prefix="/api/v1/usage",
    tags=["Usage"],
)


@router.get("/quota")
async def get_usage_quota(
    user_id: str = Depends(get_current_user),
):

    resume_quota = await get_quota_status(
        user_id=user_id,
        feature="resume_analysis",
    )

    token_quota = await get_token_quota_status(
        user_id=user_id,
    )

    credentials = await get_user_llm_credentials(
        user_id=user_id,
    )

    connected_providers = [
        {
            "provider": item["provider"],
            "model": item.get("model"),
            "key_last4": item.get("key_last4"),
        }
        for item in credentials
    ]

    byok_usage = await get_user_byok_token_usage(
        user_id
    )

    return {
        "resume": {
            "used": resume_quota.used,
            "limit": resume_quota.limit,
            "remaining": resume_quota.remaining,
            "exhausted": resume_quota.exhausted,
        },

        "tokens": {
            "used": token_quota.used,
            "limit": token_quota.limit,
            "remaining": token_quota.remaining,
            "input_tokens": token_quota.input_tokens,
            "output_tokens": token_quota.output_tokens,
            "exhausted": token_quota.exhausted,
        },

        "byok": {
            "connected": (
                len(connected_providers) > 0
            ),
            "providers": connected_providers,

            "usage": {
                "input_tokens": byok_usage[
                    "input_tokens"
                ],
                "output_tokens": byok_usage[
                    "output_tokens"
                ],
                "total_tokens": byok_usage[
                    "total_tokens"
                ],
            },
        },
    }