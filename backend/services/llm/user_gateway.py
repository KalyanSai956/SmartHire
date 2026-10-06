from __future__ import annotations

import logging
from typing import Optional

from backend.database.supabase_db import (
    get_user_llm_credential,
)
from backend.services.llm.credentials import (
    decrypt_api_key,
    validate_api_key,
)
from backend.services.llm.gateway import LLMGateway


logger = logging.getLogger(
    "smarthire.llm.user_gateway"
)


SUPPORTED_PROVIDERS = {
    "groq",
    "openai",
    "anthropic",
    "google",
}


DEFAULT_PROVIDER_PRIORITY = [
    "groq",
    "openai",
    "anthropic",
    "google",
]


async def _get_user_credential(
    *,
    user_id: str,
    provider: str,
):
    """
    Load and decrypt a user's stored BYOK credential.

    Returns:
        (api_key, credential)

    Returns:
        (None, None) if the credential does not exist.
    """

    credential = await get_user_llm_credential(
        user_id=user_id,
        provider=provider,
    )

    if not credential:
        return None, None

    encrypted_key = (
        credential.get("encrypted_api_key")
        or ""
    ).strip()

    if not encrypted_key:
        logger.warning(
            "LLM credential exists without an encrypted "
            "API key. provider=%s user_id=%s",
            provider,
            user_id,
        )
        return None, credential

    try:
        api_key = decrypt_api_key(
            encrypted_key
        )

    except Exception:
        logger.exception(
            "Failed to decrypt LLM credential. "
            "provider=%s user_id=%s",
            provider,
            user_id,
        )

        return None, credential

    if not api_key:
        logger.warning(
            "Decrypted LLM credential is empty. "
            "provider=%s user_id=%s",
            provider,
            user_id,
        )
        return None, credential

    return api_key, credential


async def create_user_llm_gateway(
    *,
    user_id: str,
    feature: str,
    provider: Optional[str] = None,
    usage_source: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMGateway:
    """
    Create an LLM gateway for a user.

    Provider selection:

    1. Explicit provider:
       Use exactly that provider's BYOK credential.

    2. No explicit provider:
       Select the first configured BYOK provider.

    3. No usable BYOK credential:
       Fall back to the platform Groq provider.

    Important:
    - Explicit provider selection is strict.
    - Automatic selection only uses credentials that can
      be successfully decrypted.
    - API keys are NOT logged.
    """

    selected_provider = (
        provider.strip().lower()
        if isinstance(provider, str)
        and provider.strip()
        else None
    )

    # =========================================================
    # EXPLICIT PROVIDER
    # =========================================================

    if selected_provider:

        if selected_provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported LLM provider: "
                f"{selected_provider}"
            )

        api_key, credential = (
            await _get_user_credential(
                user_id=user_id,
                provider=selected_provider,
            )
        )

        if not credential:
            raise ValueError(
                f"No API key is configured for provider "
                f"'{selected_provider}'. "
                f"Please connect it in AI Settings."
            )

        if not api_key:
            raise ValueError(
                f"The stored API key for provider "
                f"'{selected_provider}' could not be loaded. "
                f"Please reconnect the provider in AI Settings."
            )

        selected_model = (
            model
            or credential.get("model")
            or None
        )

        return LLMGateway(
            provider=selected_provider,
            api_key=api_key,
            model=selected_model,
            user_id=user_id,
            feature=feature,
            usage_source=(
                usage_source
                or "byok"
            ),
        )

    # =========================================================
    # AUTOMATIC BYOK SELECTION
    # =========================================================

    for candidate in DEFAULT_PROVIDER_PRIORITY:

        api_key, credential = (
            await _get_user_credential(
                user_id=user_id,
                provider=candidate,
            )
        )

        if not credential:
            continue

        if not api_key:
            logger.warning(
                "Skipping unusable BYOK credential. "
                "provider=%s user_id=%s",
                candidate,
                user_id,
            )
            continue

        selected_model = (
            model
            or credential.get("model")
            or None
        )

        return LLMGateway(
            provider=candidate,
            api_key=api_key,
            model=selected_model,
            user_id=user_id,
            feature=feature,
            usage_source=(
                usage_source
                or "byok"
            ),
        )

    # =========================================================
    # PLATFORM PROVIDER FALLBACK
    # =========================================================

    return LLMGateway(
        provider="groq",
        api_key=None,
        model=model,
        user_id=user_id,
        feature=feature,
        usage_source=(
            usage_source
            or "platform"
        ),
    )