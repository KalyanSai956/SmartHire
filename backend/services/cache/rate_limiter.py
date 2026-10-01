from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.core.config import REDIS_ENABLED

logger = logging.getLogger("smarthire.rate_limiter")


_RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""


async def enforce_rate_limit(
    redis: Optional[Redis],
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    """
    Apply a distributed fixed-window rate limit.

    Redis is required for accurate limits across multiple
    FastAPI/Kubernetes pods.
    """

    if not REDIS_ENABLED:
        return

    if redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "RATE_LIMIT_SERVICE_UNAVAILABLE",
                "message": (
                    "Rate limiting service is temporarily "
                    "unavailable. Please try again shortly."
                ),
            },
        )

    try:
        result = await redis.eval(
            _RATE_LIMIT_SCRIPT,
            1,
            key,
            str(window_seconds),
        )

        current = int(result[0])
        ttl = max(int(result[1]), 1)

    except RedisError as exc:
        logger.error(
            "Redis rate limiter failed: %s",
            exc,
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "RATE_LIMIT_SERVICE_UNAVAILABLE",
                "message": (
                    "Request protection is temporarily "
                    "unavailable. Please try again shortly."
                ),
            },
        ) from exc

    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": (
                    "Too many requests. "
                    "Please try again shortly."
                ),
                "retry_after": ttl,
            },
            headers={
                "Retry-After": str(ttl),
            },
        )