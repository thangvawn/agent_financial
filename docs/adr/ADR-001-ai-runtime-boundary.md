# ADR-001: AI Runtime Boundary

- Status: Accepted
- Date: 2026-08-28

## Context

`risk_dashboard.platform.model_runtime` already reports local model runtime and model-path availability. Sprint 1 adds `risk_dashboard.platform.ai_runtime` for remote LLM provider contracts, adapters, redaction, retry, structured output, telemetry, and provider health.

Without an explicit boundary, two packages can report incompatible health for a remote provider or mix local model-path checks with network provider checks.

## Decision

`risk_dashboard.platform.ai_runtime` is sole owner of remote LLM provider health, including provider protocol health, adapter availability, retry behavior, redaction before provider dispatch, provider telemetry, and structured output validation.

`risk_dashboard.platform.model_runtime` remains sole owner of local model runtime/path availability. It does not own remote provider health.

Production remote model policy remains `gemini-3.5-flash`. No OpenAI production fallback is introduced.

No health API merge, package rename, or consumer migration occurs in this ADR.

## Consequences

Remote-provider consumers use `platform.ai_runtime` contracts and health checks. Local model consumers continue using `platform.model_runtime`.

AIR2 work remains required before a production surface migration: trusted prompt resolution, tool-schema handling, and enforceable cost policy are not implemented by this boundary decision.

## Rollback

This ADR changes ownership documentation only. Reverting it requires no data migration or runtime rollback.
