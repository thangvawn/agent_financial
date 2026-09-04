---
phase: 7
title: "BCTC6 — Private Data Controls"
status: completed
priority: P1
effort: "5h"
dependencies: [1]
---

# Phase 7: BCTC6 — Private Data Controls (IDOR Blocker)

## Overview

Thêm account ownership cho private uploads (`/financials/upload`, `/uploads/{upload_id}/analyze`). **Đây là IDOR blocker — phải xong trước khi private upload path lộ ra agent.** Path traversal blocking, retention policy, redaction policy.

## Requirements

### Functional

- Account A KHÔNG resolve được `upload_id` của account B (IDOR test)
- Upload binding qua `upload_ownership_repository.py`
- `RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR` path traversal blocked
- Private report content KHÔNG xuất hiện trong durable memory
- Log KHÔNG chứa payload
- Retention: uploads có expiry, cleanup job xóa đúng hạn

### Non-functional

- Security test: IDOR, path traversal, log leakage
- This phase is a HARD BLOCKER for any agent access to private uploads

## Related Code Files

### Create

- `src/risk_dashboard/modules/financials_product/infrastructure/upload_ownership_repository.py`
- `tests/test_bctc_private_data_controls.py`

### Modify

- `src/risk_dashboard/modules/financials_product/api/public.py` — `/financials/upload` (:315), `/uploads/{upload_id}/analyze` (:387) add ownership check
- `src/risk_dashboard/platform/database/migrate.py` — add migration for upload_ownership table

### Reference

- `src/risk_dashboard/modules/financials_product/api/public.py:315` — upload endpoint
- `src/risk_dashboard/modules/financials_product/api/public.py:387` — analyze endpoint
- `RISK_DASHBOARD_FINANCIAL_UPLOADS_DIR` env var

## Implementation Steps

### Step 1: Migration for upload ownership

```sql
CREATE TABLE IF NOT EXISTS bctc_upload_ownership (
    upload_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    upload_path TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_upload_owner ON bctc_upload_ownership(account_id);
```

### Step 2: `upload_ownership_repository.py`

```python
class UploadOwnershipRepository:
    def bind_upload(self, upload_id: str, account_id: str, filename: str, upload_path: str) -> None: ...
    def check_ownership(self, upload_id: str, account_id: str) -> bool: ...
    def get_upload(self, upload_id: str, account_id: str) -> UploadRecord | None: ...
    def delete_expired(self) -> int: ...
```

### Step 3: Path traversal protection

```python
def validate_upload_path(upload_id: str, base_dir: str) -> str:
    """Resolve upload path, reject traversal attempts."""
    safe_path = os.path.join(base_dir, upload_id)
    real_path = os.path.realpath(safe_path)
    if not real_path.startswith(os.path.realpath(base_dir)):
        raise PermissionError("Path traversal detected")
    return real_path
```

### Step 4: Wire into upload/analyze endpoints

Modify `/financials/upload` and `/uploads/{upload_id}/analyze` to:
1. Resolve `account_id` from session (server-side)
2. `bind_upload()` on upload
3. `check_ownership()` before analyze
4. Reject with 403 if mismatch

### Step 5: Security tests

```python
def test_idor_cross_account_rejected():
    """Account A uploads, account B tries to analyze → 403."""

def test_path_traversal_blocked():
    """upload_id='../../../etc/passwd' → PermissionError."""

def test_expired_upload_cleanup():
    """Expired uploads cleaned by retention job."""

def test_private_content_not_in_memory():
    """Agent memory proposals don't contain private report content."""
```

## Success Criteria

- [ ] Account A cannot resolve upload_id of account B
- [ ] Path traversal (../) → PermissionError
- [ ] Expired uploads cleaned
- [ ] Private report content not in durable memory
- [ ] Log does not contain upload payload
- [ ] ≥4 security tests pass
