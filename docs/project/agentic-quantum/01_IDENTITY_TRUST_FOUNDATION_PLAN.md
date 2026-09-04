# 01 — Identity & Trust Foundation Plan

> Capability owners: `src/risk_dashboard/modules/auth`, `src/risk_dashboard/modules/trust_safety`
> Consumers: mọi agentic module
> Roadmap liên quan: AT0, AT2, AT4A, AT7
> Reality: **EXTEND, không greenfield** — `ResolveSession` + account/session model đã tồn tại (`modules/auth/application/services.py:163-187`); việc còn lại là emit typed `AuthPrincipal` và tắt client-supplied identity.

## 1. Capability

Foundation này bảo đảm mỗi agent run, memory, artifact và tool call được gắn với một canonical account, đúng entitlement, đúng consent và đúng resource ownership. Đây là blocker P0 trước durable memory hoặc cross-surface personalization.

## 2. Hiện trạng và vấn đề phải giải quyết

Auth module đã có nền server-side: `ResolveSession.execute(*, session_id) -> tuple[Account, AccountSession]` (`modules/auth/application/services.py:163-187`) validate session active/không hết hạn/account tồn tại và `touch` last-seen. Đây là điểm tựa để EXTEND, **không phải viết lại**.

Vấn đề còn lại:

- `GET /auth/me` nhận `session_id` từ **client query param** (`modules/auth/api/public.py:95-96`: `session_id: str = Query(...)`) — identity do client cung cấp, không phải server resolve từ cookie/credential. Đây là anti-pattern phải tắt trong compatibility window.
- `ResolveSession` trả `tuple[Account, AccountSession]` thô, chưa có typed `AuthPrincipal` mang `assurance`/`scopes` để downstream (entitlement, envelope) tiêu thụ an toàn.
- Nhiều surface khác còn nhận `session_id`/`user_id` trực tiếp; News còn anonymous behavior. Client-controlled identity dẫn tới IDOR / cross-account retrieval.

Mục tiêu: (1) bọc `ResolveSession` thành một FastAPI dependency emit typed `AuthPrincipal`; (2) chuyển identity nguồn từ client param sang server-resolved cookie/credential; (3) migrate từng agentic endpoint sang boundary đó.

## 3. Target contract

```text
credential/session cookie
  → ResolveSession
  → AuthPrincipal(account_id, session_id, assurance, scopes)
  → EntitlementPolicy(surface, capability)
  → ResourceOwnership(resource_ref)
  → ConsentSnapshot(memory, analytics, data-use policy version)
  → TrustedExecutionEnvelope
```

Các invariant:

- canonical `account_id` chỉ do server resolve;
- anonymous user có isolated ephemeral namespace, không durable semantic memory;
- mọi query cá nhân có `account_id` bắt buộc;
- resource ownership được kiểm tra lại lúc tool execution và action confirmation;
- consent có version, timestamp và purpose;
- admin role không mặc nhiên được đọc raw personal memory/conversation.

### 3.1. Contract schemas

Sống tại `src/risk_dashboard/modules/auth/schemas/principal.py` (style: `from __future__ import annotations`, `pydantic.BaseModel`/`Field`, giống `modules/auth/schemas/auth.py`). `AuthPrincipal` là output typed của `ResolveSession` dependency; `ConsentSnapshot` được doc 00 §5.1 (`TrustedExecutionEnvelope.consent`) tiêu thụ nguyên bản — freeze cùng version.

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class ConsentSnapshot(BaseModel):
    schema_version: str = "1.0.0"
    memory: bool = False            # user đồng ý durable memory
    analytics: bool = False         # user đồng ý analytics
    policy_version: str             # version chính sách đã đồng ý
    consented_at: str | None = None # ISO-8601 UTC, None nếu chưa consent

class AuthPrincipal(BaseModel):
    schema_version: str = "1.0.0"
    account_id: str                 # canonical, server-resolved từ ResolveSession — KHÔNG từ client
    session_id: str
    assurance: str = "session"      # "anonymous" | "session" | "recent_auth"
    scopes: tuple[str, ...] = ()    # entitlements, format {tier}:{module}:{action}
    is_anonymous: bool = False      # True → ephemeral namespace, no durable memory
    consent: ConsentSnapshot | None = None
    resolved_at: str                # ISO-8601 UTC, thời điểm resolve
```

Mapping từ nền hiện có: `ResolveSession.execute(*, session_id) -> tuple[Account, AccountSession]` (`services.py:163-187`) là nguồn `account_id`/`session_id`; ID1 bọc thành dependency emit `AuthPrincipal`, resolve `scopes` từ entitlement server-side và `assurance` theo recency của session. `recent_auth` yêu cầu re-auth gần đây (dùng cho sensitive action confirmation ở doc 00 §5.2). Client không bao giờ truyền `account_id`, `scopes` hay `assurance`.

## 4. Scope

Trong phạm vi:

- `AuthPrincipal`/`ResolveSession` dependency;
- account-scoped repository interface;
- entitlement and ownership policy;
- memory consent/preferences, export/delete;
- retention classification;
- audit/security events and privacy-safe support workflow;
- optional migration path từ bearer/local storage sang secure cookie.

Ngoài phạm vi:

- identity provider replacement;
- KYC/trading identity;
- unrestricted staff impersonation;
- collection of extra PII để “cải thiện personalization”.

## 5. API và policy đề xuất

Tất cả endpoint yêu cầu `AuthPrincipal` server-resolved (không nhận `account_id`/`session_id` từ client body/query). `account_id` lấy từ principal, không từ path/param. Đây là **user-facing REST endpoint**, không phải agent tool — `risk_class` (`read|proposal|confirmed_write|forbidden`) là taxonomy của tool call ở doc 00 §5.2; ở đây dùng cột `effect` cho ngữ nghĩa read/write/destructive.

| Method + path | Required scope | Effect | Ghi chú |
|---|---|---|---|
| `GET /api/me/agent-preferences` | `me:preferences:read` | read | trả preference hiện tại của principal |
| `PATCH /api/me/agent-preferences` | `me:preferences:write` | write | update memory mode / analytics opt-in; ghi `ConsentSnapshot` mới |
| `GET /api/me/agent-memory` | `me:memory:read` | read | list durable memory items của principal |
| `DELETE /api/me/agent-memory/{memory_id}` | `me:memory:delete` | destructive | xoá 1 item; ownership re-check `memory_id` thuộc principal |
| `DELETE /api/me/agent-memory` | `me:memory:delete` | destructive | xoá toàn bộ; deletion propagate qua index/cache theo SLA (ID7) |
| `POST /api/me/agent-data-export` | `me:data:export` | export | tạo export job; audit event, không đưa raw payload vào log |

Request của conversation/embedded run chỉ nhận surface, resource reference, question/action và idempotency; không nhận trusted user namespace.

Nếu dùng httpOnly cookie, phải thiết kế CSRF token, SameSite, rotation và logout invalidation. Nếu giữ bearer token trong pilot, phải khóa TTL, storage policy và XSS threat model.

## 6. Work packages

| ID | Work package | Deliverable | Exit evidence |
|---|---|---|---|
| ID0 | Identity inventory | map mọi endpoint nhận session/user identity | reviewed inventory |
| ID1 | Canonical principal | shared `ResolveSession` and `AuthPrincipal` | auth contract tests |
| ID2 | Ownership/entitlement | policies cho surface/resource/tool/action | IDOR test matrix |
| ID3 | Consent/retention | versioned preferences, memory mode, policy purpose | consent lifecycle tests |
| ID4 | User rights | list/edit/delete/export with deletion workflow | privacy E2E |
| ID5 | Session hardening | cookie/bearer decision, CSRF/XSS/session rotation | threat-model sign-off |
| ID6 | Operational access | break-glass/support policy and privacy-safe logs | access audit drill |
| ID7 | Data retention TTL spec | session token TTL, refresh rotation policy, audit log retention window | retention matrix approved + TTL expiry/rotation tests |

### 6.1. Acceptance test + Definition of Done per WP

| WP | Acceptance test | Definition of Done |
|---|---|---|
| ID0 | enumerate mọi endpoint nhận session/user identity; phân loại nguồn (server-resolved vs client-supplied); flag anti-pattern `/auth/me` nhận `session_id` qua `Query(...)` (`modules/auth/api/public.py:95-96`) | inventory table reviewed; mọi client-supplied identity site đánh dấu migrate target; 0 endpoint mới nhận `account_id`/`scopes` từ client |
| ID1 | `AuthPrincipal`/`ConsentSnapshot` round-trip Pydantic; principal **từ chối** client truyền `account_id`/`scopes` (server-resolved only); assurance downgrade khi session-only vs recent_auth | `modules/auth/schemas/principal.py` freeze `schema_version="1.0.0"`; `ResolveSession.execute(*, session_id) -> tuple[Account, AccountSession]` (`application/services.py:163-187`) là EXTEND point duy nhất phát principal; 0 endpoint tự parse identity |
| ID2 | IDOR matrix: account A không truy cập resource account B qua surface/resource/tool/action; tool `risk_class="forbidden"` không bao giờ authorize | ownership guard tập trung; mọi resource access check `principal.account_id`; risk-class enum (`read\|proposal\|confirmed_write\|forbidden`) enforce |
| ID3 | consent lifecycle: grant/revoke versioned; `consent.memory=false` → 0 memory write; `policy_version` mismatch → re-consent | `ConsentSnapshot` versioned (`policy_version`, `consented_at`); consent gate trước mọi memory/analytics side effect |
| ID4 | privacy E2E: list/edit/delete/export; deletion propagate qua store/index/cache; export chỉ own data | deletion workflow doc'd + SLA; rights API scoped tới `principal.account_id`; 0 cross-account leak |
| ID5 | threat-model: CSRF token enforce, session rotation sau re-auth/privilege change; client không spoof được session (đóng `/auth/me` `Query` anti-pattern trên authenticated path) | sign-off; `session_id` không còn nhận qua client `Query` trên authenticated path; cookie/bearer decision nhất quán |
| ID6 | access audit drill: break-glass logged, support access scoped + time-boxed; logs privacy-safe (0 secret/PII) | break-glass policy doc'd; audit log immutable; redaction enforce trước khi log |
| ID7 | TTL expiry test: session token quá TTL bị reject; refresh rotation hoạt động; audit log retention window enforce | retention matrix approved; TTL/rotation config từ trusted server config, **không** client-tunable |

## 7. Migration order

1. Tạo shared principal contract không phá API cũ.
2. Migrate AI Tutor/Learn endpoints đầu tiên.
3. Migrate BCTC and Simulation resources.
4. Migrate News, Market/Portfolio and Home.
5. Tắt client-provided authority fields sau compatibility window.
6. Backfill only identifiers that can be mapped deterministically; ambiguous records remain quarantined, never guessed.

## 8. Threat model và controls

| Threat | Control bắt buộc |
|---|---|
| Cross-user memory leak | account scope at repository + integration tests |
| IDOR on report/run/artifact | resource ownership check on read and execute |
| Session fixation/replay | rotation, TTL, revoke and recent-auth for sensitive confirm |
| CSRF | token/SameSite/origin validation when cookie-based |
| XSS token theft | CSP, sanitization, no long-lived token in local storage |
| Staff overreach | least privilege, break-glass reason, immutable audit |
| Deletion gaps | inventory of DB/index/cache/backup and deletion SLA |
| Consent drift | policy version pinned to run/memory event |

## 9. Tests và metrics

- Unit: entitlement/ownership/retention policies.
- Integration: every personal repository requires account scope.
- Security: cross-account matrix for conversation, memory, artifact, report, simulation and action.
- E2E: consent off → ephemeral chat; export; single-item delete; delete all.
- Metrics: unauthorized attempts, stale sessions, deletion SLA, export completion, memory opt-in rate.

Test dữ liệu phải có ít nhất hai accounts, cùng loại resource IDs và deliberately colliding external/session IDs.

## 10. Definition of Done

- Agent endpoints không tin `user_id`, namespace hoặc allowed tools từ client.
- Cross-account read/write/action suite có zero leakage.
- Memory preference and data-right APIs usable by UI.
- Retention map được owner/pháp lý sản phẩm duyệt.
- Session hardening decision có ADR và security tests.
- Không raw prompt/private payload xuất hiện trong standard application logs.

## 11. Open decisions

- Secure cookie hay opaque bearer cho production?
- Durable memory opt-in hay opt-out cho pilot?
- Deletion SLA và backup tombstone strategy?
- Instructor/operator được xem aggregate nào?
- Session token TTL value là bao nhiêu?
- Refresh rotation policy nào được áp dụng?
- Audit retention window (default 12 months) có được duyệt?

## 12. Validation checkpoint

Entry criteria:

- auth module inventory complete;
- canonical identity ADR done.

Exit criteria (quantitative):

- 100% endpoints resolve server-side identity;
- zero client-trusted `user_id`/`account_id`;
- session resolve p50 < 50ms, p95 < 150ms;
- audit log append-only verified.

Validation gate: maps to VP-AT0.
