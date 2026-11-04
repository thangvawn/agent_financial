# 02/11/2026 — Heatmap review findings fixed

Status: **fixed and verified**. User explicitly authorized fixes for all six findings in the preceding review.

- HM-01: reject incomplete SSI exchange batches; validate exchange coverage for every fallback and at the snapshot-write boundary. Preserve complete cached data as stale or return degraded/empty on cold start. Never silently combine separate refreshes.
- HM-02: adaptive money/share units prevent positive values displaying0; tiny percentage changes retain digits.
- HM-03: reanchor camera to the selected ticker/inspected point on data relayout; keep pinned quote. Removed selection returns to overview; scope changes reset camera.
- HM-04/HM-06: immediate capture on the actual cell, complete pointer/blur/visibility cleanup, and suppression limited to the click following a drag. Keyboard actions and ordinary cell clicks work.
- HM-05: retry generation restarts worker for identical data via top refresh or dedicated retry.
- Verification:176 frontend,16 isolated backend,19 browser groups pass; build/CSS55 pass. ESLint0 errors with1 unrelated Social warning; source has16 unchanged legacy Ruff E501 findings, no new findings. [Report/source/evidence](../../qa/results/MARKET_HEATMAP_LOGIC_FIXES_2026_11_02.md).
- Existing local frontend asset matches QA (`index-BendRU5c.js`); local read-only API returns1,521 rows. No user DB reset, manual main-app restart, deploy/push or staged changes. The earlier review is now resolved for HM-01–06.

Limits remain: expected-exchange completeness does not audit every individual ticker, capitalization source coverage is sparse, physical Safari/iOS unverified.
