# Vietnam market heatmap — 02/11/2026

Status: **historical; visual acceptance superseded** by [the readable treemap correction](MARKET_HEATMAP_READABILITY_2026_11_02.md). The old functional checks passed but did not establish readable ticker/% labels for every cell. The old `ship` verdict below is not current acceptance. API/data evidence remains relevant. No push, publish, service restart of port 8000, or live-account mutations.

## Delivered

- A sector-grouped weighted Voronoi chart, first in Market & Portfolio → Tổng quan. The user-supplied polygon chart is the visual reference; it is not a request to copy proprietary FoamTree assets/code. Implementation uses d3-voronoi-map 2.1.1 (BSD-3-Clause) and d3-polygon 3.0.1 (ISC).
- One complete snapshot from `/api/v1/public/data-hub/vn-market/heatmap`; no paginated quote mixing, inferred capitalizations, or provider fetch on this endpoint. Cached ICB level-3 classification is grouped by its top-level prefix; 8630 is separated as Bất động sản. These are ICB-derived groups, not a claim of GICS classification.
- Traded value is the default weight. Volume and available capitalization are alternatives. The captured source has 1,521 symbols, 874 positive values/volumes, and only 14 positive capitalizations. All missing/zero weights are counted explicitly; tiny names are aggregated without discarding their weight. Search, exchange and sector filters run before weighting.
- Color follows reference-relative change, with actual quote ceiling/floor prices for those states. No hardcoded ±7% rule. Missing/non-traded prices are gray. Sector/aggregate % is the weighted mean of names with usable prices, not an index return.
- Desktop shows individual stocks (190 cells in the captured GTGD sample); mobile shows 11 sectors and drills into stocks. Accessible table, quote popover, existing stock detail action, keyboard traversal, fullscreen and recovery states are included. Worker calculation avoids blocking the main UI.
- Corrected the existing overview summary's traded-value conversion: source value is VND; billion VND requires division by 1e9, not 1e3. Live read-only probe returned HOSE 15,836.3 / HNX 758.3 / UPCOM 569.1 billion VND at the sampled time.

## Evidence

- Backend: **13 passed**, including one coherent read-only snapshot, full universe, numeric validation, ICB mapping, turnover units and existing sector/exchange filters. [Isolated report](../../../../output/qa/isolated-tests/20261102T144608Z-b4dccf72/report.json).
- Frontend: **169 passed**; four dedicated model/layout contracts cover aggregation conservation, filtering/missing data, ceiling/floor semantics, unit formatting, deterministic finite polygons, representative area and mobile grouping. [Log](../../../../output/market-heatmap/frontend-tests.log).
- ESLint passed; CSS parser checked **55 files, zero failures**. Vite production build passed. Ruff passed on the touched public API and the new domain/test files. [Build](../../../../output/market-heatmap/build.log).
- Chromium: **12 groups passed, zero page errors**. Exchange filters match API row counts; capitalization coverage is 14/1,521; FPT search/quote/detail opens; keyboard and fullscreen work; 503 preserves prior data and recovers; first-load failure and stale sources are explicit; worker failure falls back to all 874 eligible table rows. Widths 768/390/320 are covered. [Results](../../../../output/market-heatmap/browser-results.json).
- Browser tests use the real auth/public routes in a QA FastAPI app and a captured copy of the complete real public quote payload. All auth/DB state is temporary. Unrelated global quote/history widgets are outside this QA's provider scope. No reset was run against the user's live DB.
- [Desktop viewport](../../../../output/market-heatmap/desktop.png), [mobile viewport](../../../../output/market-heatmap/mobile.png), [full desktop chart](../../../../output/market-heatmap/chart-desktop.png), [mobile chart](../../../../output/market-heatmap/chart-mobile-390.png), [mobile stock detail](../../../../output/market-heatmap/chart-mobile-detail-390.png).
- Layout probe across all three metrics at 1530/740/366/296 px succeeded. Observed 1–115 ms on this machine; solver error 0.0064–0.0194 before display gutters/header reservation. These are local measurements, not a universal performance guarantee. [Probe](../../../../output/market-heatmap/layout-probe.json).
- Snapshot-copy SHA-256: `f48706b52fa8fb079347e7a9d7da18aace30914d24c7eab621b0f3e73e2d68e5`. `live-snapshot.json` is a quote capture, not generated demo prices.
- Existing Docker source/build watchers already serve the new endpoint and the same final Vite index asset as QA: `index-ktfq9jV6.js`. No deployment/restart was needed. The preexisting 116 staged changes retain SHA-256 `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`.

## Design review

Impeccable finishing review was performed inline because no subagent review capability was available. This is an Operate-mode extension of an existing product, not a new comp-led site. The detector ran once and returned `[]`; subsequent fixes were assessed against captures, not a second detector run.

**disposition: ship**

- **persistence:** PRODUCT.md records the confirmed chart workflow and data constraints. Existing terminal tokens/chrome are preserved; the unrelated marketing DESIGN.md is not applied to this authenticated surface.
- **fidelity:** polygon clusters, sector grouping, bold ticker/change labels and white separation match the reference. TYPE: adaptation to the app's font and dynamic label fit. MATERIAL: match, geometry is rendered as SVG data. GROUND: light chart field and colored cells match; dark controls adapt to the existing terminal. Mobile sector drilldown and explicit coverage are functional adaptations to screen/data limits.
- **ceiling:** no decorative motion or 3D is needed for this data surface; chart geometry and interaction carry the design.
- **material_fixes:** none remaining in the delivered chart. Browser review fixed pointer tooltip interception, wrapped long mobile sector names, made the chart the first overview block, and strengthened text contrast (darkest red tile label ≈4.78:1; tooltip secondary text ≈6.39:1).
- **keep:** truthful weights/coverage, sector boundaries, legible color states, and access to every eligible name through filters/table.

## Limits and rerun

Area is approximate: numerical partition error, sector headers and gutters affect final visible area. Very small cells omit text and are available via search/table. A sector is an aggregate view, not an investment signal. Source timestamp reflects snapshot collection, not a guaranteed real-time tick for each security. No historical/replay mode, export, paid feed enrichment or full capitalization collection was added. Safari/iOS physical devices and full WCAG conformance were not tested.

Run frontend tests/lint/build from `frontend`; run backend tests only through `scripts/qa/run_isolated_tests.py`. For UI, build to `output/market-heatmap/dist`, provide a current public snapshot capture as `live-snapshot.json`, start `scripts/qa/market-heatmap-server.py`, wait for port 5188, then run `node scripts/qa/market-heatmap-browser.mjs`. The browser script's sample-count assertions are tied to the captured universe. Stop the QA server and remove its temporary session file after use.
