# Module 12 — Legacy Reactivation Gates Framework

## Prompt thực thi (điều chỉnh theo khảo sát codebase)

---

## Context (verified from codebase survey)

Module 12 is a GATE/GOVERNANCE module, NOT an agent-building spec. It governs
4 legacy modules currently archived/hold/retired:

```
LEGACY_MODULES = ("community", "goals", "financial_health", "guided_investing")
(src/risk_dashboard/app/registry/product_domains.py:74-79)
```

Registry state (`src/risk_dashboard/app/registry/registry.py`):
- `goals`, `financial_health`, `community`: UNMOUNTED (not in `get_registered_modules()`)
- `guided_investing`: MOUNTED at line 68 but `enabled_by_default=False`
- All 4 `module.py` files: `enabled_by_default=False`, `public_mount_prefix="/api/v1/public"`

Baseline test gap (VERIFIED — run `.venv/bin/python -m pytest tests/test_goals.py tests/test_financial_health.py tests/test_community.py tests/test_guided_investing.py`):
- 10 tests exist but 100% FAIL with 404 Not Found
- Root cause: routers unmounted from app registry → HTTP-level tests cannot pass
- This violates §10 exit criteria: "100% legacy behavior covered by baseline tests"

Identity debt (VERIFIED):
- `goals/api/public.py:59` — `list_goals(session_id: str = Query(...))` takes session_id from client
- Same pattern in `financial_health`, `community`, `guided_investing`
- Violates Module 01 P0: server-resolved `AuthPrincipal` (`account_id`)
- Module 12 RECORDS this debt in baseline reports. It does NOT fix it (that's GOAL1/FH1 work packages).

## Core Principle

Module 12 builds the **GATE INFRASTRUCTURE**. It does NOT reactivate any legacy module. Reactivation is a separate future action gated by this framework.

---

## Deliverable 1: Baseline Test Suites (capture current behavior WITHOUT HTTP)

Because routers are unmounted, baseline tests MUST exercise domain/service/schema
layers directly — NOT through `TestClient` HTTP. This captures legacy behavior without
violating the gate (no remount = no reactivation).

### `tests/modules/goals/test_baseline.py`

Import domain entities, policies, and application services directly:

```python
"""Baseline regression tests for legacy goals module.
Captures current behavior WITHOUT HTTP (router unmounted).
Serves as behavioral contract that must not regress before reactivation."""

from risk_dashboard.modules.goals.domain.entities import Goal, utc_now_iso
from risk_dashboard.modules.goals.domain.policies import (
    apply_checkin,
    build_planner_reply,
    build_reminder_state,
    build_snapshot,
    create_goal,
)
from risk_dashboard.modules.goals.schemas.requests import GoalCreateRequest
from risk_dashboard.modules.goals.schemas.responses import GoalResponse, GoalSummaryResponse


def _make_goal(**overrides):
    base = dict(
        user_id="session-baseline-001",
        goal_type="emergency_fund",
        goal_name="Quy du phong",
        target_amount=20000000.0,
        current_amount=2000000.0,
        currency="VND",
        base_currency="VND",
        deadline="2027-01-31",
        priority="high",
        confidence_level="estimated",
    )
    base.update(overrides)
    return create_goal(**base)


class TestGoalsBaseline:
    def test_create_goal_entity(self):
        goal = _make_goal()
        assert goal.goal_id
        assert goal.user_id == "session-baseline-001"
        assert goal.status == "active"

    def test_build_snapshot_metrics(self):
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        assert snap.gap_amount == 18000000.0
        assert snap.monthly_contribution_needed > 0
        assert snap.feasibility_band in {"on_track", "stretch", "high_stress", "not_feasible_yet"}
        assert snap.inflation_sensitivity_band == "medium"  # emergency_fund default
        assert snap.fx_sensitivity_band == "low"  # VND/VND

    def test_apply_checkin_completes_goal(self):
        goal = _make_goal(current_amount=20000000.0)
        updated = apply_checkin(goal, current_amount=20000000.0)
        assert updated.status == "completed"

    def test_build_planner_reply(self):
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        reply = build_planner_reply(goal, snap, financial_health=None)
        assert reply.summary
        assert reply.trade_offs
        assert reply.next_steps

    def test_build_reminder_state(self):
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        state = build_reminder_state(goal, snap)
        assert state.reminder_frequency in {"weekly", "biweekly", "monthly"}
        assert state.next_reminder_at

    def test_goal_create_request_schema(self):
        req = GoalCreateRequest(
            session_id="session-baseline-001",
            goal_type="emergency_fund",
            goal_name="Test",
            deadline="2027-01-31",
            target_amount=10000000,
            current_amount=0,
            priority="high",
            currency="VND",
            base_currency="VND",
            confidence_level="estimated",
        )
        assert req.session_id == "session-baseline-001"

    def test_goal_response_schema_roundtrip(self):
        goal = _make_goal()
        snap = build_snapshot(goal, financial_health=None)
        resp = GoalResponse.model_validate({...})  # map entity fields
        assert resp.goal_id == goal.goal_id

    def test_goal_entity_extra_forbid(self):
        # Pydantic v2: unknown field rejected
        ...

    def test_goal_type_defaults(self):
        # emergency_fund -> ("medium", "cashflow-basics-101")
        ...
```

### `tests/modules/financial_health/test_baseline.py`

Same pattern — import domain policies directly:
- `calculate_health_score` / assessment policy (8 subscores, 0-100)
- `guided_investing_eligible` flag derivation
- `build_coach_reply` (summary, explanation, next_small_actions)
- Schema roundtrips (FinancialHealthAssessmentRequest, FinancialHealthSnapshotResponse)
- Compliance note / transparency note presence

### `tests/modules/community/test_baseline.py`

Same pattern — import domain/services directly:
- Space membership policy
- Post moderation status derivation (published / blocked / held_for_review)
- Risk label detection (pump_and_dump)
- Notification state transitions (read / dismissed)
- Schema roundtrips

### `tests/modules/guided_investing/test_baseline.py`

Same pattern:
- Eligibility derivation (`guided_investing_eligible`)
- Watchlist item policy
- Portfolio review warnings (stress_case)
- Safe-chat guardrail (`allowed=False` for "Ma nao nen mua?")
- Schema roundtrips

Each baseline file: 8-12 tests, ALL PASS without HTTP. Target: ~40 baseline tests total.

---

## Deliverable 2: Gate Registry Module

### `src/risk_dashboard/modules/legacy_gate/`

#### `module.py`

```python
from risk_dashboard.app.registry.module_definition import ModuleDefinition
from risk_dashboard.modules.legacy_gate.api.public import router as public_router

module = ModuleDefinition(
    id="legacy_gate",
    slug="legacy_gate",
    enabled_by_default=True,  # Gate must always be active
    dependencies=(),
    feature_flags=("module.legacy_gate.enabled",),
    permission_scopes=("public:legacy_gate:read",),
    public_router=public_router,
    public_mount_prefix="/api/v1/public",
)
```

#### `domain/entities.py`

Pydantic v2 models, all `extra="forbid"`:

- `GateCategory` Literal: `"product"` | `"data"` | `"security"` | `"regulatory"` | `"maintenance"`
- `GateItemStatus` Literal: `"pending"` | `"passed"` | `"failed"` | `"waived"`
- `GateOverallStatus` Literal: `"hold"` | `"baseline_captured"` | `"gates_documented"` | `"decision_recorded"` | `"approved"` | `"reactivated"`
- `GateCheckItem`: gate_id, category, description, status, evidence_ref, approver, notes
- `ReactivationDecisionRecord`: record_id, module_slug, schema_version="1.0.0", outcome, owner_product, owner_engineering, owner_domain, owner_compliance, source_of_truth, risk_class, allowed_actions, dependencies, eval_criteria, rollout, adr_reference, status, created_at, updated_at
- `LegacyModuleBaselineReport`: module_slug, schema_version="1.0.0", entities_defined, policies_defined, services_defined, schemas_defined, routes_defined, tests_count, test_files, archived_reason, archived_phase, captured_at, **identity_debt_notes** (NEW — records session_id→account_id debt)
- `ModuleGateStatus`: module_slug, overall_status, gates, baseline, decision_record, total_gates, passed_gates, failed_gates, pending_gates, updated_at

#### `domain/errors.py`

`LegacyGateError` with Literal error_type: `"module_not_found"` | `"gate_not_ready"` | `"missing_baseline"` | `"decision_required"` | `"approval_required"` | `"already_reactivated"`

#### `domain/ports.py`

Protocols: `GateRepositoryPort`, `BaselineReporterPort`, `GateEvaluatorPort`

#### `schemas/gates.py`

Request/response models mirroring entities.

#### `application/evaluators.py`

Gate checklists per module. Each module: 8 common gates (§2) + module-specific (§3-§6):

```python
COMMON_GATES = (
    GateCheckItem(gate_id="{slug}-1", category="product", description="Product owner and target user/outcome defined"),
    GateCheckItem(gate_id="{slug}-2", category="data", description="Source of truth, API, data ownership, maintainer confirmed"),
    GateCheckItem(gate_id="{slug}-3", category="maintenance", description="Archived reason resolved via ADR"),
    GateCheckItem(gate_id="{slug}-4", category="security", description="Auth/account migration and retention complete"),
    GateCheckItem(gate_id="{slug}-5", category="regulatory", description="Regulatory/advisory boundary reviewed"),
    GateCheckItem(gate_id="{slug}-6", category="maintenance", description="Deterministic service/tool baseline passes tests"),
    GateCheckItem(gate_id="{slug}-7", category="security", description="Gold set, threat model, feature flag, rollout/rollback exist"),
    GateCheckItem(gate_id="{slug}-8", category="product", description="No P0/P1 roadmap degradation"),
)

GOALS_SPECIFIC = (
    GateCheckItem(gate_id="goals-9", category="product", description="Goal taxonomy and explicit user consent defined"),
    GateCheckItem(gate_id="goals-10", category="product", description="Goal correction/delete/export supported"),
    GateCheckItem(gate_id="goals-11", category="security", description="No inference of sensitive wealth/income from conversation"),
    GateCheckItem(gate_id="goals-12", category="product", description="Deterministic eligibility and next-step plan"),
    GateCheckItem(gate_id="goals-13", category="regulatory", description="Education goal separated from regulated advice"),
    GateCheckItem(gate_id="goals-14", category="product", description="Home integration only via compact summary"),
)

FH_SPECIFIC = (
    GateCheckItem(gate_id="fh-9", category="security", description="Field-level redaction before AI context"),
    GateCheckItem(gate_id="fh-10", category="regulatory", description="High-stakes disclaimer and escalation policy"),
    GateCheckItem(gate_id="fh-11", category="security", description="No inferred wealth profile written to durable memory"),
    GateCheckItem(gate_id="fh-12", category="product", description="Read-only explanation focus (no mutation without consent)"),
)

COM_SPECIFIC = (
    GateCheckItem(gate_id="com-9", category="security", description="Community content treated as untrusted data source"),
    GateCheckItem(gate_id="com-10", category="security", description="Stored prompt injection defense (content isolation)"),
    GateCheckItem(gate_id="com-11", category="product", description="No autonomous posting / no user impersonation"),
    GateCheckItem(gate_id="com-12", category="product", description="Moderated read-only summary only"),
)

GI_SPECIFIC = (
    GateCheckItem(gate_id="gi-9", category="regulatory", description="Legal review: Securities Law 2019 advisory boundary"),
    GateCheckItem(gate_id="gi-10", category="product", description="Education-only scope on paper portfolio"),
    GateCheckItem(gate_id="gi-11", category="security", description="No broker connection / no real order placement"),
    GateCheckItem(gate_id="gi-12", category="product", description="Explicitly approved pilot required"),
)

EVALUATORS = {
    "goals": COMMON_GATES + GOALS_SPECIFIC,           # 14 gates
    "financial_health": COMMON_GATES + FH_SPECIFIC,   # 12 gates
    "community": COMMON_GATES + COM_SPECIFIC,         # 12 gates
    "guided_investing": COMMON_GATES + GI_SPECIFIC,   # 12 gates
}
```

`build_baseline_report(module_slug)` — scans module package via importlib:
- `entities.py` / `policies.py` / `services.py` / `schemas/` / `api/public.py` existence
- counts baseline test files in `tests/modules/{slug}/`
- reads `ARCHIVE.md` for reason + phase
- records `identity_debt_notes` (session_id usage in `api/public.py`)

#### `application/service.py`

```python
class LegacyGateService:
    MODULES = ("goals", "financial_health", "community", "guided_investing")

    def list_modules(self) -> tuple[ModuleGateStatus, ...]
    def get_module_status(self, module_slug: str) -> ModuleGateStatus
    def initialize_module(self, module_slug: str) -> ModuleGateStatus  # idempotent
    def evaluate_module(self, module_slug: str) -> ModuleGateStatus
    def record_decision(self, module_slug: str, decision) -> ReactivationDecisionRecord
```

Overall status derivation:
- `hold` → default
- `baseline_captured` → baseline exists + tests pass
- `gates_documented` → all gates defined
- `decision_recorded` → decision record exists
- `approved` → all gates pass + decision approved
- `reactivated` → NEVER set by gate module (external action only)

#### `infrastructure/in_memory.py`

Thread-safe `OrderedDict` store (`RLock` pattern from `quant_research/api/public.py`).

#### `api/public.py`

Routes (auth via `resolve_principal` + scope check, same as `quant_research`):

- `GET  /api/legacy-gates/modules`
- `GET  /api/legacy-gates/modules/{slug}`
- `POST /api/legacy-gates/modules/{slug}/evaluate`
- `POST /api/legacy-gates/modules/{slug}/decisions`
- `GET  /api/legacy-gates/modules/{slug}/baseline`

---

## Deliverable 3: Registry Wiring

### `src/risk_dashboard/app/registry/registry.py`

Add import + mount `legacy_gate_module` in platform section (after `system_surface_module`).

### `src/risk_dashboard/app/registry/product_domains.py`

Add `"legacy_gate"` to `PLATFORM_MODULES` tuple.

---

## Deliverable 4: Gate Tests

### `tests/modules/legacy_gate/test_schemas.py` (~10 tests)

Roundtrips, `extra_forbid`, Literal constraints, `schema_version` defaults.

### `tests/modules/legacy_gate/test_gate_service.py` (~13 tests)

- list returns 4 modules
- initialize idempotent
- baseline captured with identity_debt_notes
- evaluate before init fails
- overall status derivation chain
- record decision requires documented gates
- module_not_found error
- gate counts: goals=14, fh=12, community=12, gi=12
- guided_investing includes regulatory/legal gates

### `tests/modules/legacy_gate/test_api.py` (~10 tests)

- endpoints return correct status codes
- auth required (401)
- scope check (403)
- feature flag disabled → 404
- invalid slug → 404

---

## Implementation Order

1. Baseline test suites (4 files, ~40 tests) — capture behavior FIRST
2. `legacy_gate` domain (entities, errors, ports)
3. `schemas/gates.py`
4. `evaluators.py` (gate checklists + baseline reporter)
5. `service.py`
6. `in_memory.py`
7. `api/public.py`
8. `module.py`
9. Registry wiring
10. Gate tests (~33 tests)
11. Full suite run — verify no regression (Module 11's 59 tests must still pass)

---

## Validation Criteria

1. `.venv/bin/python -m pytest tests/modules/goals/test_baseline.py tests/modules/financial_health/test_baseline.py tests/modules/community/test_baseline.py tests/modules/guided_investing/test_baseline.py -v` → ALL PASS (no HTTP dependency)
2. `.venv/bin/python -m pytest tests/modules/legacy_gate/ -v` → ALL PASS
3. Full suite: Module 11's 59 tests + new tests all pass
4. `legacy_gate` module registered with `enabled_by_default=True`
5. Legacy modules remain unmounted/disabled — NO reactivation
6. Baseline reports record `identity_debt_notes` (session_id usage)
7. Gate evaluation correctly identifies 4 legacy modules with correct gate counts
8. Decision record cannot be created without documented gates

---

## Constraints

- Module 12 is **GATE INFRASTRUCTURE ONLY**. Do NOT build agents for goals/fh/community/gi.
- Baseline tests exercise domain/service/schema layers directly — NEVER through HTTP (routers unmounted).
- Do NOT remount legacy modules. Do NOT modify legacy module.py files.
- Do NOT fix identity debt (`session_id`→`account_id`). Record it in baseline reports only.
- Pydantic v2 `extra="forbid"`, `schema_version="1.0.0"` where applicable.
- In-memory storage only (`RLock` pattern). No SQLite migrations.
- "Quantum" = Quantitative Finance, NOT quantum computing.
- Follow `quant_research` patterns: typed errors, auth via `resolve_principal`, feature flag checks.
- Vietnamese comments where appropriate, English identifiers.

---

## Gate Count Reference

| Module | Common Gates | Module-Specific | Total |
|---|---|---|---|
| `goals` | 8 | 6 (§3) | **14** |
| `financial_health` | 8 | 4 (§4) | **12** |
| `community` | 8 | 4 (§5) | **12** |
| `guided_investing` | 8 | 4 (§6) | **12** |

## Forbidden Shortcuts (§7)

- ❌ Remove ARCHIVE.md and remount without ADR
- ❌ Generic chatbot prompt replacing validated domain service
- ❌ Reuse Learn/BCTC memory as suitability profile
- ❌ Enable mutation just because Agentic Core supports confirmation
- ❌ "Personalized investing" from inferred preferences
- ❌ Community content as trusted instructions without moderation

## Open Decisions (§11)

1. Reactivation candidate priority (recommended: `goals` as first vertical slice)
2. Baseline test owner (product / engineering / compliance)
3. Gate approver (must be all three for any reactivation)
