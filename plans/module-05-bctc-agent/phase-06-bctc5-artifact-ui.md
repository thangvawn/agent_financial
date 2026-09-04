---
phase: 6
title: "BCTC5 — Artifact/UI (Evidence Memo)"
status: completed
priority: P2
effort: "6h"
dependencies: [4, 5]
---

# Phase 6: BCTC5 — Evidence Memo Artifact & UI

## Overview

Tạo evidence memo lifecycle (draft → reviewed → delivered → archived), source drawer UI, stale indicator khi revision thay đổi. Memo repository dùng additive migration. Frontend: evidence source drawer, keyboard-only, screen-reader labels.

## Requirements

### Functional

- `MemoService` class: create_memo, get_memo, mark_stale, archive_memo
- Memo table via additive migration (`010_bctc_evidence_memos`)
- Memo is snapshot có source refs — không thay thế report
- Revision đổi → memo hiện `is_stale = True`
- Frontend: source drawer hiện `source/fetched_at/revision_id` per evidence row
- Accessibility: keyboard-only navigation, aria-live, role attributes, focus restore

### Non-functional

- Deterministic BCTC UI vẫn dùng được khi agent off
- Migration additive theo `platform/database/migrate.py` convention

## Related Code Files

### Create

- `src/risk_dashboard/modules/financials_product/application/memo_service.py`
- `src/risk_dashboard/modules/financials_product/infrastructure/sqlite_memo_repository.py`
- `frontend/src/features/bctc/components/EvidenceSourceDrawer.jsx`
- `tests/test_bctc_memo_service.py`

### Modify

- `src/risk_dashboard/platform/database/migrate.py` — add migration `010_bctc_evidence_memos`
- `frontend/src/features/bctc/pages/BctcAnalysisWorkspace.jsx` — integrate evidence drawer

## Implementation Steps

### Step 1: Add migration `010_bctc_evidence_memos`

```sql
CREATE TABLE IF NOT EXISTS bctc_evidence_memos (
    memo_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    report_refs_json TEXT NOT NULL,
    scope TEXT NOT NULL,
    evidence_rows_json TEXT NOT NULL,
    calculations_json TEXT NOT NULL,
    interpretations_json TEXT NOT NULL,
    unresolved_questions_json TEXT NOT NULL,
    limitations_json TEXT NOT NULL,
    reviewer_status TEXT NOT NULL DEFAULT 'pending',
    is_stale INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bctc_memos_account ON bctc_evidence_memos(account_id);
```

### Step 2: Create `infrastructure/sqlite_memo_repository.py`

CRUD operations matching `BCTCEvidenceMemo` schema. Pattern: follow `SqliteLearningCheckpointRepository`.

### Step 3: Create `application/memo_service.py`

```python
class MemoService:
    def create_memo(self, *, account_id: str, subject: str, ...) -> BCTCEvidenceMemo: ...
    def get_memo(self, *, account_id: str, memo_id: str) -> BCTCEvidenceMemo: ...
    def mark_stale(self, *, memo_id: str) -> None: ...
    def check_staleness(self, *, memo_id: str, current_revision_id: str) -> bool: ...
    def archive_memo(self, *, account_id: str, memo_id: str) -> None: ...
```

### Step 4: Frontend — `EvidenceSourceDrawer.jsx`

- Collapsible drawer showing per-row: source, fetched_at, revision_id, period, currency
- Stale indicator badge when `is_stale`
- `aria-live="polite"` for stale notifications
- `role="complementary"` for drawer
- Keyboard: Escape closes, Tab navigates rows

### Step 5: Tests

- `test_create_and_get_memo`
- `test_staleness_detection` — revision change → is_stale=True
- `test_account_isolation` — account A cannot read account B's memo
- `test_archive_memo`

## Success Criteria

- [ ] Memo CRUD working with SQLite
- [ ] Revision change → memo marked stale
- [ ] Account A cannot access account B memo
- [ ] Migration additive (010)
- [ ] Frontend drawer shows source/fetched_at/revision_id
- [ ] Keyboard-only + screen-reader pass
- [ ] ≥4 tests pass
