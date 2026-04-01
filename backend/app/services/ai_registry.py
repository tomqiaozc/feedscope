"""AI provider registry — known AI providers and their defaults."""

AI_PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "label": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-20250514",
        "sdk_type": "anthropic",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "sdk_type": "openai",
    },
    "custom": {
        "label": "Custom",
        "base_url": "",
        "default_model": "",
        "sdk_type": "openai",
    },
}
