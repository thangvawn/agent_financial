from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Sequence

from risk_dashboard.modules.agentic_core.schemas.claim import (
    Claim,
    ClaimKind,
    ClaimLedger,
    ClaimStatus,
    ReviewedArtifact,
    ReviewedClaim,
)

_NO_REVIEWED_CLAIMS = "Không có nhận định nào đủ bằng chứng để phát hành."


_NUMERIC_TOKEN_PATTERN = re.compile(
    r'(?:\b|^|(?<=[^\w.,]))([+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)(?:\s*(%|[a-zA-ZđĐ]+))?(?=\s|[.,;:?!)]|$)'
)
_NAN_INF_PATTERN = re.compile(r'(?i)(?:\b|^)[+-]?(?:nan|infinity|inf)(?:\b|$)')


def _parse_canonical_numeric(text: str) -> tuple[Decimal, str | None] | None:
    """Parses a numeric string into canonical (Decimal, unit)."""
    clean = text.strip(".,;:?!")
    tokens = _extract_statement_numeric_tokens(clean)
    if tokens:
        return tokens[0]
    return None


def _extract_statement_numeric_tokens(statement: str) -> list[tuple[Decimal, str | None]]:
    """Extracts numeric tokens with optional units (e.g. '42%', '42 VND', '0.045', '142', '-15%', '1e-5', '12,5%')."""
    matches = _NUMERIC_TOKEN_PATTERN.finditer(statement)
    tokens: list[tuple[Decimal, str | None]] = []
    for m in matches:
        raw_num = m.group(1)
        raw_unit = m.group(2)
        unit = raw_unit.strip() if raw_unit and raw_unit.strip() else None

        # Handle Vietnamese decimal comma (e.g., "12,5" -> "12.5") vs thousands separator ("1,000")
        if "," in raw_num and "." not in raw_num:
            parts = raw_num.split(",")
            if len(parts) == 2 and (unit == "%" or len(parts[1]) != 3):
                num_str = f"{parts[0]}.{parts[1]}"
            else:
                num_str = raw_num.replace(",", "")
        else:
            num_str = raw_num.replace(",", "")

        try:
            tokens.append((Decimal(num_str), unit))
        except (InvalidOperation, ValueError):
            continue
    return tokens


_DEFAULT_ABS_TOL = Decimal("0.0001")


def _match_single_numeric_evidence(
    statement: str,
    ev_val: str,
    abs_tol: Decimal = _DEFAULT_ABS_TOL,
) -> bool:
    """Matches an evidence numeric value against isolated numeric tokens in statement with tolerance and unit parity."""
    # Guard against NaN / Inf injection in evidence string
    if _NAN_INF_PATTERN.search(ev_val.strip()):
        return False

    ev_clean = ev_val.strip()
    ev_parsed = _parse_canonical_numeric(ev_clean)
    if ev_parsed is None:
        # Fallback to exact string matching
        tokens = re.findall(r'\b\S+\b', statement)
        return any(t.strip(".,;:?!") == ev_clean for t in tokens)

    ev_dec, ev_unit = ev_parsed
    if ev_dec.is_nan() or ev_dec.is_infinite():
        return False

    extracted_tokens = _extract_statement_numeric_tokens(statement)
    if not extracted_tokens:
        return False

    for tok_dec, tok_unit in extracted_tokens:
        if tok_dec.is_nan() or tok_dec.is_infinite():
            continue
        if ev_unit == tok_unit:
            # Check exact equality or strictly within tolerance abs_tol (< 1e-4)
            if ev_dec == tok_dec or abs(ev_dec - tok_dec) < abs_tol:
                return True

    return False


def _match_numeric_evidence(statement: str, values: Sequence[str | None]) -> bool:
    for value in values:
        if value is None:
            return False
        if not _match_single_numeric_evidence(statement, value):
            return False
    return True


def review_claims(
    claims: tuple[Claim, ...],
    evidence: dict[str, str] | None,
) -> ReviewedArtifact:
    evidence = evidence or {}
    reviewed = tuple(_review_claim(claim, evidence) for claim in claims)
    ledger = ClaimLedger(claims=reviewed)
    accepted = tuple(claim.statement for claim in reviewed if claim.status is ClaimStatus.ACCEPTED)
    if not accepted:
        return ReviewedArtifact(
            status=ClaimStatus.BLOCKED,
            text=_NO_REVIEWED_CLAIMS,
            ledger=ledger,
        )
    return ReviewedArtifact(
        status=ClaimStatus.ACCEPTED,
        text="\n".join(accepted),
        ledger=ledger,
    )


def _review_claim(claim: Claim, evidence: dict[str, str]) -> ReviewedClaim:
    if not claim.evidence_refs:
        return _blocked(claim, "missing_evidence")
    values = tuple(evidence.get(ref) for ref in claim.evidence_refs)
    if any(value is None for value in values):
        return _blocked(claim, "unknown_evidence")
    if claim.kind is ClaimKind.NUMERIC and not _match_numeric_evidence(claim.statement, values):
        return _blocked(claim, "numeric_evidence_mismatch")
    return ReviewedClaim(**claim.model_dump(), status=ClaimStatus.ACCEPTED)


def _blocked(claim: Claim, reason: str) -> ReviewedClaim:
    return ReviewedClaim(
        **claim.model_dump(),
        status=ClaimStatus.BLOCKED,
        block_reason=reason,
    )
