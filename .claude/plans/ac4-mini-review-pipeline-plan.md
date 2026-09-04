# AC4-mini — Offline Review Pipeline Plan

## Goal

Turn an AC3 `GraphResult` into a deterministic reviewed artifact candidate. Every emitted claim must be backed by supplied tool evidence; numeric claims require an exact evidence-value match.

## Scope

- Claim Ledger, Evidence Reviewer, Numeric Reviewer, Safety/Policy Reviewer, Final Composer.
- Pure deterministic functions over AC3 output and caller-supplied claim payloads.
- Offline tests only.

## Non-goals

- No Gemini/network, LangChain wrapper, provider call, API route, frontend, feature flag, database migration, run checkpoint, memory write, `ActionProposal`, domain quant tool, commit/push.
- Do not modify `.claude/settings.json` or `data/global_market_prices/global_market_snapshot.json`.

## Files

1. Create `src/risk_dashboard/modules/agentic_core/schemas/claim.py`.
2. Create `src/risk_dashboard/modules/agentic_core/application/review.py`.
3. Create `tests/test_agentic_review.py`.

## Design

### Claim schemas

- `ClaimKind`: `text`, `numeric`, `policy`.
- `ClaimStatus`: `accepted`, `blocked`.
- `Claim`: stable `claim_id`, `kind`, `statement`, `evidence_refs`.
- `ReviewedClaim`: original claim plus status and optional `block_reason`.
- `ClaimLedger`: ordered immutable tuple of reviewed claims.
- `ReviewedArtifact`: reviewed final text, ledger, deterministic terminal status.

All contracts use `schema_version="1.0.0"` and contain no model/provider/tool capability fields.

### Review functions

`review_claims(claims, evidence)` performs ordered stages:

1. **Evidence reviewer:** blocks no refs or refs absent from `GraphResult.evidence`.
2. **Numeric reviewer:** for `numeric`, accepts only when an evidence value exactly occurs in claim statement; otherwise blocks `numeric_evidence_mismatch`.
3. **Safety/policy reviewer:** treats evidence and statement as untrusted data. It has no authority to change grants, capabilities, tools, envelope, or execution state.
4. **Final composer:** joins only accepted claim statements in ledger order. If none accepted, emits stable recovery text.

No extraction/NLP parser. Tests build claims explicitly; a future adapter can map structured provider output into these contracts.

## Test matrix

1. Valid evidence-backed text claim is accepted and composed.
2. No-evidence claim is blocked and omitted.
3. Numeric claim with exact evidence is accepted.
4. Numeric mismatch is blocked.
5. Composer output contains only accepted ledger statements.
6. Prompt-injection text in evidence remains data; no action/capability change is possible and unsupported claim stays blocked.
7. Agentic Core source has no `google.genai` provider SDK import.
8. Existing AC3 graph tests still pass.

## Risk and rollback

- Risk: treating arbitrary prose as claims. Mitigation: no automatic extraction; explicit typed inputs only.
- Risk: generic numeric matching is insufficient for formulas. Mitigation: exact literal evidence only; domain math validation deferred to AC6/domain reviewers.
- Rollback: delete three new files. No state or migration requires reversal.

## Success criteria

- Every final statement originates from an accepted claim.
- Every accepted claim references supplied evidence.
- Numeric accepted claim has exact evidence coverage.
- No network/provider SDK/API/DB mutation.
- Targeted AC3 + AC4 + Sprint foundation tests pass.
