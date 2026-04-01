"""Translation prompt template and renderer."""

from __future__ import annotations

DEFAULT_PROMPT = """\
你是一位专业的社交媒体内容翻译和分析师。请将以下推文翻译成中文，并提供简短锐评。

请严格按照以下格式输出：

[翻译]
（在此输出推文的中文翻译）

{{#quoted}}
[引用翻译]
（在此输出被引用推文的中文翻译）

{{/quoted}}
[锐评]
（在此输出一句简短的锐评，点评推文的要点、影响或值得关注之处）

---
推文内容：
{{content}}
{{#quoted}}

引用推文内容：
{{quoted_content}}
{{/quoted}}
"""


def render_prompt(
    content: str,
    *,
    quoted_content: str | None = None,
    custom_prompt: str | None = None,
) -> str:
    """Render the translation prompt with content variables."""
    template = custom_prompt or DEFAULT_PROMPT

    # Handle conditional {{#quoted}}...{{/quoted}} blocks
    if quoted_content:
        template = template.replace("{{#quoted}}", "").replace("{{/quoted}}", "")
        template = template.replace("{{quoted_content}}", quoted_content)
    else:
        # Remove entire quoted blocks
        import re

        template = re.sub(r"\{\{#quoted\}\}.*?\{\{/quoted\}\}", "", template, flags=re.DOTALL)

    template = template.replace("{{content}}", content)
    return template.strip()
