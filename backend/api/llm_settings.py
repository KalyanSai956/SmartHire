from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.api.dependencies import (
    llm_connect_rate_limit,
)
from backend.api.auth import get_current_user
from backend.database.supabase_db import (
    delete_user_llm_credential,
    get_user_llm_credentials,
    save_user_llm_credential,
    update_user_llm_credential,
)
from backend.services.llm.credentials import (
    SUPPORTED_BYOK_PROVIDERS,
    encrypt_api_key,
    get_last4,
    validate_api_key,
)


router = APIRouter(
    prefix="/api/v1/llm-settings",
    tags=["LLM Settings"],
)


PROVIDER_METADATA = {
    "groq": {
        "name": "Groq",
        "default_model": "openai/gpt-oss-120b",
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "name": "Anthropic",
        "default_model": "claude-haiku-4-5-20251001",
    },
    "google": {
        "name": "Google Gemini",
        "default_model": "gemini-3.6-flash",
    },
}


class ConnectProviderRequest(BaseModel):
    provider: str
    api_key: str = Field(min_length=1)
    model: str | None = None


class SelectProviderRequest(BaseModel):
    provider: str | None = None


def normalize_provider(provider: str) -> str:
    value = provider.strip().lower()

    if value not in SUPPORTED_BYOK_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}",
        )

    return value


@router.get("")
async def get_llm_settings(
    user_id: str = Depends(get_current_user),
):
    credentials = await get_user_llm_credentials(
        user_id=user_id
    )

    credential_map = {
        item["provider"]: item
        for item in credentials
    }

    providers = []

    for provider, metadata in PROVIDER_METADATA.items():

        credential = credential_map.get(provider)

        providers.append(
            {
                "provider": provider,
                "name": metadata["name"],
                "default_model": metadata["default_model"],
                "connected": credential is not None,
                "model": (
                    credential.get("model")
                    if credential
                    else metadata["default_model"]
                ),
                "key_last4": (
                    credential.get("key_last4")
                    if credential
                    else None
                ),
            }
        )

    return {
        "providers": providers
    }


@router.post("/connect")
async def connect_llm_provider(
    payload: ConnectProviderRequest,
    user_id: str = Depends(
    llm_connect_rate_limit
),
):
    provider = normalize_provider(payload.provider)

    api_key = payload.api_key.strip()

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="API key cannot be empty.",
        )

    model = (
        payload.model.strip()
        if payload.model and payload.model.strip()
        else PROVIDER_METADATA[provider]["default_model"]
    )

    valid, validation_message = await validate_api_key(
        provider=provider,
        api_key=api_key,
        model=model,
    )

    if not valid:
        raise HTTPException(
            status_code=422,
            detail=validation_message,
        )

    encrypted_api_key = encrypt_api_key(api_key)

    existing = await get_user_llm_credentials(
        user_id=user_id
    )

    existing_credential = next(
        (
            item
            for item in existing
            if item["provider"] == provider
        ),
        None,
    )

    if existing_credential:
        await update_user_llm_credential(
            user_id=user_id,
            provider=provider,
            encrypted_api_key=encrypted_api_key,
            key_last4=get_last4(api_key),
            model=model,
        )
    else:
        await save_user_llm_credential(
            user_id=user_id,
            provider=provider,
            encrypted_api_key=encrypted_api_key,
            key_last4=get_last4(api_key),
            model=model,
        )

    return {
        "success": True,
        "provider": provider,
        "model": model,
        "key_last4": get_last4(api_key),
    }


@router.delete("/{provider}")
async def disconnect_llm_provider(
    provider: str,
    user_id: str = Depends(get_current_user),
):
    provider = normalize_provider(provider)

    await delete_user_llm_credential(
        user_id=user_id,
        provider=provider,
    )

    return {
        "success": True,
        "provider": provider,
    }