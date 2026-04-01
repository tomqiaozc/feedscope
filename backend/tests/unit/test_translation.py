"""Unit tests for translation parsing and prompt rendering."""

from app.services.prompt import render_prompt
from app.services.translation import TranslationResult, parse_translation


class TestParseTranslation:
    def test_structured_all_markers(self):
        raw = "[翻译]\n这是翻译\n[引用翻译]\n这是引用翻译\n[锐评]\n这是锐评"
        result = parse_translation(raw)
        assert result.translation == "这是翻译"
        assert result.quoted_translation == "这是引用翻译"
        assert result.editorial == "这是锐评"

    def test_structured_no_quoted(self):
        raw = "[翻译]\n这是翻译\n[锐评]\n这是锐评"
        result = parse_translation(raw)
        assert result.translation == "这是翻译"
        assert result.quoted_translation is None
        assert result.editorial == "这是锐评"

    def test_structured_translation_only(self):
        raw = "[翻译]\n仅翻译内容"
        result = parse_translation(raw)
        assert result.translation == "仅翻译内容"
        assert result.editorial is None

    def test_fallback_no_markers(self):
        raw = "This is just plain text response"
        result = parse_translation(raw)
        assert result.translation == "This is just plain text response"
        assert result.editorial is None
        assert result.quoted_translation is None

    def test_fallback_whitespace(self):
        raw = "  plain response with spaces  "
        result = parse_translation(raw)
        assert result.translation == "plain response with spaces"

    def test_returns_translation_result(self):
        result = parse_translation("[翻译]\ntest")
        assert isinstance(result, TranslationResult)

    def test_multiline_content(self):
        raw = "[翻译]\n第一行\n第二行\n[锐评]\n评论"
        result = parse_translation(raw)
        assert result.translation == "第一行\n第二行"
        assert result.editorial == "评论"


class TestRenderPrompt:
    def test_content_substitution(self):
        result = render_prompt("Hello world")
        assert "Hello world" in result
        assert "{{content}}" not in result

    def test_quoted_content_included(self):
        result = render_prompt("Main tweet", quoted_content="Quoted tweet")
        assert "Main tweet" in result
        assert "Quoted tweet" in result
        assert "{{#quoted}}" not in result
        assert "{{/quoted}}" not in result

    def test_quoted_content_absent(self):
        result = render_prompt("Main tweet")
        assert "引用推文" not in result
        assert "{{#quoted}}" not in result
        assert "{{/quoted}}" not in result

    def test_custom_prompt(self):
        custom = "Translate: {{content}}"
        result = render_prompt("Hello", custom_prompt=custom)
        assert result == "Translate: Hello"

    def test_custom_prompt_with_quoted(self):
        custom = "Translate: {{content}}{{#quoted}} Quote: {{quoted_content}}{{/quoted}}"
        result = render_prompt("Main", quoted_content="Sub", custom_prompt=custom)
        assert "Main" in result
        assert "Sub" in result

    def test_default_prompt_used(self):
        result = render_prompt("test content")
        # Should contain Chinese instructions from DEFAULT_PROMPT
        assert "翻译" in result
