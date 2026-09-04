---
phase: 1
title: "BCTC0 — Data Contract & Scopes"
status: completed
priority: P1
effort: "6h"
dependencies: []
---

# Phase 1: BCTC0 — Data Contract, Schemas & Permission Scopes

## Overview

Freeze root schemas (`ProvenanceRef`, `NumericValue`, tool I/O contracts), implement deterministic `revision_id` derivation, và mở rộng `module.py` permission scopes cho `bctc:*`. Đây là blocker cho mọi phase sau.

## Requirements

### Functional
- `ProvenanceRef` schema: `report_id`, `revision_id`, `period`, `source`, `fetched_at`, `statement`, `line_item`
- `NumericValue` schema: `value`, `unit` (VND|VND_bn|pct|x|ratio), `scale`, `calculation_status`, `provenance`
- 6 cặp Input/Output schemas (§5.1 trong plan doc) — tất cả Pydantic v2, frozen, `schema_version="1.0.0"`
- `BCTCEvidenceMemo` schema (§7): memo_id, subject, report_refs, evidence_rows, calculations, interpretations, unresolved_questions, limitations, reviewer_status, is_stale, expires_at
- Revision derivation: deterministic hash từ `source + fetched_at + period_set` → `revision_id`
- `NumericValue` thiếu `provenance` phải fail Pydantic validation
- Client-supplied `account_id` authority bị từ chối (server-resolved via `ResolveSession`)
- Permission scopes: thêm `bctc:report:read`, `bctc:formula:read`, `bctc:evidence:read` vào `module.py`

### Non-functional
- Cùng dataset → cùng `revision_id` (deterministic)
- `fetched_at` đổi → `revision_id` đổi
- Schema round-trip test pass cho mọi root schema

## Architecture

```
schemas/
├── agent_tools.py          # ProvenanceRef, NumericValue, 6×Input/Output
└── evidence.py             # BCTCEvidenceMemo, EvidenceRow

domain/
├── provenance.py           # derive_revision_id(), validate_freshness()
├── numeric_policy.py       # NumericValue validation rules
└── ports.py                # ReportReader, UploadOwnershipPort ABC
```

ProvenanceRef → gắn vào mọi NumericValue → NumericValue là atomic unit truyền qua mọi tool output.

## Related Code Files

### Create
- `src/risk_dashboard/modules/financials_product/schemas/__init__.py`
- `src/risk_dashboard/modules/financials_product/schemas/agent_tools.py`
- `src/risk_dashboard/modules/financials_product/schemas/evidence.py`
- `src/risk_dashboard/modules/financials_product/domain/__init__.py`
- `src/risk_dashboard/modules/financials_product/domain/provenance.py`
- `src/risk_dashboard/modules/financials_product/domain/numeric_policy.py`
- `src/risk_dashboard/modules/financials_product/domain/ports.py`

### Modify
- `src/risk_dashboard/modules/financials_product/module.py` — thêm bctc:* scopes

### Reference (READ ONLY)
- `src/risk_dashboard/modules/financials_product/api/public.py` — `_load_dataset_or_503()` (:769), `FinancialDataset` shape
- `src/risk_dashboard/schemas/financials.py` — `FinancialDataset` (:48-65), `FinancialPeriodData` (:11-45)
- `src/risk_dashboard/modules/learning/schemas/agent_tools.py` — pattern reference (Pydantic v2 conventions)

## Implementation Steps

### Step 1: Tạo `schemas/agent_tools.py`
Copy exact schema definitions từ §5.1 trong `05_BCTC_AGENT_PLAN.md`:
- `ProvenanceRef(BaseModel)` — frozen
- `NumericValue(BaseModel)` — `provenance` field bắt buộc (không Optional)
- `ResolveReportInput/Output`
- `ResolveLineItemInput/Output`
- `ComparePeriodsInput/Output` + `PeriodDelta`
- `CalculateRatioInput/Output`
- `TraceProvenanceInput/Output` + `TransformStep`
- `BuildEvidenceTableInput/Output` + `EvidenceRow`

**Invariant:** Mọi schema có `schema_version: str = "1.0.0"`. Không field nào chứa `correct_answer` hay sensitive data.

```python
from pydantic import BaseModel, Field
from typing import Literal

class ProvenanceRef(BaseModel):
    model_config = {"frozen": True}
    report_id: str
    revision_id: str
    period: str
    source: str
    fetched_at: str
    statement: Literal["income_statement", "balance_sheet", "cash_flow"] | None = None
    line_item: str | None = None

class NumericValue(BaseModel):
    model_config = {"frozen": True}
    value: float | None = None
    unit: Literal["VND", "VND_bn", "pct", "x", "ratio"]
    scale: int = Field(default=1, ge=1)
    calculation_status: Literal["ok", "insufficient_data"] = "ok"
    provenance: ProvenanceRef  # REQUIRED — không Optional
```

### Step 2: Tạo `schemas/evidence.py`
```python
class BCTCEvidenceMemo(BaseModel):
    model_config = {"frozen": True}
    schema_version: str = "1.0.0"
    memo_id: str
    subject: str
    report_refs: tuple[ProvenanceRef, ...]
    scope: str
    evidence_rows: tuple[EvidenceRow, ...]
    calculations: tuple[CalculateRatioOutput, ...]
    interpretations: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    limitations: tuple[str, ...]
    reviewer_status: Literal["pending", "approved", "rejected"]
    is_stale: bool
    expires_at: str
```

### Step 3: Tạo `domain/provenance.py`
```python
import hashlib

def derive_revision_id(source: str, fetched_at: str, periods: tuple[str, ...]) -> str:
    """Deterministic revision from source + time + period set."""
    canonical = f"{source}|{fetched_at}|{'|'.join(sorted(periods))}"
    return f"rev_{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"
```

### Step 4: Tạo `domain/ports.py`
```python
from abc import ABC, abstractmethod

class ReportReader(ABC):
    @abstractmethod
    def resolve_report(self, ticker: str, period: str | None = None, refresh: bool = False): ...

class UploadOwnershipPort(ABC):
    @abstractmethod
    def check_ownership(self, account_id: str, upload_id: str) -> bool: ...
```

### Step 5: Mở rộng `module.py`
```python
permission_scopes=(
    "public:financials:read",
    "public:financials:write",
    "bctc:report:read",
    "bctc:formula:read",
    "bctc:evidence:read",
),
```

### Step 6: Tạo contract tests
File: `tests/test_bctc_agent_contracts.py`
- Test round-trip cho mọi root schema
- Test `NumericValue` thiếu `provenance` → ValidationError
- Test `derive_revision_id` deterministic: same input → same output, different `fetched_at` → different output
- Test `ResolveReportOutput` serialize/deserialize

## Success Criteria

- [ ] Mọi root schema round-trip với `schema_version="1.0.0"`
- [ ] `NumericValue` thiếu `provenance` → Pydantic ValidationError
- [ ] Cùng dataset → cùng `revision_id`
- [ ] `fetched_at` đổi → `revision_id` đổi
- [ ] `module.py` có đủ `bctc:*` scopes
- [ ] Contract tests pass (≥8 tests)

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Schema break downstream tools | Freeze tại v1.0.0, add-only changes |
| `FinancialDataset` chưa có `revision_id` | Derive deterministic từ hash |
| Schema quá phức tạp | Follow exact spec từ plan doc §5.1, không thêm field |
