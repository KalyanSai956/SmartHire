from __future__ import annotations

from typing import Any


def classify_source_status(
    *,
    enabled: bool,
    provider: str,
    last_error: str | None,
) -> str:

    if not enabled:
        return "paused"

    if last_error:
        return "error"

    if provider in {
        "lever",
        "greenhouse",
    }:
        return "active"

    return "pending"