from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)

from backend.core.config import (
    LLM_CREDENTIAL_ENCRYPTION_KEY,
)


logger = logging.getLogger(
    "smarthire.llm.credentials"
)


SUPPORTED_BYOK_PROVIDERS = {
    "groq",
    "openai",
    "anthropic",
    "google",
}


# ============================================================
# ENCRYPTION
# ============================================================

def _get_fernet() -> Fernet:

    key = (
        LLM_CREDENTIAL_ENCRYPTION_KEY
        or ""
    ).strip()

    if not key:

        raise RuntimeError(
            "LLM_CREDENTIAL_ENCRYPTION_KEY "
            "is not configured."
        )

    try:

        return Fernet(
            key.encode()
        )

    except Exception as exc:

        raise RuntimeError(
            "Invalid LLM credential encryption key."
        ) from exc


def encrypt_api_key(
    api_key: str,
) -> str:

    api_key = (
        api_key or ""
    ).strip()

    if not api_key:

        raise ValueError(
            "API key cannot be empty."
        )

    fernet = _get_fernet()

    encrypted = fernet.encrypt(
        api_key.encode()
    )

    return encrypted.decode()


def decrypt_api_key(
    encrypted_api_key: str,
) -> str:

    encrypted_api_key = (
        encrypted_api_key or ""
    ).strip()

    if not encrypted_api_key:

        raise ValueError(
            "Encrypted API key is empty."
        )

    fernet = _get_fernet()

    try:

        decrypted = fernet.decrypt(
            encrypted_api_key.encode()
        )

        return decrypted.decode()

    except InvalidToken as exc:

        raise RuntimeError(
            "Could not decrypt stored API key."
        ) from exc


# ============================================================
# VALIDATION
# ============================================================

def validate_provider(
    provider: str,
) -> str:

    normalized = (
        provider or ""
    ).strip().lower()

    if normalized not in SUPPORTED_BYOK_PROVIDERS:

        raise ValueError(
            (
                "Unsupported LLM provider. "
                "Supported providers: "
                "Groq, OpenAI, Anthropic, Google."
            )
        )

    return normalized


def mask_api_key(
    api_key: str,
) -> str:

    api_key = (
        api_key or ""
    ).strip()

    if len(api_key) <= 4:

        return "••••"

    return (
        "••••••••"
        + api_key[-4:]
    )


def get_last4(
    api_key: str,
) -> str:

    api_key = (
        api_key or ""
    ).strip()

    return (
        api_key[-4:]
        if len(api_key) >= 4
        else api_key
    )

async def validate_api_key(
    provider: str,
    api_key: str,
    model: str | None = None,
) -> tuple[bool, str]:
    provider = validate_provider(provider)
    api_key = (api_key or "").strip()

    if not api_key:
        return False, "API key cannot be empty."

    timeout = httpx.Timeout(connect=10, read=20, write=20, pool=10)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider == "openai":
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"limit": "1"},
                )
            elif provider == "groq":
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            elif provider == "anthropic":
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
            elif provider == "google":
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    headers={"x-goog-api-key": api_key},
                    params={"pageSize": "1"},
                )
            else:
                return False, "Unsupported provider."
    except httpx.TimeoutException:
        return False, "The provider did not respond in time. Please try again."
    except httpx.RequestError:
        return False, "Could not reach the AI provider. Please try again."

    if response.status_code in {401, 403}:
        return False, "The API key is invalid or unauthorized."

    if response.status_code == 429:
        return False, "The API key is valid, but the provider rate limit was reached."

    if response.status_code >= 400:
        return False, "The API key could not be verified with this provider."

    try:
        payload = response.json()
    except ValueError:
        return False, "The provider returned an invalid validation response."

    if provider == "google" and not payload.get("models"):
        return False, "The API key did not return any available Gemini models."

    if provider in {"openai", "groq", "anthropic"} and not payload.get("data"):
        return False, "The API key did not return any available models."

    return True, "API key verified successfully."
