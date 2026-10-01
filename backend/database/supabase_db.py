import logging
import httpx
import json
from datetime import datetime, timezone
from typing import Any,List, Optional, Dict

logger = logging.getLogger('ats_resume_scorer')

from backend.core.config import SUPABASE_URL, SUPABASE_KEY

def _get_headers():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
def _get_rest_url(table: str) -> str:
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured.")

    return f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"

async def supabase_rest_delete(
    table: str,
    params: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError(
            "Supabase database configuration is not available."
        )

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=headers,
                params=params or {},
            )

            response.raise_for_status()

            result = response.json()

            return result if isinstance(result, list) else []

    except Exception as exc:
        logger.error(
            f"Supabase DELETE failed for {table}: {exc}"
        )
        raise
async def save_analysis(user_id: str, filename: str, analysis_result: Dict) -> Optional[str]:
    headers = _get_headers()
    if not headers:
        return None

    def _json_default(o):
        if hasattr(o, 'model_dump'):
            return o.model_dump()
        return str(o)
    serializable_result = json.loads(json.dumps(analysis_result, default=_json_default))

    doc = {
        "user_id": user_id,
        "filename": filename,
        "ats_score": serializable_result.get("ats_score", 0),
        "keyword_match": serializable_result.get("keyword_match", 0),
        "missing_keywords": serializable_result.get("missing_keywords", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analysis_result": serializable_result,
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=doc)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                inserted_id = str(data[0].get("id"))
                logger.info(f"Saved analysis for user {user_id}: {inserted_id}")
                return inserted_id
            return None
    except Exception as exc:
        logger.error(f"Failed to save analysis to Supabase: {exc}")
        return None

async def get_user_history(user_id: str) -> List[Dict]:
    headers = _get_headers()
    if not headers:
        return []

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers=headers, 
                params={
                    "user_id": f"eq.{user_id}",
                    "order": "created_at.desc"
                }
            )
            response.raise_for_status()
            docs = response.json()
            
            results = []
            for doc in docs:
                results.append({
                    "id": str(doc.get("id")),
                    "filename": doc.get("filename", "resume"),
                    "resume_name": doc.get("filename", "resume"),
                    "job_title": "Software Engineer",
                    "ats_score": doc.get("ats_score", 0),
                    "keyword_match": doc.get("keyword_match", 0),
                    "missing_keywords": doc.get("missing_keywords", []),
                    "date": doc.get("created_at", ""),
                    "created_at": doc.get("created_at", ""),
                    "analysis_result": doc.get("analysis_result", {}),
                })
            return results
    except Exception as exc:
        logger.error(f"Failed to fetch history from Supabase: {exc}")
        return []
# ============================================================
# PHASE 7B — FREE QUOTA COUNTERS
# ============================================================

async def count_user_resume_analyses(
    user_id: str,
) -> int:
    """
    Count successful resume analyses for a user.

    The existing `analyses` table is used as the source of truth.
    """

    try:

        rows = await supabase_rest_get(
            "analyses",
            {
                "user_id": f"eq.{user_id}",
                "select": "id",
            },
        )

        return len(rows or [])

    except Exception as exc:

        logger.exception(
            "Failed to count resume analyses for user %s",
            user_id,
        )

        raise

async def delete_analysis(analysis_id: str, user_id: str) -> bool:
    headers = _get_headers()
    if not headers:
        return False

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url, 
                headers=headers, 
                params={
                    "id": f"eq.{analysis_id}",
                    "user_id": f"eq.{user_id}"
                }
            )
            response.raise_for_status()
            return True
    except Exception as exc:
        logger.error(f"Failed to delete analysis {analysis_id}: {exc}")
        return False
async def get_user_profile(
    user_id: str,
) -> Optional[Dict]:
    headers = _get_headers()

    if not headers:
        return None

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
            )

            response.raise_for_status()

            data = response.json()

            if not data:
                return None

            return data[0]

    except Exception as exc:
        logger.error(
            f"Failed to fetch profile for {user_id}: {exc}"
        )
        return None


async def upsert_user_profile(
    user_id: str,
    username: str,
    career_interests: List[str],
    specializations: List[str],
    skills: List[str],
    target_roles: List[str],
    experience: str,
    graduation_year: Optional[int],
    onboarding_completed: bool = False,
    onboarding_step: int = 1,
) -> Optional[Dict]:

    headers = _get_headers()

    if not headers:
        return None

    headers = {
        **headers,
        "Prefer": (
            "resolution=merge-duplicates,"
            "return=representation"
        ),
    }

    url = (
        f"{SUPABASE_URL.rstrip('/')}"
        "/rest/v1/profiles"
    )

    doc = {
    "user_id": user_id,
    "username": username,
    "career_interests": career_interests,
    "specializations": specializations,
    "skills": skills,
    "target_roles": target_roles,
    "experience": experience,
    "graduation_year": graduation_year,
    "onboarding_completed": onboarding_completed,
    "onboarding_step": onboarding_step,
}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=doc,
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to save profile for {user_id}: {exc}"
        )

        return None

async def save_onboarding_progress(
    user_id: str,
    step: int,
    username: Optional[str] = None,
    career_interests: Optional[List[str]] = None,
    specializations: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    target_roles: Optional[List[str]] = None,
    experience: Optional[str] = None,
    graduation_year: Optional[int] = None,
) -> Optional[Dict]:
    """
    Persist incomplete onboarding progress.

    Creates the profile if it does not exist.
    Only fields explicitly provided are updated.
    onboarding_completed remains unchanged.
    """

    headers = _get_headers()

    if not headers:
        return None

    if step < 1 or step > 7:
        raise ValueError(
            "Onboarding step must be between 1 and 7."
        )

    try:
        existing = await get_user_profile(user_id)

        if existing is None:
            doc = {
                "user_id": user_id,
                "username": username or "",
                "career_interests": career_interests or [],
                "specializations": specializations or [],
                "skills": skills or [],
                "target_roles": target_roles or [],
                "experience": experience or "",
                "graduation_year": graduation_year,
                "onboarding_step": step,
                "onboarding_completed": False,
            }

            headers_upsert = {
                **headers,
                "Prefer": (
                    "resolution=merge-duplicates,"
                    "return=representation"
                ),
            }

            url = (
                f"{SUPABASE_URL.rstrip('/')}"
                "/rest/v1/profiles"
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers_upsert,
                    json=doc,
                )

                response.raise_for_status()

                data = response.json()

                if data:
                    return data[0]

                return None

        headers_patch = {
            **headers,
            "Prefer": "return=representation",
        }

        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

        doc = {
            "onboarding_step": step,
        }

        if username is not None:
            doc["username"] = username

        if career_interests is not None:
            doc["career_interests"] = career_interests

        if specializations is not None:
            doc["specializations"] = specializations

        if skills is not None:
            doc["skills"] = skills

        if target_roles is not None:
            doc["target_roles"] = target_roles

        if experience is not None:
            doc["experience"] = experience

        if graduation_year is not None:
            doc["graduation_year"] = graduation_year

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=headers_patch,
                params={
                    "user_id": f"eq.{user_id}",
                },
                json=doc,
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to save onboarding progress for {user_id}: {exc}"
        )

        return None
async def update_profile_resume(
    user_id: str,
    filename: str,
    resume_text: str,
) -> Optional[Dict]:

    headers = _get_headers()

    if not headers:
        return None

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    doc = {
        "resume_filename": filename,
        "resume_text": resume_text,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                },
                json=doc,
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to save resume for {user_id}: {exc}"
        )
        return None


async def mark_onboarding_completed(
    user_id: str,
) -> Optional[Dict]:

    headers = _get_headers()

    if not headers:
        return None

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=headers,
                params={
                    "user_id": f"eq.{user_id}",
                },
                json={
    "onboarding_completed": True,
    "onboarding_step": 7,
},
            )

            response.raise_for_status()

            data = response.json()

            if data:
                return data[0]

            return None

    except Exception as exc:
        logger.error(
            f"Failed to complete onboarding for {user_id}: {exc}"
        )
        return None
async def supabase_rest_get(
    table: str,
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError("Supabase database client is not available.")

    url = _get_rest_url(table)

    try:
        timeout = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=30.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                url,
                headers=headers,
                params=params or {},
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                return data

            return []

    except httpx.TimeoutException as exc:
        logger.error(
            "Supabase GET timeout for %s: %s",
            table,
            exc,
        )
        raise

    except Exception as exc:
        logger.exception(
            "Supabase GET failed for %s: %s",
            table,
            exc,
        )
        raise


async def supabase_rest_post(
    table: str,
    data: Any,
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError("Supabase database client is not available.")

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=30.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                json=data,
            )

            response.raise_for_status()

            result = response.json()

            if isinstance(result, list):
                return result

            return []

    except httpx.TimeoutException as exc:
        logger.error(
            "Supabase POST timeout for %s: %s",
            table,
            exc,
        )
        raise

    except Exception as exc:
        logger.exception(
            "Supabase POST failed for %s: %s",
            table,
            exc,
        )
        raise

async def supabase_rest_patch(
    table: str,
    params: Dict[str, Any],
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    headers = _get_headers()

    if not headers:
        raise RuntimeError("Supabase database client is not available.")

    headers = {
        **headers,
        "Prefer": "return=representation",
    }

    url = _get_rest_url(table)

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=30.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.patch(
                url,
                headers=headers,
                params=params,
                json=data,
            )

            response.raise_for_status()

            result = response.json()

            if isinstance(result, list):
                return result

            return []

    except httpx.TimeoutException as exc:
        logger.error(
            "Supabase PATCH timeout for %s: %s",
            table,
            exc,
        )
        raise

    except Exception as exc:
        logger.exception(
            "Supabase PATCH failed for %s: %s",
            table,
            exc,
        )
        raise

# ============================================================
# LLM USAGE
# ============================================================


async def save_llm_usage(
    *,
    user_id: str,
    provider: str,
    model: str,
    feature: str,
    usage_source: str = "platform",
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
    request_id: Optional[str] = None,
) -> List[Dict[str, Any]]:

    row = {
        "user_id": str(user_id),
        "provider": str(provider),
        "model": str(model),
        "feature": str(feature),
        "usage_source": str(
            usage_source
            or "platform"
        ),
        "input_tokens": max(
            0,
            int(input_tokens or 0),
        ),
        "output_tokens": max(
            0,
            int(output_tokens or 0),
        ),
        "total_tokens": max(
            0,
            int(total_tokens or 0),
        ),
        "request_id": request_id,
    }

    return await supabase_rest_post(
        "llm_usage",
        [row],
    )
async def get_user_llm_usage(
    user_id: str,
) -> List[Dict[str, Any]]:
    """
    Return all LLM usage records for a user.

    The caller can aggregate platform and BYOK
    usage independently using usage_source.
    """

    return await supabase_rest_get(
        "llm_usage",
        {
            "user_id": f"eq.{user_id}",
            "select": (
                "id,"
                "provider,"
                "model,"
                "feature,"
                "usage_source,"
                "input_tokens,"
                "output_tokens,"
                "total_tokens,"
                "request_id,"
                "created_at"
            ),
            "order": "created_at.desc",
        },
    )
async def get_user_platform_token_usage(
    user_id: str,
) -> Dict[str, int]:
    """
    Aggregate platform-funded LLM token usage.

    BYOK usage is deliberately excluded.
    """

    rows = await supabase_rest_get(
        "llm_usage",
        {
            "user_id": f"eq.{user_id}",
            "usage_source": "eq.platform",
            "select": (
                "input_tokens,"
                "output_tokens,"
                "total_tokens"
            ),
        },
    )

    input_tokens = sum(
        int(row.get("input_tokens") or 0)
        for row in rows
    )

    output_tokens = sum(
        int(row.get("output_tokens") or 0)
        for row in rows
    )

    total_tokens = sum(
        int(row.get("total_tokens") or 0)
        for row in rows
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }
async def get_user_byok_token_usage(
    user_id: str,
) -> Dict[str, int]:
    """
    Aggregate BYOK token usage.

    This is informational only and is not counted
    against the SmartHire platform allowance.
    """

    rows = await supabase_rest_get(
        "llm_usage",
        {
            "user_id": f"eq.{user_id}",
            "usage_source": "eq.byok",
            "select": (
                "input_tokens,"
                "output_tokens,"
                "total_tokens"
            ),
        },
    )

    input_tokens = sum(
        int(row.get("input_tokens") or 0)
        for row in rows
    )

    output_tokens = sum(
        int(row.get("output_tokens") or 0)
        for row in rows
    )

    total_tokens = sum(
        int(row.get("total_tokens") or 0)
        for row in rows
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }
# ============================================================
# PHASE 7C — USER LLM CREDENTIALS
# ============================================================

async def save_user_llm_credential(
    user_id: str,
    provider: str,
    encrypted_api_key: str,
    key_last4: str,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    data = {
        "user_id": user_id,
        "provider": provider,
        "encrypted_api_key": encrypted_api_key,
        "key_last4": key_last4,
        "model": model,
    }

    try:

        rows = await supabase_rest_post(
            "user_llm_credentials",
            data,
        )

        return (
            rows[0]
            if rows
            else None
        )

    except Exception as exc:

        logger.exception(
            "Failed to save LLM credential."
        )

        raise


async def update_user_llm_credential(
    user_id: str,
    provider: str,
    encrypted_api_key: str,
    key_last4: str,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    data = {
        "encrypted_api_key": encrypted_api_key,
        "key_last4": key_last4,
        "model": model,
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    try:

        rows = await supabase_rest_patch(
            "user_llm_credentials",
            {
                "user_id": f"eq.{user_id}",
                "provider": f"eq.{provider}",
            },
            data,
        )

        return (
            rows[0]
            if rows
            else None
        )

    except Exception as exc:

        logger.exception(
            "Failed to update LLM credential."
        )

        raise


async def get_user_llm_credentials(
    user_id: str,
) -> List[Dict[str, Any]]:

    try:

        return await supabase_rest_get(
            "user_llm_credentials",
            {
                "user_id": f"eq.{user_id}",
                "order": "provider.asc",
            },
        )

    except Exception as exc:

        logger.exception(
            "Failed to load LLM credentials."
        )

        raise


async def get_user_llm_credential(
    user_id: str,
    provider: str,
) -> Optional[Dict[str, Any]]:

    try:

        rows = await supabase_rest_get(
            "user_llm_credentials",
            {
                "user_id": f"eq.{user_id}",
                "provider": f"eq.{provider}",
                "limit": "1",
            },
        )

        return (
            rows[0]
            if rows
            else None
        )

    except Exception as exc:

        logger.exception(
            "Failed to load LLM credential."
        )

        raise


async def delete_user_llm_credential(
    user_id: str,
    provider: str,
) -> bool:

    try:

        rows = await supabase_rest_delete(
            "user_llm_credentials",
            {
                "user_id": f"eq.{user_id}",
                "provider": f"eq.{provider}",
            },
        )

        return bool(rows)

    except Exception as exc:

        logger.exception(
            "Failed to delete LLM credential."
        )

        raise