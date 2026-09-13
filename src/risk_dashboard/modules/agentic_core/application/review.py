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


def _parse_canonical_numeric(text: str) -> tuple[Decimal, str | None] | None:
    """Parses a numeric string into canonical (Decimal, unit)."""
    clean = text.strip(".,;:?!")
    unit = None
    if clean.endswith("%"):
        unit = "%"
        clean = clean[:-1].strip()
    elif " " in clean:
        parts = clean.rsplit(" ", 1)
        if not parts[1].replace(".", "").isdigit():
            clean = parts[0].strip()
            unit = parts[1].strip()
    clean = clean.replace(",", "").strip()
    try:
        return Decimal(clean), unit
    except (InvalidOperation, ValueError):
        return None


def _extract_statement_numeric_tokens(statement: str) -> list[tuple[Decimal, str | None]]:
    """Extracts numeric tokens with optional units (e.g. '42%', '42 VND', '0.045', '142')."""
    pattern = r'(?:\b|^)(\d+(?:[.,]\d+)?)(?:\s*(%|[a-zA-ZđĐ]+))?(?=\s|[.,;:?!)]|$)'
    matches = re.finditer(pattern, statement)
    tokens: list[tuple[Decimal, str | None]] = []
    for m in matches:
        num_str = m.group(1).replace(",", "")
        raw_unit = m.group(2)
        unit = raw_unit.strip() if raw_unit and raw_unit.strip() else None
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
    ev_lower = ev_val.strip().lower()
    if any(pattern in ev_lower for pattern in ("nan", "inf", "infinity")):
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
            # Check exact equality or within tolerance abs_tol (1e-4)
            if ev_dec == tok_dec or abs(ev_dec - tok_dec) <= abs_tol:
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
