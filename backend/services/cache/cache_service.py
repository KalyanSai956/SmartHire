from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger("smarthire.cache")


CACHE_PREFIX = "smarthire:v1"


def build_cache_key(
    namespace: str,
    payload: Any,
) -> str:
    """
    Build a deterministic, bounded Redis key.

    User input is hashed instead of being placed directly
    into Redis keys.
    """

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()

    return (
        f"{CACHE_PREFIX}:"
        f"{namespace}:"
        f"{digest}"
    )


async def get_json(
    redis: Optional[Redis],
    key: str,
) -> Any:
    """
    Return cached JSON data.

    Cache failures are intentionally fail-open:
    if Redis has a problem, the application continues
    and behaves as though the cache missed.
    """

    if redis is None:
        return None

    try:
        value = await redis.get(key)

        if value is None:
            return None

        try:
            return json.loads(value)

        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON found in cache key=%s",
                key,
            )

            await redis.delete(key)

            return None

    except RedisError:
        logger.warning(
            "Redis GET failed for key=%s",
            key,
            exc_info=True,
        )

        return None


async def set_json(
    redis: Optional[Redis],
    key: str,
    value: Any,
    ttl_seconds: int,
) -> bool:
    """
    Store JSON data with an explicit TTL.

    Cache writes are best-effort.
    """

    if redis is None:
        return False

    if ttl_seconds <= 0:
        return False

    try:
        payload = json.dumps(
            value,
            separators=(",", ":"),
            default=str,
        )

        await redis.set(
            key,
            payload,
            ex=ttl_seconds,
        )

        return True

    except (RedisError, TypeError, ValueError):
        logger.warning(
            "Redis SET failed for key=%s",
            key,
            exc_info=True,
        )

        return False


async def delete_key(
    redis: Optional[Redis],
    key: str,
) -> bool:
    """
    Delete a specific cache entry.
    """

    if redis is None:
        return False

    try:
        deleted = await redis.delete(key)
        return bool(deleted)

    except RedisError:
        logger.warning(
            "Redis DELETE failed for key=%s",
            key,
            exc_info=True,
        )

        return False