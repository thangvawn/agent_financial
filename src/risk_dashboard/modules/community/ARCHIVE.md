# Archived from product surface (Phase 4)

This package is **unmounted** from `app/registry/registry.py`.

- Routers are not served.
- SQLite tables are retained (no data wipe).
- Soft imports may still exist in AI assistant (optional / try-except).
- Do not add new product features here.

To re-enable temporarily: remount in registry and set
`RISK_FLAG__MODULE__COMMUNITY__ENABLED=true`.
