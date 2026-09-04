from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from dataclasses import dataclass
from typing import Any

from risk_dashboard.modules.ai_tutor.domain.teaching_policy import (
    contains_investment_advice,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    NumericClaimRef,
)

# Standard pedagogical enumeration and benchmark constants allowed in educational texts
_ALLOWED_PEDAGOGICAL_NUMBERS = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "1-day", "5-day", "10-day", "252", "100", "1,000", "1000",
    "90", "90%", "95", "95%", "99", "99%", "99.9", "99.9%", "100", "100%",
    "0.0", "0.00", "15", "15%", "20", "20%", "25", "25%", "30", "30%",
    "0.8", "1.5", "2.0", "10", "10%",
}


def _extract_typed_numbers(text: str) -> list[tuple[str, Decimal, str | None]]:
    """Extracts numeric tokens with optional unit from prose text.

    Returns list of (raw_token, decimal_value, unit_or_none).
    Handles patterns like "42", "42%", "42.5%", "42 USD", "42 VND", "0.15".
    """
    # Match: number (optionally with decimals/commas), optional % or word unit
    pattern = r'(?<!\w)(\d+(?:[.,]\d+)?)(\s*%|\s+[a-zA-ZđĐàáảãạ]+)?(?=\s|[.,;:?!)\]>]|$)'
    results: list[tuple[str, Decimal, str | None]] = []
    for m in re.finditer(pattern, text):
        num_str = m.group(1).replace(",", "")
        unit_part = (m.group(2) or "").strip()
        unit: str | None = unit_part if unit_part else None
        try:
            dec = Decimal(num_str)
            raw = f"{num_str}{unit_part}" if unit_part else num_str
            results.append((raw, dec, unit))
        except (InvalidOperation, ValueError):
            continue
    return results


def _parse_canonical_typed_value(raw_val: Any, explicit_unit: str | None = None) -> tuple[Decimal, str | None] | None:
    """Parses a raw evidence/claim value into a canonical (Decimal, unit) tuple."""
    if raw_val is None:
        return None
    s = str(raw_val).strip()
    unit = explicit_unit.strip() if explicit_unit and explicit_unit.strip() else None
    if s.endswith("%"):
        unit = "%"
        s = s[:-1].strip()
    elif " " in s:
        parts = s.rsplit(" ", 1)
        if not parts[1].replace(".", "").isdigit():
            s = parts[0].strip()
            unit = unit or parts[1].strip()
    s = s.replace(",", "").strip()
    try:
        dec = Decimal(s)
        return dec, unit
    except (InvalidOperation, ValueError):
        return None


class EvidenceAndNumericReviewer:
    """Verifies that all numeric claims in metadata AND prose text are strictly grounded in deterministic tool evidence."""

    def review(
        self,
        candidate_text: str,
        evidence: dict[str, str] | None,
        citations: tuple[CitationRef, ...],
        numeric_claims: tuple[NumericClaimRef, ...],
    ) -> tuple[tuple[CitationRef, ...], tuple[NumericClaimRef, ...], str, list[str]]:
        evidence = evidence or {}
        rejections: list[str] = []

        # 1. Validate citations
        valid_citations: list[CitationRef] = []
        for cite in citations:
            if cite.source_id:
                valid_citations.append(cite)

        # 2. Validate metadata numeric claims with canonical Decimal value and exact unit matching
        valid_numeric: list[NumericClaimRef] = []
        for claim in numeric_claims:
            ev_val = evidence.get(claim.evidence_ref)
            if ev_val is None:
                rejections.append(f"missing_evidence_for_claim_{claim.claim_id}")
                continue

            ev_typed = _parse_canonical_typed_value(ev_val)
            claim_typed = _parse_canonical_typed_value(claim.value, claim.unit)

            if ev_typed is None or claim_typed is None:
                if str(ev_val).strip() != str(claim.value).strip():
                    rejections.append(f"numeric_mismatch_for_claim_{claim.claim_id}")
                    continue
                if claim.unit is not None:
                    rejections.append(f"unit_mismatch_for_claim_{claim.claim_id}")
                    continue
            else:
                ev_dec, ev_unit = ev_typed
                claim_dec, claim_unit = claim_typed
                if ev_unit != claim_unit:
                    rejections.append(f"unit_mismatch_for_claim_{claim.claim_id}")
                    continue
                if ev_dec != claim_dec:
                    rejections.append(f"numeric_mismatch_for_claim_{claim.claim_id}")
                    continue

            valid_numeric.append(claim)

        # 3. Validate numbers in prose text - STRICT typed (Decimal, unit) matching against evidence
        # Build typed evidence set: (Decimal, unit_or_none) pairs
        allowed_typed: set[tuple[Decimal, str | None]] = set()
        for k, v in evidence.items():
            parsed = _parse_canonical_typed_value(v)
            if parsed is not None:
                allowed_typed.add(parsed)

        # Build plain string set for pedagogical constants
        allowed_pedagogical: set[str] = set(_ALLOWED_PEDAGOGICAL_NUMBERS)

        # Filter ungrounded numeric statements line-by-line
        sanitized_lines: list[str] = []
        for line in candidate_text.splitlines():
            typed_nums = _extract_typed_numbers(line)
            has_ungrounded = False
            for raw, dec_val, unit in typed_nums:
                # Allow pedagogical constants by raw string
                if raw in allowed_pedagogical:
                    continue
                # Check typed evidence match: both value AND unit must match exactly
                if (dec_val, unit) not in allowed_typed:
                    has_ungrounded = True
                    rejections.append(f"ungrounded_prose_number_{raw}")
            if has_ungrounded:
                continue
            sanitized_lines.append(line)

        sanitized_text = "\n".join(sanitized_lines).strip()
        if not sanitized_text:
            sanitized_text = "Em đã phân tích dữ liệu nhưng một số số liệu chưa đủ bằng chứng xác thực để trích dẫn."

        return tuple(valid_citations), tuple(valid_numeric), sanitized_text, rejections


class SafetyAndPolicyReviewer:
    """Enforces safety rules: strips buy/sell advice, maintains polite register and educational framing."""

    def review(self, text: str) -> tuple[bool, str, list[str], str | None]:
        rejections: list[str] = []
        policy_notice: str | None = None

        if contains_investment_advice(text):
            rejections.append("contains_investment_advice")
            policy_notice = "Nội dung chỉ phục vụ mục đích học tập và nghiên cứu, không cấu thành khuyến nghị đầu tư."

            # Strip specific advisory sentences line-by-line while preserving educational explanations
            cleaned_lines = []
            for line in text.splitlines():
                if contains_investment_advice(line):
                    continue
                cleaned_lines.append(line)
            cleaned_text = "\n".join(cleaned_lines).strip()
            if cleaned_text:
                text = f"{cleaned_text}\n\nLưu ý: {policy_notice}"
            else:
                text = policy_notice

        return (len(rejections) == 0), text, rejections, policy_notice
