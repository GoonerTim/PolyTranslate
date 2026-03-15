"""Tests for JSON parsing utilities."""

from __future__ import annotations

import json

import pytest

from app.utils.json_helpers import parse_json_response


class TestParseJsonResponse:
    def test_plain_json(self) -> None:
        result = parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_markdown_fence(self) -> None:
        result = parse_json_response('```json\n{"score": 8}\n```')
        assert result == {"score": 8}

    def test_json_with_generic_fence(self) -> None:
        result = parse_json_response('```\n{"a": 1}\n```')
        assert result == {"a": 1}

    def test_json_with_whitespace(self) -> None:
        result = parse_json_response('  \n {"x": true} \n ')
        assert result == {"x": True}

    def test_json_array(self) -> None:
        result = parse_json_response("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("not json at all")

    def test_fence_only_json_prefix(self) -> None:
        # ```json prefix stripped, then ``` suffix stripped
        result = parse_json_response("```json\n[]\n```")
        assert result == []

    def test_nested_json_with_fence(self) -> None:
        raw = '```json\n{"scores": [1, 2], "nested": {"a": "b"}}\n```'
        result = parse_json_response(raw)
        assert result["scores"] == [1, 2]
        assert result["nested"]["a"] == "b"

    def test_generic_fence_without_json_label(self) -> None:
        # Starts with ``` but not ```json — only the generic ``` prefix strip applies
        result = parse_json_response('```\n{"ok": true}\n```')
        assert result == {"ok": True}
