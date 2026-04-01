"""Unit tests for SSE event formatting."""

import json

from app.services.sse_utils import sse_event


class TestSseEvent:
    def test_format(self):
        result = sse_event("progress", {"count": 5})
        assert result == 'event: progress\ndata: {"count": 5}\n\n'

    def test_ends_with_double_newline(self):
        result = sse_event("done", {})
        assert result.endswith("\n\n")

    def test_event_name(self):
        result = sse_event("error", {"msg": "fail"})
        assert result.startswith("event: error\n")

    def test_data_is_valid_json(self):
        result = sse_event("test", {"key": "value", "nested": {"a": 1}})
        data_line = result.split("\n")[1]
        assert data_line.startswith("data: ")
        payload = json.loads(data_line[len("data: ") :])
        assert payload["key"] == "value"
        assert payload["nested"]["a"] == 1

    def test_empty_data(self):
        result = sse_event("ping", {})
        assert "data: {}" in result

    def test_special_characters(self):
        result = sse_event("msg", {"text": "hello\nworld"})
        # Newlines in JSON should be escaped
        data_line = result.split("\n")[1]
        payload = json.loads(data_line[len("data: ") :])
        assert payload["text"] == "hello\nworld"
