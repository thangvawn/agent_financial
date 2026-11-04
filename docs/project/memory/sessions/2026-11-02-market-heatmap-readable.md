# 02/11/2026 — Every stock cell must be readable

Status: **historical, pagination superseded** by the user's explicit choice of one weighted map with zoom/pan. See [current implementation](2026-11-02-market-heatmap-single-map.md). The verification below describes the earlier paginated version only; it must not be treated as the current UX requirement.

- Replaced Voronoi with D3 squarified rectangular treemap; retained sector headers, true value weights and quote colors. Every colored cell is one stock with two unconditional text lines, font >=12px.
- Adaptive pages fit labels without inflating small stocks. All eligible names appear exactly once across pages. Count and metric share are explicit; areas compare within a page. Search/sector/table reach the complete filtered set.
- Missing price/% stays in table with an explicit count, not a blank chart cell. Mobile shows stocks with the same invariant, never a sector-only tile or anonymous aggregate.
- Old baseline: 190 cells, 109 blank and 122 missing %. New browser tests measure actual SVG glyph boxes on every page at five viewports: 5,263 stock occurrences passed. 171 frontend tests, lint/CSS55/build and 13 browser groups passed. [Research and evidence](../../qa/results/MARKET_HEATMAP_READABILITY_2026_11_02.md).
- Sample desktop first view: 38/874 stocks, 69.7% GTGD, 15 pages. At 390px: 11 stocks, 35.8%, 52 pages. Capitalization coverage remains only 14 source rows. Do not claim all stocks are simultaneously visible.
- Dependencies: d3-hierarchy 3.1.2; d3-voronoi-map/d3-polygon removed. Worker remains. Backend unchanged. Existing watcher serves final build; no push/deploy/restart or live DB writes. Existing staged fingerprint unchanged.
