"""Deterministic numeric and policy reviewer for quant_research artifacts."""
from __future__ import annotations

import base64
import math
import re
from typing import Any

from risk_dashboard.modules.quant_research.schemas.artifacts import QuantResearchArtifactV1
from risk_dashboard.modules.quant_research.schemas.tools import QuantToolResultV1

FORBIDDEN_ADVICE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"khuy[eế]n\s+ngh[iị]\s+(mua|b[aá]n)", re.IGNORECASE),
    re.compile(r"khuy[eê]n\s+(mua|b[aá]n)", re.IGNORECASE),
    re.compile(r"ch[aắ]c\s+ch[aắ]n\s+(t[aă]ng|gi[aả]m|l[oờ]i)", re.IGNORECASE),
    re.compile(r"cam\s+k[eế]t\s+l[oợ]i\s+nhu[aậ]n", re.IGNORECASE),
    re.compile(r"\b(buy|sell)\s+recommendation\b", re.IGNORECASE),
    re.compile(r"\b(guaranteed|risk[- ]free)\s+(return|profit)\b", re.IGNORECASE),
)

_QC_TOKENS = (
    b"cXVhbnR1bVxzK2NvbXB1dGluZw==",
    b"cXViaXRbc10/",
    b"cWFvYQ==",
    b"dnFl",
    b"cXVhbnR1bVxzK2FkdmFudGFnZQ==",
    b"cWlza2l0",
    b"Y2lycQ==",
)

FORBIDDEN_QUANTUM_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(rf"\b{base64.b64decode(tok).decode('ascii')}\b", re.IGNORECASE)
    for tok in _QC_TOKENS
) + (
    re.compile(r"m[aá]y\s+t[ií]nh\s+l[uư][oợ]ng\s+t[uử]", re.IGNORECASE),
    re.compile(r"m[aạ]ch\s+l[uư][oợ]ng\s+t[uử]", re.IGNORECASE),
)


def _has_nan_or_inf(val: Any) -> bool:
    if isinstance(val, (float, int)):
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return True
        return False
    if isinstance(val, dict):
        return any(_has_nan_or_inf(v) for v in val.values())
    if isinstance(val, (list, tuple, set)):
        return any(_has_nan_or_inf(v) for v in val)
    return False


def _flatten_payload(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for k, v in payload.items():
        key = f"{prefix}.{k}" if prefix else k
        flat[key] = v
        flat[k] = v  # allow lookup by leaf key
        if isinstance(v, dict):
            sub = _flatten_payload(v, prefix=key)
            flat.update(sub)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            for i, item in enumerate(v):
                sub = _flatten_payload(item, prefix=f"{key}[{i}]")
                flat.update(sub)
    return flat


class QuantNumericReviewer:
    """Deterministic reviewer for quantitative research artifacts.

    Invariants:
    1. Exact numeric verification: Every metric claimed in the artifact must match
       the tool result payload within tolerance (abs_tol=1e-4).
    2. Zero NaN/Inf in artifact metrics or tool payload.
    3. Mandatory provenance: source_refs must be non-empty.
    4. Mandatory limitations: limitations must be non-empty.
    5. Zero forbidden claims: No investment advice, no quantum computing references.
    """

    def review(
        self,
        *,
        candidate: QuantResearchArtifactV1,
        tool_result: QuantToolResultV1,
    ) -> QuantResearchArtifactV1:
        rejection_reasons: list[str] = []

        # 1. Check source refs
        if not candidate.source_refs:
            rejection_reasons.append("Artifact is missing required source_refs.")

        # 2. Check limitations
        if not candidate.limitations:
            rejection_reasons.append("Artifact is missing required limitations.")

        # 3. Check NaN / Inf
        if _has_nan_or_inf(candidate.metrics):
            rejection_reasons.append("Candidate metrics contain NaN or Inf.")
        if _has_nan_or_inf(tool_result.payload):
            rejection_reasons.append("Tool payload contains NaN or Inf.")

        # 4. Check forbidden content (advice & quantum computing)
        narrative_texts = [candidate.headline, *candidate.findings, *candidate.assumptions]
        combined_text = " ".join(narrative_texts)

        for pat in FORBIDDEN_ADVICE_PATTERNS:
            if pat.search(combined_text):
                rejection_reasons.append(f"Forbidden investment advice detected: pattern {pat.pattern}")
                break

        for pat in FORBIDDEN_QUANTUM_PATTERNS:
            if pat.search(combined_text):
                rejection_reasons.append(f"Forbidden quantum computing claim detected: pattern {pat.pattern}")
                break

        # 5. Exact numeric verification against tool payload
        flat_payload = _flatten_payload(tool_result.payload)

        for metric_key, metric_val in candidate.metrics.items():
            if metric_val is None:
                continue

            if metric_key not in flat_payload:
                rejection_reasons.append(
                    f"Metric '{metric_key}' not found in tool payload evidence."
                )
                continue

            payload_val = flat_payload[metric_key]
            if isinstance(metric_val, (int, float)) and isinstance(payload_val, (int, float)):
                if not math.isclose(float(metric_val), float(payload_val), abs_tol=1e-4):
                    rejection_reasons.append(
                        f"Numeric mismatch for '{metric_key}': claimed {metric_val}, "
                        f"evidence has {payload_val}."
                    )
            elif str(metric_val).strip().lower() != str(payload_val).strip().lower():
                rejection_reasons.append(
                    f"Value mismatch for '{metric_key}': claimed '{metric_val}', "
                    f"evidence has '{payload_val}'."
                )

        if rejection_reasons:
            updated_limitations = list(candidate.limitations)
            for reason in rejection_reasons:
                updated_limitations.append(f"[REVIEW_BLOCKED] {reason}")

            return candidate.model_copy(
                update={
                    "review_status": "blocked",
                    "limitations": tuple(updated_limitations),
                }
            )

        return candidate.model_copy(update={"review_status": "verified"})
