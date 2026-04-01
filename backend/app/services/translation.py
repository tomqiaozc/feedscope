"""Core AI translation service — config loader, client factory, translator, parser."""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.db.repos.settings_repo import SettingsRepo
from app.services.ai_registry import AI_PROVIDERS
from app.services.prompt import render_prompt


class AiConfig(BaseModel):
    provider_id: str
    api_key: str
    model: str
    base_url: str | None = None
    sdk_type: str = "openai"
    custom_prompt: str | None = None


class TranslationResult(BaseModel):
    translation: str
    editorial: str | None = None
    quoted_translation: str | None = None


async def load_ai_config(user_id: str, session) -> AiConfig | None:
    """Load AI configuration from user settings. Returns None if not configured."""
    repo = SettingsRepo(user_id, session)
    values = await repo.get_many("ai.")

    api_key = values.get("ai.api_key")
    if not api_key:
        return None

    provider_id = values.get("ai.provider_id", "openai")
    provider_defaults = AI_PROVIDERS.get(provider_id, AI_PROVIDERS["openai"])

    return AiConfig(
        provider_id=provider_id,
        api_key=api_key,
        model=values.get("ai.model") or provider_defaults["default_model"],
        base_url=values.get("ai.base_url") or provider_defaults.get("base_url"),
        sdk_type=values.get("ai.sdk_type") or provider_defaults.get("sdk_type", "openai"),
        custom_prompt=values.get("ai.custom_prompt"),
    )


def parse_translation(raw: str) -> TranslationResult:
    """Parse AI response into structured translation result."""
    translation = ""
    editorial = None
    quoted_translation = None

    # Extract sections by markers
    sections = re.split(r"\[(翻译|引用翻译|锐评)\]", raw)

    current_key = None
    for part in sections:
        stripped = part.strip()
        if stripped == "翻译":
            current_key = "translation"
        elif stripped == "引用翻译":
            current_key = "quoted_translation"
        elif stripped == "锐评":
            current_key = "editorial"
        elif current_key and stripped:
            if current_key == "translation":
                translation = stripped
            elif current_key == "quoted_translation":
                quoted_translation = stripped
            elif current_key == "editorial":
                editorial = stripped

    # Fallback: if no markers found, use the whole response as translation
    if not translation:
        translation = raw.strip()

    return TranslationResult(
        translation=translation,
        editorial=editorial,
        quoted_translation=quoted_translation,
    )


async def translate_post(
    content: str,
    config: AiConfig,
    *,
    quoted_content: str | None = None,
) -> TranslationResult:
    """Translate post content using the configured AI provider."""
    prompt = render_prompt(
        content,
        quoted_content=quoted_content,
        custom_prompt=config.custom_prompt,
    )

    raw_response = await _call_ai(prompt, config)
    return parse_translation(raw_response)


async def _call_ai(prompt: str, config: AiConfig) -> str:
    """Call the AI provider and return the raw text response."""
    if config.sdk_type == "anthropic":
        import anthropic

        client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url
            if config.base_url and config.base_url != "https://api.anthropic.com"
            else anthropic.NOT_GIVEN,
        )
        response = await client.messages.create(
            model=config.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""
    else:
        import openai

        client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or None,
        )
        response = await client.chat.completions.create(
            model=config.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
