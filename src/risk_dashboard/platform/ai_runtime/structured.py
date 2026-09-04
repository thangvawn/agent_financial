from __future__ import annotations

import json
from typing import Any

from jsonschema import ValidationError, validate

from risk_dashboard.platform.ai_runtime.contracts import ModelError


def parse_structured(text: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ModelError("schema_invalid", "Model response is not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ModelError("schema_invalid", "Model response must be a JSON object.")
    if schema is not None:
        try:
            validate(instance=parsed, schema=schema)
        except ValidationError as exc:
            raise ModelError("schema_invalid", "Model response does not match output schema.") from exc
    return parsed
