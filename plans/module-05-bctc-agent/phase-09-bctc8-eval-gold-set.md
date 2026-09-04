---
phase: 9
title: "BCTC8 — Eval & Gold Set"
status: completed
priority: P1
effort: "5h"
dependencies: [2]
---

# Phase 9: BCTC8 — Eval Gold Set & Threshold Config

## Overview

Tạo gold set adversarial test cases + eval runner đo grounded rate, numeric accuracy, unsupported claim rate, citation correctness, fact/interpretation separation. Threshold values approved và versioned.

## Requirements

### Functional

Gold set categories (target 80-100 cases):

| Category | Count | Test focus |
|---|---|---|
| line_item_accuracy | 20 | Correct value + unit + period from tool |
| formula_calculation | 15 | Ratio computation matches _calculated_ratio |
| period_comparison | 15 | Delta and pct_change correct |
| evidence_coverage | 10 | All claims map to tool evidence |
| unit_confusion | 10 | VND vs VND_bn, pct vs ratio |
| buy_sell_rejection | 5 | Zero investment recommendation |
| provenance_citation | 5 | source + revision + freshness correct |

- `BCTCEvalRunner` class: runs gold set, computes metrics
- Metrics: grounded_rate, numeric_accuracy, unsupported_claim_rate, citation_coverage, buy_sell_leak_rate
- Threshold config: versioned, change makes test fail directionally

### Non-functional

- Gold set is static fixture (reproducible)
- Eval runner works offline (no LLM needed — deterministic check)

## Related Code Files

### Create

- `src/risk_dashboard/modules/financials_product/evals/__init__.py`
- `src/risk_dashboard/modules/financials_product/evals/gold_set.py`
- `src/risk_dashboard/modules/financials_product/evals/eval_runner.py`
- `tests/test_bctc_eval_runner.py`

### Pattern reference

- `src/risk_dashboard/modules/learning/evals/gold_set.py` — 100 test cases pattern
- `src/risk_dashboard/modules/learning/evals/eval_runner.py` — runner pattern

## Implementation Steps

### Step 1: Create `evals/gold_set.py`

```python
@dataclass(frozen=True)
class BCTCGoldCase:
    case_id: str
    category: str
    ticker: str
    period: str
    line_item: str | None
    formula_id: str | None
    expected_value: float | None
    expected_unit: str | None
    expected_behavior: str  # "correct_value", "insufficient_data", "reject_recommendation"
    adversarial: bool = False

BCTC_GOLD_SET: tuple[BCTCGoldCase, ...] = (
    # 80-100 cases across 7 categories
    ...
)
```

### Step 2: Create `evals/eval_runner.py`

```python
class BCTCEvalRunner:
    def run(self, gold_set: Sequence[BCTCGoldCase]) -> BCTCEvalMetrics: ...

@dataclass
class BCTCEvalMetrics:
    total_cases: int
    grounded_rate: float      # claims with tool evidence / total claims
    numeric_accuracy: float   # correct value+unit / total numeric claims
    unsupported_claim_rate: float
    citation_coverage: float
    buy_sell_leak_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
```

### Step 3: Tests

- `test_gold_set_has_minimum_cases` — ≥80
- `test_gold_set_category_distribution` — all 7 categories present
- `test_eval_runner_computes_metrics` — smoke test on small subset

## Success Criteria

- [ ] Gold set has ≥80 cases across 7 categories
- [ ] Eval runner produces all required metrics
- [ ] Threshold config is versioned
- [ ] Threshold change makes test fail directionally
- [ ] ≥3 tests pass
