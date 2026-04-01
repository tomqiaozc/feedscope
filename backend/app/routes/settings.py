from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.engine import get_db_session
from app.db.repos.credentials_repo import CredentialsRepo
from app.db.repos.settings_repo import SettingsRepo
from app.schemas.settings import (
    AISettingsOut,
    AISettingsUpdate,
    AITestResult,
    CredentialOut,
    CredentialUpsert,
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

AI_SETTING_KEYS = [
    "ai.provider_id",
    "ai.api_key",
    "ai.model",
    "ai.base_url",
    "ai.sdk_type",
    "ai.custom_prompt",
]


def _cred_to_out(c) -> CredentialOut:
    return CredentialOut(
        id=c.id,
        provider=c.provider,
        has_api_key=c.api_key is not None and c.api_key != "",
        has_cookie=c.cookie is not None and c.cookie != "",
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


# --- Credentials ---


@router.get("/credentials")
async def list_credentials(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = CredentialsRepo(user_id, session)
    creds = await repo.list()
    return {"success": True, "data": [_cred_to_out(c) for c in creds]}


@router.put("/credentials")
async def upsert_credential(
    body: CredentialUpsert,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = CredentialsRepo(user_id, session)
    cred = await repo.upsert(provider=body.provider, api_key=body.api_key, cookie=body.cookie)
    return {"success": True, "data": _cred_to_out(cred)}


@router.delete("/credentials/{provider}")
async def delete_credential(
    provider: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = CredentialsRepo(user_id, session)
    deleted = await repo.delete(provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"success": True}


# --- AI Settings ---


@router.get("/ai")
async def get_ai_settings(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = SettingsRepo(user_id, session)
    values = await repo.get_many("ai.")
    return {
        "success": True,
        "data": AISettingsOut(
            provider_id=values.get("ai.provider_id"),
            has_api_key=bool(values.get("ai.api_key")),
            model=values.get("ai.model"),
            base_url=values.get("ai.base_url"),
            sdk_type=values.get("ai.sdk_type"),
            custom_prompt=values.get("ai.custom_prompt"),
        ),
    }


@router.put("/ai")
async def update_ai_settings(
    body: AISettingsUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = SettingsRepo(user_id, session)
    field_map = {
        "ai.provider_id": body.provider_id,
        "ai.api_key": body.api_key,
        "ai.model": body.model,
        "ai.base_url": body.base_url,
        "ai.sdk_type": body.sdk_type,
        "ai.custom_prompt": body.custom_prompt,
    }
    for key, value in field_map.items():
        if value is not None:
            await repo.set(key, value)
    # Re-read to return current state
    values = await repo.get_many("ai.")
    return {
        "success": True,
        "data": AISettingsOut(
            provider_id=values.get("ai.provider_id"),
            has_api_key=bool(values.get("ai.api_key")),
            model=values.get("ai.model"),
            base_url=values.get("ai.base_url"),
            sdk_type=values.get("ai.sdk_type"),
            custom_prompt=values.get("ai.custom_prompt"),
        ),
    }


@router.post("/ai/test")
async def test_ai_connection(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = SettingsRepo(user_id, session)
    values = await repo.get_many("ai.")

    provider_id = values.get("ai.provider_id")
    api_key = values.get("ai.api_key")
    model = values.get("ai.model")
    base_url = values.get("ai.base_url")
    sdk_type = values.get("ai.sdk_type")

    if not api_key:
        raise HTTPException(status_code=400, detail="No AI API key configured")

    try:
        if sdk_type == "anthropic" or (not sdk_type and provider_id == "anthropic"):
            import anthropic

            client = anthropic.AsyncAnthropic(
                api_key=api_key, base_url=base_url or anthropic.NOT_GIVEN
            )
            response = await client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": "Say hello in one sentence."}],
            )
            preview = response.content[0].text if response.content else ""
        else:
            import openai

            client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url or None)
            response = await client.chat.completions.create(
                model=model or "gpt-4o-mini",
                max_tokens=50,
                messages=[{"role": "user", "content": "Say hello in one sentence."}],
            )
            preview = response.choices[0].message.content or ""

        return {
            "success": True,
            "data": AITestResult(
                provider=provider_id,
                model=model,
                response_preview=preview[:200],
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AI connection test failed: {e}") from e
