---
phase: 2
title: "BCTC1 — Read Tools (6 Adapters)"
status: completed
priority: P1
effort: "8h"
dependencies: [1]
---

# Phase 2: BCTC1 — Six Read-Only Tool Adapters

## Overview

Tạo 6 tool adapter classes bọc live compute hiện có (`_load_dataset_or_503`, `_calculated_ratio`, `_line_item_explanations`). Mỗi tool có `ToolManifest` với risk_class `read`. **Không** tạo loader mới — delegate về existing code.

## Requirements

### Functional
6 tools theo §5 của plan doc:

| Tool | Wrap target | Scope |
|---|---|---|
| `bctc.resolve_report` | `_load_dataset_or_503(ticker, refresh)` (`api/public.py:769`) | `bctc:report:read` |
| `bctc.resolve_line_item` | `FinancialPeriodData` fields + `_line_item_explanations()` (`:1165`) | `bctc:report:read` |
| `bctc.compare_periods` | `_income_formulas()` entries yoy/qoq (`:1147`) + trends route | `bctc:report:read` |
| `bctc.calculate_ratio` | `_calculated_ratio(numerator, denominator, formula_id, expression)` (`:929`) | `bctc:formula:read` |
| `bctc.trace_provenance` | `FinancialDataset.source/fetched_at/provider_notes` | `bctc:report:read` |
| `bctc.build_evidence_table` | `_build_financial_context(dataset)` (`:1297`) → typed rows | `bctc:evidence:read` |

### Non-functional
- Mọi output number có `ProvenanceRef` (invariant từ BCTC0)
- `calculate_ratio` với denominator 0/None → `calculation_status="insufficient_data"` (khớp `api/public.py:929`)
- Không tool nào nhận SQL/expression tự do
- p95 latency < 200ms per tool call

## Architecture

```
src/risk_dashboard/modules/financials_product/
├── agent_tools.py                    # 6 tool adapter classes + get_bctc_tool_manifests()
├── application/
│   └── report_resolver.py            # ReportResolver wraps _load_dataset_or_503
└── schemas/agent_tools.py            # (from BCTC0)
```

Pattern: follow Module 04 `learning/agent_tools.py` structure exactly.

Each adapter:
```python
class BctcResolveReportTool:
    manifest = ToolManifest(
        tool_id="bctc.resolve_report",
        risk_class="read",
        required_capabilities=("bctc:report:read",),
    )
    def execute(self, input: ResolveReportInput, *, account_id: str) -> ResolveReportOutput: ...
```

## Related Code Files

### Create
- `src/risk_dashboard/modules/financials_product/agent_tools.py`
- `src/risk_dashboard/modules/financials_product/application/report_resolver.py`
- `tests/test_bctc_agent_tools.py`

### Reference (READ ONLY — wrap, don't rewrite)
- `src/risk_dashboard/modules/financials_product/api/public.py`
  - `_load_dataset_or_503()` (line ~769)
  - `_calculated_ratio()` (line ~929)
  - `_income_formulas()` (line ~1147)
  - `_formula_by_id()` (line ~1159)
  - `_line_item_explanations()` (line ~1165)
  - `_build_financial_context()` (line ~1297)
- `src/risk_dashboard/schemas/financials.py` — `FinancialDataset`, `FinancialPeriodData`
- `src/risk_dashboard/data/financials.py` — `get_financial_dataset()`

### Pattern reference
- `src/risk_dashboard/modules/learning/agent_tools.py` — exact adapter pattern to follow

## Implementation Steps

### Step 1: Tạo `application/report_resolver.py`
Wrap `_load_dataset_or_503` thành clean service:
```python
class ReportResolver:
    def resolve(self, ticker: str, period: str | None = None, refresh: bool = False) -> ResolveReportOutput:
        dataset = _load_dataset_or_503(ticker, refresh=refresh)
        # derive revision_id from BCTC0's derive_revision_id()
        # map FinancialDataset → ResolveReportOutput
        # compute freshness_days from fetched_at
```

**Critical:** Import `_load_dataset_or_503` hoặc `get_financial_dataset` — KHÔNG viết loader mới.

### Step 2: Tạo `agent_tools.py` với 6 adapter classes

Mỗi adapter class:
1. Has `manifest: ToolManifest` class attribute
2. Has `execute(self, input: XxxInput, *, account_id: str) -> XxxOutput` method
3. Delegates to existing compute, wraps result in typed output with `ProvenanceRef`
4. Never exposes SQL, raw expression, or upload path

```python
class BctcResolveReportTool:
    manifest = ToolManifest(...)
    def execute(self, input: ResolveReportInput, *, account_id: str) -> ResolveReportOutput: ...

class BctcResolveLineItemTool:
    manifest = ToolManifest(...)
    def execute(self, input: ResolveLineItemInput, *, account_id: str) -> ResolveLineItemOutput: ...

class BctcComparePeriodsTool:
    manifest = ToolManifest(...)
    def execute(self, input: ComparePeriodsInput, *, account_id: str) -> ComparePeriodsOutput: ...

class BctcCalculateRatioTool:
    manifest = ToolManifest(...)
    def execute(self, input: CalculateRatioInput, *, account_id: str) -> CalculateRatioOutput: ...

class BctcTraceProvenanceTool:
    manifest = ToolManifest(...)
    def execute(self, input: TraceProvenanceInput, *, account_id: str) -> TraceProvenanceOutput: ...

class BctcBuildEvidenceTableTool:
    manifest = ToolManifest(...)
    def execute(self, input: BuildEvidenceTableInput, *, account_id: str) -> BuildEvidenceTableOutput: ...

def get_bctc_tool_manifests() -> list[ToolManifest]:
    return [cls.manifest for cls in (
        BctcResolveReportTool, BctcResolveLineItemTool,
        BctcComparePeriodsTool, BctcCalculateRatioTool,
        BctcTraceProvenanceTool, BctcBuildEvidenceTableTool,
    )]
```

### Step 3: Implement `calculate_ratio` logic
```python
def execute(self, input: CalculateRatioInput, *, account_id: str) -> CalculateRatioOutput:
    # 1. Resolve dataset via ReportResolver
    # 2. Lookup formula from _formula_by_id(input.formula_id)
    # 3. Extract numerator/denominator from dataset period data
    # 4. Call _calculated_ratio(numerator, denominator, formula_id, expression)
    # 5. If denominator is 0/None → calculation_status="insufficient_data"
    # 6. Wrap in NumericValue with ProvenanceRef
    # 7. Return CalculateRatioOutput
```

### Step 4: Tạo tests
File: `tests/test_bctc_agent_tools.py`
- `test_manifest_registration()` — 6 manifests, correct tool_ids
- `test_resolve_report_tool()` — returns valid output with revision_id, available_periods
- `test_resolve_line_item_tool()` — returns amount with ProvenanceRef
- `test_calculate_ratio_denominator_zero()` — returns `calculation_status="insufficient_data"`
- `test_calculate_ratio_valid()` — returns correct value with formula_id, expression
- `test_compare_periods_tool()` — returns deltas with pct_change
- `test_trace_provenance_tool()` — returns citations chain
- `test_build_evidence_table_tool()` — returns typed EvidenceRows
- `test_all_outputs_have_provenance()` — check every NumericValue in output has provenance

## Success Criteria

- [ ] 6 adapters chạy trên live dataset
- [ ] `calculate_ratio` với denominator 0/None → `calculation_status="insufficient_data"`
- [ ] Mọi output NumericValue có `ProvenanceRef`
- [ ] Không tool nào nhận SQL/expression tự do
- [ ] `get_bctc_tool_manifests()` returns 6 manifests
- [ ] ≥9 tests pass
- [ ] Zero duplicate compute logic — tools delegate về existing functions

## Risk Assessment

| Risk | Mitigation |
|---|---|
| `api/public.py` helpers are private (_prefixed) | Import from same package; or extract to application service |
| Dataset may be unavailable | Return typed failure, not crash |
| Formula lookup may fail | Return `calculation_status="insufficient_data"` |
