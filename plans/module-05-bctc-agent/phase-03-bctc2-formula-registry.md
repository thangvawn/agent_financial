---
phase: 3
title: "BCTC2 — Formula Registry"
status: completed
priority: P1
effort: "4h"
dependencies: [1]
---

# Phase 3: BCTC2 — Versioned Formula Registry

## Overview

Nâng `_income_formulas()` (`api/public.py:1147`) từ 7 hardcoded entries thành versioned registry có `unit`, `applicability`, `limitations`, `version` và approval state. `calculate_ratio` chỉ nhận `formula_id` đã approved.

## Requirements

### Functional

- Migrate 7 formula hiện hữu: `gross_profit`, `gross_margin`, `operating_margin`, `net_margin`, `yoy_growth`, `qoq_growth`, `cost_to_revenue_ratio`
- Mỗi formula entry có: `formula_id`, `version`, `expression`, `unit`, `applicability`, `limitations`, `approved`, `approved_by`, `approved_at`
- `formula_id` không tồn tại hoặc chưa approved → reject với typed error
- Unapproved version không resolve được
- `_income_formulas()` (`api/public.py:1147`) đọc từ registry thay vì hardcode
- ≥5 ratios có approval record

### Non-functional

- Registry là single source of truth cho formulas
- Version bump không break existing callers

## Related Code Files

### Create

- `src/risk_dashboard/modules/financials_product/domain/formula_registry.py`
- `tests/test_bctc_formula_registry.py`

### Modify

- `src/risk_dashboard/modules/financials_product/api/public.py` — `_income_formulas()` reads from registry

### Reference

- `src/risk_dashboard/modules/financials_product/api/public.py:1147` — current hardcoded formulas
- `src/risk_dashboard/modules/financials_product/api/public.py:929` — `_calculated_ratio()`

## Implementation Steps

### Step 1: Define `FormulaEntry` dataclass

```python
@dataclass(frozen=True)
class FormulaEntry:
    formula_id: str
    version: str           # e.g. "1.0.0"
    display_name: str
    expression: str        # e.g. "gross_profit / revenue"
    unit: str              # e.g. "pct", "VND", "ratio"
    applicability: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    approved: bool = False
    approved_by: str | None = None
    approved_at: str | None = None
```

### Step 2: Create registry with 7 formulas

```python
_FORMULA_REGISTRY: dict[str, FormulaEntry] = {
    "gross_profit": FormulaEntry(
        formula_id="gross_profit",
        version="1.0.0",
        display_name="Lợi nhuận gộp",
        expression="revenue - cost_of_goods_sold",
        unit="VND",
        applicability=("income_statement",),
        limitations=("Không bao gồm chi phí bán hàng và quản lý",),
        approved=True,
        approved_by="domain_expert",
        approved_at="2026-09-01T00:00:00Z",
    ),
    # ... 6 more formulas
}

def get_formula(formula_id: str, version: str | None = None) -> FormulaEntry:
    """Return approved formula or raise ValueError."""
    entry = _FORMULA_REGISTRY.get(formula_id)
    if entry is None:
        raise ValueError(f"Formula '{formula_id}' not found in registry.")
    if not entry.approved:
        raise ValueError(f"Formula '{formula_id}' is not approved.")
    if version and entry.version != version:
        raise ValueError(f"Formula '{formula_id}' version mismatch.")
    return entry

def list_approved_formulas() -> list[FormulaEntry]:
    return [f for f in _FORMULA_REGISTRY.values() if f.approved]
```

### Step 3: Wire `_income_formulas()` to registry

Modify `api/public.py:_income_formulas()` to delegate to `get_formula()` / `list_approved_formulas()`.

### Step 4: Write tests

- `test_registry_has_7_formulas`
- `test_get_approved_formula`
- `test_get_unapproved_raises`
- `test_get_nonexistent_raises`
- `test_version_mismatch_raises`
- `test_list_approved_returns_at_least_5`

## Success Criteria

- [ ] 7 formula entries migrated with version/unit/applicability/limitations
- [ ] `formula_id` not found → ValueError
- [ ] Unapproved formula → ValueError
- [ ] ≥5 ratios have approval record
- [ ] `_income_formulas()` reads from registry
- [ ] ≥6 tests pass
