# 02/11/2026 — Review logic heatmap

Status: **historical review; all six findings resolved in the subsequent fix**. See [verified fixes](2026-11-02-market-heatmap-logic-fixes.md). No production code edits were made during the review itself; the findings below describe the pre-fix version.

- HM-01 P1: one exchange timeout lets a partial SSI result overwrite the complete cache with freshness=fresh. Reproduced with mocked HNX failure and a temporary producer cache.
- HM-02 P2: fixed billion/million units and two decimals display positive values as zero; captured snapshot has123 affected GTGD rows and341 volume rows. PFL150,000 VND displays0 tỷ.
- HM-03 P2: after focusing PFL, VCB GTGD+1% retiles the map while keeping the old camera; PFL and its pinned quote disappear. Confirmed after worker completion.
- HM-04 P2: mouse release just outside the SVG before pointer capture leaves a stuck pan; reentry pans without a held mouse button.
- HM-05 P2: retrying a transient worker failure fetches identical data without restarting the worker; error remains.
- HM-06 P3: drag suppression also blocks later keyboard-generated sector-button clicks; mouse click works.
- [Full report, source locations, evidence and proposed fixes](../../qa/results/MARKET_HEATMAP_LOGIC_REVIEW_2026_11_02.md). Eight frontend and10 backend scoped tests pass but do not cover these failures. Browser probes use temporary auth/DB; feed calls mocked; no user-data changes, deploy or main-app restart.

HM-01–06 are now closed by targeted regressions in the linked fix session. This review's reproduction evidence remains historical.
