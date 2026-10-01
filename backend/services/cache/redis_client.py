from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.core.config import (
    REDIS_CONNECT_TIMEOUT,
    REDIS_ENABLED,
    REDIS_REQUIRED,
    REDIS_URL,
)

logger = logging.getLogger("smarthire.redis")


async def create_redis_client() -> Optional[Redis]:
    """
    Create and verify the shared Redis connection.

    Redis is an infrastructure dependency for caching and
    distributed rate limiting.

    When REDIS_REQUIRED=false, the application can still start
    without Redis. Cache operations will simply behave as misses.

    When REDIS_REQUIRED=true, startup fails if Redis cannot be
    reached.
    """

    if not REDIS_ENABLED:
        logger.info("Redis is disabled by configuration.")
        return None

    client = Redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        socket_timeout=REDIS_CONNECT_TIMEOUT,
        health_check_interval=30,
    )

    try:
        await client.ping()

        logger.info(
            "Redis connection established: %s",
            REDIS_URL.split("@")[-1],
        )

        return client

    except RedisError as exc:
        logger.warning(
            "Redis is unavailable: %s",
            exc,
        )

        try:
            await client.aclose()
        except Exception:
            pass

        if REDIS_REQUIRED:
            raise RuntimeError(
                "Redis is required but unavailable."
            ) from exc

        return None


async def close_redis_client(
    client: Optional[Redis],
) -> None:
    """
    Close the Redis connection during application shutdown.
    """

    if client is None:
        return

    try:
        await client.aclose()
        logger.info("Redis connection closed.")

    except Exception:
        logger.exception(
            "Failed to close Redis connection cleanly."
        )