---
phase: 5
title: "BCTC4 — Numeric Reviewer"
status: completed
priority: P1
effort: "5h"
dependencies: [2]
---

# Phase 5: BCTC4 — Numeric Reviewer & Claim-Tool Mapping

## Overview

Tạo numeric reviewer chạy trước mọi BCTC response. Reviewer map từng numeric claim về tool result. `unsupported_claims` không rỗng → response không được gửi. Adversarial suite: fabricated number, đúng-số-sai-kỳ, unit swap, stale revision — tất cả bị block.

## Requirements

### Functional

- `NumericReviewer` class nhận list claims + list tool results
- Map mỗi claim về tool evidence bằng: value + unit + period + report_id
- Unmapped claim → thêm vào `unsupported_claims`
- `unsupported_claims` non-empty → block response (return review decision "reject")
- Hypothetical example phải gắn nhãn rõ (không bị block)
- Review decisions: `pass`, `repair`, `reject`
- Reviewer KHÔNG viết lại số liệu — chỉ verify hoặc reject

### Non-functional

- Reviewer chạy synchronously trước response delivery
- No false negatives trên adversarial suite

## Related Code Files

### Create

- `src/risk_dashboard/modules/financials_product/application/numeric_reviewer.py`
- `tests/test_bctc_numeric_reviewer.py`

### Reference

- `src/risk_dashboard/modules/financials_product/schemas/agent_tools.py` — NumericValue, ProvenanceRef
- Module 04 pattern: `checkpoint_service.py` grading boundary → similar verification boundary

## Implementation Steps

### Step 1: Define `NumericClaim` and `ReviewDecision`

```python
@dataclass(frozen=True)
class NumericClaim:
    claim_id: str
    statement: str          # e.g. "Biên lợi nhuận gộp tăng 2,1%"
    value: float
    unit: str
    period: str
    report_id: str
    revision_id: str
    is_hypothetical: bool = False

@dataclass(frozen=True)
class ReviewDecision:
    verdict: Literal["pass", "repair", "reject"]
    accepted_claims: tuple[str, ...]
    rejected_claims: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    violations: tuple[str, ...]
```

### Step 2: Implement `NumericReviewer`

```python
class NumericReviewer:
    def review(
        self,
        claims: Sequence[NumericClaim],
        tool_results: Sequence[NumericValue],
    ) -> ReviewDecision:
        accepted = []
        rejected = []
        unsupported = []
        violations = []

        for claim in claims:
            if claim.is_hypothetical:
                accepted.append(claim.claim_id)
                continue
            matched = self._find_matching_evidence(claim, tool_results)
            if matched:
                accepted.append(claim.claim_id)
            else:
                unsupported.append(claim.claim_id)
                violations.append(f"Claim '{claim.claim_id}' has no matching tool evidence")

        verdict = "pass" if not unsupported else "reject"
        return ReviewDecision(
            verdict=verdict,
            accepted_claims=tuple(accepted),
            rejected_claims=tuple(rejected),
            unsupported_claims=tuple(unsupported),
            violations=tuple(violations),
        )

    def _find_matching_evidence(self, claim: NumericClaim, results: Sequence[NumericValue]) -> bool:
        for r in results:
            if (
                r.value is not None
                and abs(r.value - claim.value) < 1e-6
                and r.unit == claim.unit
                and r.provenance.period == claim.period
                and r.provenance.report_id == claim.report_id
            ):
                return True
        return False
```

### Step 3: Adversarial test suite

```python
# test_bctc_numeric_reviewer.py

def test_fabricated_number_rejected():
    """Claim with number not in any tool result → rejected."""

def test_correct_number_wrong_period_rejected():
    """Right value but wrong period → rejected."""

def test_unit_swap_rejected():
    """VND claim matched against VND_bn tool result → rejected."""

def test_stale_revision_rejected():
    """Claim from old revision_id not matching current → rejected."""

def test_all_claims_match_passes():
    """All claims map to tool results → pass."""

def test_hypothetical_not_blocked():
    """Hypothetical example claim (is_hypothetical=True) → accepted regardless."""

def test_empty_claims_passes():
    """No claims → pass."""

def test_mixed_pass_and_reject():
    """Some match, some don't → reject (unsupported non-empty)."""
```

## Success Criteria

- [ ] Fabricated number → rejected
- [ ] Right number wrong period → rejected
- [ ] Unit swap (VND vs VND_bn) → rejected
- [ ] Stale revision → rejected
- [ ] All claims match → pass
- [ ] Hypothetical example → accepted (not blocked)
- [ ] `unsupported_claims` non-empty → verdict "reject"
- [ ] ≥8 tests pass
