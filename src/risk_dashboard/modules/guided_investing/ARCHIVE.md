# Retired from product surface (Phase 4)

BCTC product UI uses `financials_product`. This module stays on disk for optional AI
context reads and can be remounted with `RISK_FLAG__MODULE__GUIDED_INVESTING__ENABLED=true`.

`enabled_by_default=False` — routers off unless the flag is set.
