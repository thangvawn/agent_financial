from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from jsonschema import SchemaError, ValidationError, validate

from risk_dashboard.platform.ai_runtime.contracts import ModelError


def parse_structured(
    text: str,
    schema: dict[str, Any] | None = None,
    *,
    repair_fn: Callable[[str, Exception], str] | None = None,
    max_repairs: int = 2,
) -> dict[str, Any]:
    current_text = text
    attempts = 0
    while True:
        if isinstance(current_text, dict):
            return current_text
        candidate = str(current_text).strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", candidate)
        if match:
            candidate = match.group(1).strip()

        err: Exception | None = None
        try:
            parsed = json.loads(candidate)
            if not isinstance(parsed, dict):
                raise ModelError("schema_invalid", "Model response must be a JSON object.")
            if schema is not None:
                validate(instance=parsed, schema=schema)
            return parsed
        except json.JSONDecodeError as exc:
            err = ModelError("schema_invalid", "Model response is not valid JSON.")
            err.__cause__ = exc
        except (ValidationError, SchemaError) as exc:
            err = ModelError("schema_invalid", "Model response does not match output schema.")
            err.__cause__ = exc
        except ModelError as exc:
            err = exc

        if repair_fn is not None and attempts < max_repairs:
            attempts += 1
            try:
                current_text = str(repair_fn(current_text, err))
                continue
            except Exception as repair_exc:
                raise err from repair_exc

        raise err

