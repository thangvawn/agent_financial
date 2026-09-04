---
phase: 8
title: "BCTC7 — Rollout & Economics"
status: completed
priority: P2
effort: "3h"
dependencies: [3, 4, 5, 6, 7]
---

# Phase 8: BCTC7 — Rollout, Feature Flags & Economics

## Overview

Feature flags, cohort rollout (internal → 5% → 25% → 100%), cost/time-to-insight metrics, kill switch rollback. Deterministic BCTC REST vẫn hoạt động khi agent off.

## Requirements

### Functional

- Feature flag: `module.financials_product.bctc_agent.enabled` (sub-flag under module flag)
- Cohort progression: internal → 5% → 25% → 100%, chỉ advance khi KPI/security/cost gates pass
- Kill switch: rollback không mất deterministic BCTC REST
- Cost tracking: tokens/request, cost/evidence memo
- Time-to-insight metric: from trigger to reviewed memo delivery

### Non-functional

- Deterministic BCTC routes (`api/public.py`) unaffected when agent flag off
- Rollback < 1 minute (flag flip)

## Related Code Files

### Create

- `tests/test_bctc_rollout.py`

### Modify

- `src/risk_dashboard/modules/financials_product/module.py` — add sub-flag
- Feature flag config (wherever `FeatureFlagService.is_enabled()` reads from)

## Implementation Steps

1. Add `module.financials_product.bctc_agent.enabled` flag
2. Gate all agent tool endpoints behind flag check
3. Verify deterministic BCTC REST works when flag=false
4. Add cost/latency telemetry per tool call and per memo
5. Document rollout cohort progression criteria

## Success Criteria

- [ ] Flag off → deterministic BCTC works normally
- [ ] Flag on → agent tools available
- [ ] Kill switch rollback works
- [ ] Cost per memo tracked
- [ ] ≥3 tests pass
