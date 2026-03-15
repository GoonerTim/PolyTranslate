"""JSON parsing utilities for LLM responses."""

from __future__ import annotations

import json
from typing import Any


def parse_json_response(response: str) -> Any:
    """Strip markdown fences from LLM response and parse JSON."""
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    return json.loads(response.strip())
