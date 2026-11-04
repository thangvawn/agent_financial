# 02/11/2026 — Vietnam sector heatmap

Status: **superseded for visual layout/readability** by [the user's correction and rectangular implementation](2026-11-02-market-heatmap-readable.md). API/data integration remains applicable. The prior checks did not assert that every cell contained both a ticker and percentage; the later browser audit found 109 blank and 122 percent-less cells among 190. The screenshot was an example, not a mandate to reproduce the polygons.

- Added the chart first in `MarketOverviewTab`, using `MarketHeatmap`, model/layout helpers, polling hook and dedicated worker. Search, exchange/sector drilldown, value/volume/capitalization weights, table, quote/details, keyboard and fullscreen work.
- New read-only whole-universe `/data-hub/vn-market/heatmap` endpoint and `domain/market_heatmap.py`. Cached ICB sector mapping; actual quote ceiling/floor states; no fabricated market cap or quotes.
- Captured universe: 1,521 names / 874 positive GTGD or volumes / 14 market caps. Default GTGD, explicit coverage and aggregation count. Do not switch to full-market capitalization without a real source.
- Fixed existing overview `turnover_billion` conversion from VND (divide 1e9). New regression test verifies consistency with chart weights.
- 13 backend / 169 frontend tests; lint, CSS55, Ruff, build and 12 Chromium groups passed. Browser QA used temporary auth/DB and copied real quotes. [Full evidence, scope, screenshots and limitations](../../qa/results/MARKET_HEATMAP_2026_11_02.md).
- Existing local Docker watchers serve the final bundle/endpoint; no explicit restart/deploy/push. No user DB reset/write or staging changes. Staged fingerprint remains `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`.
- Chart is a current snapshot visualization, not a historical chart/index or investment signal. Solver area is approximate; small cells are aggregated or unlabeled. Mobile first shows sectors; Safari/iOS devices are unverified. Social collector activation remains a separate, unresolved previous topic.
