# Readable market heatmap — 02/11/2026

Status: **historical, pagination superseded** by the user's explicit choice of one weighted map with zoom/pan. See [current verification](MARKET_HEATMAP_SINGLE_MAP_2026_11_02.md). The measurements below apply to the earlier paginated version, not the current layout.

## Diagnosis and research

The old renderer created 190 cells at the sampled desktop size. DOM audit found **109 without text and 122 without a percentage**, including 11 aggregate cells. Prior tests counted cells but did not test their content or text fit. [Baseline](../../../../output/market-heatmap/readable/baseline.json).

Read the primary [D3 treemap documentation](https://d3js.org/d3-hierarchy/treemap): squarified tiling aims for less elongated rectangles, supporting readability and area estimation. Aspect ratio is only a hint; switching tiling alone cannot guarantee room for text. Compared squarify ratios 1/1.3/1.618/2/2.5/3/4 and binary tiling on the captured distribution. Initial conservative bounds admitted 34 leading stocks at 1.3 versus 28 at 1 or 1.618; binary also admitted 34. Final measured monospace bounds admit 38 at a 1530px plot. This is a local heuristic, not a universal optimum. The source paper was retrieved but not independently read because no PDF text extractor was available; it is not used as supporting evidence.

## Decision and behavior

- Filter first; keep actual positive weights and sort descending by selected metric, with ticker as tie-breaker. Create sector headers and one rectangular leaf per stock using d3-hierarchy 3.1.2, squarify ratio 1.3.
- Require two lines (ticker, numeric %) at **12 CSS px minimum** with padding. Fit text using a fixed-width font, then verify actual SVG glyph bounds after fonts load in Chromium.
- Reduce a candidate page's count until every label fits; continue with remaining stocks. No inflated weights, aggregates, hidden text or lost eligible stocks. Next/previous/jump controls and full-set search/industry/table are available.
- Display current count and share of the entire filtered metric. Areas compare **within the current page**, not across pages. Sample first page: **38/874 stocks, 69.7% GTGD**, 15 pages. At 390px: 11/874, 35.8%, 52 pages. This sacrifices simultaneous breadth to meet the mandatory legibility requirement.
- Missing price/% rows remain in the table and are counted explicitly, never rendered as blank stock cells. Mobile also shows individual stocks. Sector names are headers, not colored aggregate cells.
- Replaced d3-voronoi-map/d3-polygon with d3-hierarchy (ISC); removed polygon clipping, aggregate calculations and conditional hidden labels. Worker computation remains. Backend/data provenance/ceiling-floor logic unchanged.

## Evidence

- **171 frontend tests passed**, six targeted contracts covering filtering, per-stock identity, missing %, price states/units, every page's bounds/non-overlap/readability, full weight conservation, area proportionality, determinism, extreme skew and long tickers. [Log](../../../../output/market-heatmap/readable/frontend-tests.log).
- ESLint, CSS parser (55 files), and production build passed. [Build](../../../../output/market-heatmap/readable/build.log). Backend was not changed; the earlier 13 backend tests are historical, not rerun here.
- **13 browser scenario groups passed, zero page errors.** Every page checked exact ticker identity, numeric %, two lines, font >=12px, and actual text bounds entirely inside its rectangle. Enumerating pages must equal the API eligible set exactly once.
- Checked 874 GTGD stocks at each of 1600/1024/768/390/320px, all 874 volume stocks, 14 available capitalizations, and 5 search matches: **5,263 rendered stock occurrences**. [Results](../../../../output/market-heatmap/readable/browser-results.json).
- Filters, sector-header drilldown, FPT detail opening, keyboard, fullscreen, stale/503 recovery, missing % and worker/table fallback passed. [All-page layout probe](../../../../output/market-heatmap/readable/layout-probe.json) observed approximately 0–15ms locally, not a runtime guarantee.
- [Desktop chart](../../../../output/market-heatmap/readable/chart-desktop.png), [390px chart](../../../../output/market-heatmap/readable/chart-390.png), [320px chart](../../../../output/market-heatmap/readable/chart-320.png), [desktop viewport](../../../../output/market-heatmap/readable/desktop.png), [mobile viewport](../../../../output/market-heatmap/readable/mobile.png).
- QA used temporary auth/DB and copied real public quotes. No user DB mutation/reset. Unrelated global/history providers are outside this scope. Existing local watcher serves the same final asset as QA, `index-DLdTnI0D.js`; no restart/deploy/push. Staged fingerprint unchanged.

## Finishing review

Performed inline with Impeccable, not an independent subagent review. The user's corrected requirement is authoritative; polygon silhouette is no longer a fidelity target. One scoped layout detector returned `[]`, followed by actual source/screenshot and glyph-bound inspection.

**Disposition: ship.** Persistence: PRODUCT and memory capture the correction. Fidelity: each stock is a labeled rectangle; sector grouping is retained; TYPE is data-appropriate monospace; MATERIAL is SVG data geometry; GROUND is the incumbent dark terminal. Ceiling: layout uses screen/data constraints, not decorative shapes. Material fixes: none remaining against the corrected cell-content requirement. Keep: no hidden labels, no fake weights and explicit per-view coverage.

Limits: many pages on small screens; use sector/search/table for direct access. Page counts can change with viewport/weights. Areas are not comparable across pages, and gutters/headers make visible area approximate. Stable positions during live weight changes, physical iOS/Safari and full WCAG compliance are unverified. This is a snapshot view, not an investment signal or full-capitalization feed.
