from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from jsonschema import ValidationError, validate

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
      candidate = current_text.strip()
      if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
      err: Exception | None = None
      try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
          raise ModelError(
              "schema_invalid", "Model response must be a JSON object."
          )
        if schema is not None:
          validate(instance=parsed, schema=schema)
        return parsed
      except json.JSONDecodeError as exc:
        err = ModelError("schema_invalid", "Model response is not valid JSON.")
        err.__cause__ = exc
      except ValidationError as exc:
        err = ModelError("schema_invalid", "Model response does not match output schema.")
        err.__cause__ = exc
      except ModelError as exc:
        err = exc

      if repair_fn is not None and attempts < max_repairs:
        attempts += 1
        try:
          current_text = repair_fn(current_text, err)
          continue
        except Exception as repair_exc:
          raise err from repair_exc

      raise err
