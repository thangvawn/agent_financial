# 10 — Internal Ops Agent Plan

> Owner đích: `src/risk_dashboard/modules/internal_ops/`
> Sources of truth: `modules/admin_cms`, `modules/analytics_monitoring`, `modules/trust_safety`; future `modules/agentic_core`
> Trạng thái: **greenfield orchestration trên live admin modules; chỉ draft/recommend**

## 0. Reality note

| Claim | Live reality đã verify | Hệ quả |
|---|---|---|
| Internal Ops | Chưa tồn tại/đăng ký; registry platform ở `src/risk_dashboard/app/registry/registry.py:36-62`; module contract ở `app/registry/module_definition.py:8-23` | Module mới, disabled mặc định |
| Agentic Core | Chưa tồn tại; doc 00 xác nhận greenfield (`docs/project/agentic-quantum/00_AGENTIC_CORE_PLAN.md:7-17`) | Run trace/eval tools block bởi AC6; không giả lập dữ liệu |
| Analytics | Live read KPI/events/ops/alerts và mutation jobs (`modules/analytics_monitoring/api/admin.py:57-156`) | Chỉ dùng read services tại lines 62-132; jobs forbidden |
| Trust | Live read audit/incidents; live open/action (`modules/trust_safety/api/admin.py:46-104`) | Chỉ read. Open/close/resolve/reassign incident forbidden |
| CMS | Live read và upsert/review/approve/publish/archive/rollback/AI draft (`modules/admin_cms/api/admin.py:69-277`) | Chỉ read + artifact draft riêng. Auto-publish forbidden |
| System surface | `/admin/load-panel` ghi global panel, không auth dependency (`modules/system_surface/api/admin.py:8-15`) | Không cấp tool |
| Admin auth | Static keys; CMS role lấy từ `X-Content-Ops-Role` (`admin_cms/api/admin.py:41-66`) | Không đủ RBAC. OPS1 block bởi ID1/ID2/ID6; header role không là authority |
| Existing schemas | Analytics event có integer version (`analytics_monitoring/schemas/requests.py:6-25`); trust/CMS requests chưa versioned (`trust_safety/schemas/requests.py:6-19`; `admin_cms/schemas/requests.py:6-31`) | Ops contracts dùng SemVer string `1.0.0`; adapter normalize, không sửa domain schemas |

## 1. Capability và hard boundaries

Internal Ops Agent tương quan evidence đã authorize để triage incident, freshness, failed run/eval và content QA. Output duy nhất: `OpsInvestigationReport` hoặc `OpsActionRecommendation`, luôn `draft`/non-executable.

Bất biến:

1. Model chỉ read, summarize, draft, recommend.
2. **Cấm** auto-publish; incident open/close/resolve/reassign; prompt/model/feature-flag/config/role/permission changes; analytics jobs.
3. Không shell, arbitrary SQL/log search, secrets, raw conversation/personal memory, data export hoặc `/admin/load-panel`.
4. Tool grant one-run, purpose/resource/time scoped; identity/scopes server-resolved.
5. Log/content là untrusted input. Verified fact tách hypothesis; mọi fact có evidence ref.

## 2. Data flow và failures

```text
operator credential
 → AuthPrincipal + purpose grant (doc 01 ID1/ID2/ID6)
 → POST /admin/internal-ops/investigations
 → policy authorize(scope, purpose, resource, expiry)
 → bounded read-only ToolGrant
 → live application read services
 → allowlist fields + redact
 → versioned EvidenceItem
 → AI Runtime structured generation (doc 02)
 → deterministic citation/forbidden-intent verifier
 → draft report + append-only access audit
```

Input: principal, purpose, bounded filters/refs/time range, domain records. Transform: authorize → fetch → redact → normalize → correlate → summarize → verify. Output: draft report/recommendations, references, hypotheses, limitations, expiry and privacy-safe audit metadata. Không domain mutation.

Failures: missing source → `source_unavailable` + `incomplete`; insufficient/expired grant → 403 before tool; timeout/budget → failed/partial redacted trace; invalid model schema → bounded repair rồi fail; forbidden intent → `policy_blocked`; uncertain redaction → omit/fail closed.

## 3. Exact paths, wiring, real imports

```text
src/risk_dashboard/modules/internal_ops/
├── module.py
├── api/admin.py
├── application/{investigation_service,policy,redaction,verifier}.py
├── domain/{contracts,tools}.py
├── infrastructure/adapters/{analytics,trust_safety,admin_cms,agentic_core}.py
├── infrastructure/sqlite.py
└── schemas/api.py
```

`module.py` imports `risk_dashboard.app.registry.module_definition.ModuleDefinition`; registry imports `risk_dashboard.modules.internal_ops.module.module` and mounts after `admin_cms_module` (`registry.py:42-50`). Definition:

```python
ModuleDefinition(
 id="internal_ops", slug="internal_ops", enabled_by_default=False,
 dependencies=("analytics_monitoring", "trust_safety", "admin_cms"),
 feature_flags=("module.internal_ops.enabled",),
 permission_scopes=("admin:internal_ops:investigate", "admin:internal_ops:content_read",
                    "admin:internal_ops:trust_read", "admin:internal_ops:report_read"),
 admin_router=admin_router, admin_mount_prefix="/admin",
)
```

Adapters call application services directly, never API loopback:

- `ListKpiSnapshots`, `ListAnalyticsEvents`, `ListOpsMetrics`, `ListAlerts` from `risk_dashboard.modules.analytics_monitoring.application.services` (live imports `analytics_monitoring/api/admin.py:7-18`).
- `ListTrustSafetyAudit`, `ListTrustIncidents` from `risk_dashboard.modules.trust_safety.application.services` (`trust_safety/api/admin.py:7-13`).
- `ListContent`, `GetContentDetail`, `ListContentVersions`, `ListReviewQueue`, `GetAnalyticsOverview`, `GetContentAnalytics` from `risk_dashboard.modules.admin_cms.application.services` (`admin_cms/api/admin.py:7-23`).
- SQLite repository types exactly as imported at analytics lines 19-21, trust line 14, CMS line 24; per-request instances, no mutable global operator state.
- Model layer imports only future `LLMProvider`, `ModelTask`, `ModelResult` frozen by AIR0/AIR1 (`docs/project/agentic-quantum/02_AI_RUNTIME_PLAN.md:47-113`), never provider SDK.
- Agentic Core adapter disabled until AC6 freezes application read-service imports.

## 4. Versioned schemas

All root/persisted/tool inputs and outputs use `schema_version: str = "1.0.0"`. Reject unknown major; additive minor fields require contract tests.

```python
class EvidenceRef(BaseModel):
 schema_version: str = "1.0.0"
 source_module: Literal["analytics_monitoring","trust_safety","admin_cms","agentic_core"]
 resource_type: str; resource_id: str; correlation_id: str | None = None; observed_at: str

class EvidenceItem(BaseModel):
 schema_version: str = "1.0.0"
 ref: EvidenceRef
 classification: Literal["aggregate","metadata","restricted_redacted"]
 fields: dict[str, Any]
 redactions: tuple[str, ...] = ()

class InvestigationRequest(BaseModel):
 schema_version: str = "1.0.0"
 investigation_type: Literal["incident","eval_regression","content_qa","data_freshness","run_failure"]
 purpose: str = Field(min_length=8, max_length=240)
 resource_refs: tuple[EvidenceRef, ...] = ()
 time_from: str; time_to: str
 max_evidence_items: int = Field(default=100, ge=1, le=500)

class VerifiedFinding(BaseModel):
 schema_version: str = "1.0.0"
 statement: str
 evidence_refs: tuple[EvidenceRef, ...] = Field(min_length=1)

class Hypothesis(BaseModel):
 schema_version: str = "1.0.0"
 statement: str
 confidence: float = Field(ge=0, le=1)
 supporting_refs: tuple[EvidenceRef, ...] = ()
 falsification_checks: tuple[str, ...] = ()

class OpsActionRecommendation(BaseModel):
 schema_version: str = "1.0.0"
 recommendation_id: str
 action_kind: Literal["content_draft_fix","runbook_step","owner_escalation","manual_check"]
 risk_class: Literal["proposal"] = "proposal"
 target_ref: EvidenceRef; rationale: str; payload_preview: dict[str, Any]
 status: Literal["draft"] = "draft"
 executable: Literal[False] = False

class OpsInvestigationReport(BaseModel):
 schema_version: str = "1.0.0"
 report_id: str; investigation_id: str
 status: Literal["draft","incomplete","policy_blocked","failed"]
 purpose: str; severity: Literal["info","low","medium","high","critical"]
 time_from: str; time_to: str
 verified_findings: tuple[VerifiedFinding, ...]
 hypotheses: tuple[Hypothesis, ...]
 recommendations: tuple[OpsActionRecommendation, ...]
 impacted_surfaces: tuple[str, ...]; limitations: tuple[str, ...]
 owner_hint: str | None; access_expires_at: str; created_at: str
```

Additive tables through existing migration/baseline pattern: `internal_ops_investigations`, `internal_ops_reports`, `internal_ops_access_audit`. Persist redacted normalized evidence refs, not raw payload. Audit append-only.

## 5. Endpoints: signatures, scopes, risk

All require server-resolved `AuthPrincipal` plus purpose grant. Static key may be temporary outer gate only.

| Method + exact path | Signature | Scope | Risk/effect |
|---|---|---|---|
| `POST /admin/internal-ops/investigations` | `(req: InvestigationRequest, principal: AuthPrincipal) -> OpsInvestigationReport` | investigate + each source read scope | `proposal`; draft report only |
| `GET /admin/internal-ops/investigations/{investigation_id}` | `(investigation_id: str, principal: AuthPrincipal) -> OpsInvestigationReport` | `admin:internal_ops:report_read` | `read`; purpose/expiry recheck |
| `GET /admin/internal-ops/investigations/{investigation_id}/evidence` | `(investigation_id: str, limit: int=100, principal: AuthPrincipal) -> list[EvidenceItem]` | report + original source scope | `read`; redacted, max 500 |
| `POST /admin/internal-ops/investigations/{investigation_id}/recommendations` | `(investigation_id: str, principal: AuthPrincipal) -> list[OpsActionRecommendation]` | investigate | `proposal`; non-executable |

Không có execute/confirm endpoint.

## 6. Typed tools

All follow `async execute(input, grant) -> output`; exact schema/version/risk checked before adapter.

| Tool@version | Input → output | Scope | Risk/backing |
|---|---|---|---|
| `ops.get_kpi_slice@1.0.0` | kpi/window → `EvidenceBatch` | analytics read | `read`; `ListKpiSnapshots.execute`, API `analytics_monitoring/api/admin.py:62-76` |
| `ops.get_analytics_events@1.0.0` | bounded filters/limit → batch | analytics read | `read`; lines 79-96 |
| `ops.get_source_health@1.0.0` | freshness/api_health/moderation → batch | analytics read | `read`; lines 112-124 |
| `ops.get_alert_context@1.0.0` | status? → batch | analytics read | `read`; lines 127-132 |
| `ops.get_trust_case@1.0.0` | bounded audit/incident filters → redacted batch | trust read + `safety_review` purpose | `read`; trust lines 51-84 |
| `ops.get_content_context@1.0.0` | content id/type → content/version/review evidence | content read | `read`; CMS lines 80-96,219-244 |
| `ops.get_run_trace@1.0.0` | run/correlation id → redacted trace | future agentic run read | `read`; disabled until AC6 |
| `ops.get_skill_eval_diff@1.0.0` | skill/version/cohort → aggregate diff | future eval read | `read`; disabled until eval store |
| `ops.propose_content_fix@1.0.0` | refs/rationale → recommendation | investigate | `proposal`; internal artifact only |
| `ops.publish_content` | n/a | none | `forbidden`; never registered; CMS live publish at lines 162-177 |
| `ops.change_incident_state` | n/a | none | `forbidden`; blocks trust lines 87-104 |
| `ops.change_prompt_model_flag_config` | n/a | none | `forbidden`; no proposal subtype |
| `ops.run_analytics_job` | n/a | none | `forbidden`; blocks analytics lines 135-156 |

## 7. Access and redaction

Target roles: `support_viewer` (aggregate/metadata), `content_operator` (+CMS read/drafts), `reliability_operator` (+health/future redacted run/eval), `trust_reviewer` (purpose-bound redacted cases), `security_admin` (approved/time-boxed break-glass; same forbidden ceiling).

Audit principal, scope snapshot, purpose, filters, tool/version, decision, timestamp, expiry. Raw prompts, secrets, tokens, user bodies, personal memory and unrestricted properties removed pre-model and pre-trace. Export disabled.

## 8. Ordered WPs: dependencies, ownership, acceptance, DoD

| # | WP | Blockers | Exclusive production files | Acceptance | DoD |
|---:|---|---|---|---|---|
| 1 | OPS0 Contracts freeze | none | `domain/contracts.py`, `schemas/api.py` | round-trip; unknown major rejected; forbidden actions cannot validate | schemas 1.0.0 + draft-only ADR |
| 2 | OPS1 RBAC/purpose | OPS0, ID1+ID2+ID6 | `application/policy.py` | role×scope×purpose×resource matrix; spoofed headers denied; expiry/break-glass pass | 100% gates; no client authority |
| 3 | OPS2 Adapters/redaction | OPS0-1 | adapter files, `application/redaction.py` | seeded sources normalize; secret/PII canaries absent; typed unavailable | only enumerated read imports; no mutations/API loopback/shell/DB tool |
| 4 | OPS3 Registry/grants | OPS1-2, AC2 alignment | `domain/tools.py` | one-run/resource/expiry grants; forbidden unresolved; tampered schema denied | versioned manifest + allow/deny/invoke audit |
| 5 | OPS4 Orchestration | OPS0-3, AIR0+AIR1, AC3 or approved bounded flow | `investigation_service.py`, `verifier.py` | fake provider seeded eval; uncited fact/forbidden intent rejected; partial source incomplete | offline deterministic, budgets enforced |
| 6 | OPS5 API/persistence/wiring | OPS1-4 | `api/admin.py`, `infrastructure/sqlite.py`, `module.py`, registry + migration/baseline | auth/expiry/IDOR/idempotency tests; duplicate request one report | four endpoints; disabled default; no raw persistence |
| 7 | OPS6 UI | OPS5 | future internal-ops frontend module/page/routes | alert→report E2E; forbidden controls absent; a11y | “Draft—human action required”; no execute controls |
| 8 | OPS7 Readiness | OPS5-6 | tests only | security/resilience/eval/kill-switch/break-glass drills | all quantitative gates pass + security sign-off |

No parallel WPs edit the same file. `get_run_trace`/eval remain unavailable until AC6.

## 9. Test matrix and success gates

- Unit: SemVer, redaction, policy, risk registry, severity, citation/intent verifier.
- Contract: every tool I/O 1.0.0, adapter normalization, malformed/oversized/unknown major, typed errors.
- Integration: principal→grant→adapter→evidence→report→audit; two principals/resources IDOR; expiry; unavailable source.
- Security: spoofed role, prompt injection in logs/content, secret canaries, escalation/replay, audit tamper, missing purpose.
- Resilience: SQLite/provider timeout, partial source, cancel, duplicate key, budget exhaustion, kill switch.
- Eval: evidence recall, unsupported claims, false causes, relevance, forbidden recommendations.
- E2E: alert/freshness/content→draft report; zero mutation; expired access denied.

Gates: forbidden execution/recommendation = 0; cross-resource or sensitive leakage = 0; 100% decisions audited; 100% verified findings cited; evidence recall ≥95%; unsupported claims ≤1%; false-cause ≤5%; p50 <5s/p95 <15s on seeded local sources; ≤$0.05/report.

## 10. Risks, compatibility, rollback

| Phase | Likelihood × impact | Mitigation |
|---|---|---|
| OPS1 static-header RBAC | High × Critical | hard block on ID1/2/6; deny default; never trust role header |
| OPS2 sensitive model payload | Medium × Critical | field allowlist, pre-model redaction, canaries, omit/fail closed |
| OPS3 mutation confusion | Medium × Critical | allowlisted imports; forbidden absent; static import tests |
| OPS4 hallucinated cause | High × High | cited facts, hypotheses, verifier, incomplete over invention |
| OPS5 retention leak | Medium × High | refs/redacted data only, TTL, append-only audit |
| OPS6 misleading UI authority | Medium × High | draft labels, no controls, DOM assertions |
| Break-glass bypass | Low × Critical | independent approval/reason/TTL/review; same forbidden ceiling |

Compatibility: existing analytics/trust/CMS APIs and headers unchanged. Internal Ops additive, disabled default, in-process reads only. Normalize legacy records on read; ambiguous mapping stays incomplete, never guessed.

Rollback: OPS0-4 disable/unregister package; no source mutation. OPS5 set `module.internal_ops.enabled=false`, revoke grants; additive tables inert (drop only reviewed backup-aware migration). OPS6 remove route/nav. Rollout kill switch blocks new runs, preserves immutable audit; no cascading source rollback.

## 11. Definition of Done

- Exact four endpoints, nine allowed/versioned tools, four explicitly forbidden classes enforced.
- All root/tool contracts carry `schema_version="1.0.0"`; imports resolve to exact live symbols above.
- Reports only draft/incomplete/blocked/failed; recommendation is `executable=False`.
- Auto-publish, incident mutations, prompt/model/flag/config/role changes, analytics jobs, shell, SQL/log search and raw memory impossible by registry + tests.
- Ordered acceptance, test matrix, SLO/quality/security gates, kill-switch and break-glass drills pass.

## 12. Open decisions

- Final role-scope map, break-glass approver, report/audit retention.
- Exact Agentic Core run/eval read symbols after AC6.
- OPS4 graph vs bounded single-specialist service after AC3 freeze.
- Allowed redacted trust fields by purpose/severity.

Open decisions may only tighten reads/retention. They cannot enable autonomous remediation or any forbidden action above.
