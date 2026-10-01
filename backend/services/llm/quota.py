from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from backend.core.config import (
    PLATFORM_AI_TOKEN_LIMIT,
)

from backend.database.supabase_db import (
    count_user_resume_analyses,
    get_user_llm_credentials,
    get_user_platform_token_usage,
)


logger = logging.getLogger(
    "smarthire.llm.quota"
)


# ============================================================
# FREE QUOTA CONFIGURATION
# ============================================================

FREE_RESUME_ANALYSES = 3

PLATFORM_TOKEN_LIMIT = (
    PLATFORM_AI_TOKEN_LIMIT
)


QuotaFeature = Literal[
    "resume_analysis",
]


# ============================================================
# EXCEPTION
# ============================================================

class FreeQuotaExceededError(Exception):

    def __init__(
        self,
        *,
        feature: QuotaFeature,
        used: int,
        limit: int,
    ):
        self.feature = feature
        self.used = used
        self.limit = limit

        super().__init__(
            f"Free {feature} quota exhausted."
        )


# ============================================================
# RESULT
# ============================================================

@dataclass
class QuotaStatus:

    feature: QuotaFeature
    used: int
    limit: int

    @property
    def remaining(self) -> int:

        return max(
            self.limit - self.used,
            0,
        )

    @property
    def exhausted(self) -> bool:

        return self.used >= self.limit

    def to_dict(self) -> dict:

        return {
            "feature": self.feature,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "exhausted": self.exhausted,
        }


# ============================================================
# TOKEN QUOTA
# ============================================================

@dataclass
class TokenQuotaStatus:

    used: int
    limit: int

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def remaining(self) -> int:

        return max(
            self.limit - self.used,
            0,
        )

    @property
    def exhausted(self) -> bool:

        return self.used >= self.limit

    def to_dict(self) -> dict:

        return {
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "exhausted": self.exhausted,
        }


# ============================================================
# BYOK
# ============================================================

async def user_has_byok(
    user_id: str,
) -> bool:

    credentials = await get_user_llm_credentials(
        user_id
    )

    return bool(credentials)


# ============================================================
# RESUME QUOTA
# ============================================================

async def get_quota_status(
    user_id: str,
    feature: QuotaFeature,
) -> QuotaStatus:

    if feature == "resume_analysis":

        used = await count_user_resume_analyses(
            user_id
        )

        limit = FREE_RESUME_ANALYSES

    else:

        raise ValueError(
            f"Unsupported quota feature: {feature}"
        )

    return QuotaStatus(
        feature=feature,
        used=used,
        limit=limit,
    )


# ============================================================
# PLATFORM TOKEN QUOTA
# ============================================================

async def get_token_quota_status(
    user_id: str,
) -> TokenQuotaStatus:

    usage = await get_user_platform_token_usage(
        user_id
    )

    return TokenQuotaStatus(
        used=usage["total_tokens"],
        limit=PLATFORM_TOKEN_LIMIT,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
    )


# ============================================================
# REQUIRE FREE QUOTA
# ============================================================

async def require_free_quota(
    user_id: str,
    feature: QuotaFeature,
) -> QuotaStatus:

    quota = await get_quota_status(
        user_id=user_id,
        feature=feature,
    )

    logger.info(
        "Quota check user=%s feature=%s "
        "used=%s limit=%s remaining=%s",
        user_id,
        feature,
        quota.used,
        quota.limit,
        quota.remaining,
    )

    if quota.exhausted:

        raise FreeQuotaExceededError(
            feature=feature,
            used=quota.used,
            limit=quota.limit,
        )

    return quota


# ============================================================
# REQUIRE FREE QUOTA OR BYOK
# ============================================================

async def require_free_quota_or_byok(
    user_id: str,
    feature: QuotaFeature,
) -> QuotaStatus:

    if await user_has_byok(user_id):

        logger.info(
            "BYOK detected for user=%s feature=%s; "
            "free quota does not block request.",
            user_id,
            feature,
        )

        return await get_quota_status(
            user_id=user_id,
            feature=feature,
        )

    return await require_free_quota(
        user_id=user_id,
        feature=feature,
    )