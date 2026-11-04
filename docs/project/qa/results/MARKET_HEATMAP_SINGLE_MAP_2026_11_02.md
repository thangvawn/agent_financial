# Single-map heatmap — 02/11/2026

Status: **verified** against the user's explicit choice of one weighted map with zoom/pan and small labels readable after zoom. Supersedes pagination and the minimum overview font requirement in [the prior report](MARKET_HEATMAP_READABILITY_2026_11_02.md).

## Behavior and implementation

- `marketHeatmapLayout.js` now builds one complete D3 squarified treemap. Sector groups and stock leaves use actual positive weights. Relative sector headers avoid collapsing tiny leaves; there are no absolute gutters, aggregates, weight floors or pages. Visible areas are approximate because sector headers occupy space.
- `marketHeatmapViewport.js` handles bounded zoom, anchor-preserving transforms, focus and viewport projection. All cells remain in the layout; only offscreen geometry is omitted from SVG rendering. Both ticker and numeric % are unconditional. Focus supports extremely thin small cells without modifying their market weights.
- `useHeatmapCamera.js` handles pointer drag, pinch and click suppression after drag. The component supplies +/- buttons, Ctrl-wheel, reset, search navigation and sector-header zoom. Explicit dropdown filters retain their filtering semantics. Search from table mode returns to the map.
- Final visual review found the quote card could cover the focused percentage. Pinned cards now sit beside the label or below the map when there is insufficient horizontal room; actual browser bounds check this.

## Verification

- **173 frontend tests passed**, including eight targeted heatmap tests for identity, missing data, price states, proportional area, complete layouts at multiple sizes, extreme skew, zoom anchoring, clipping and focus readability. [Unit log](../../../../output/market-heatmap/single-map/frontend-tests.log).
- ESLint, CSS syntax validation (**55 files, zero failures**) and production build passed. [Lint](../../../../output/market-heatmap/single-map/lint.log), [CSS](../../../../output/market-heatmap/single-map/css.log), [build](../../../../output/market-heatmap/single-map/build.log). Backend was unchanged and backend tests were not rerun for this correction.
- **10 Chromium scenario groups passed, zero page errors.** Complete overview identities and both label lines match the API at 1600/1024/768/390/320px. Checked 874 GTGD stocks, 874 volume stocks and 14 capitalization stocks. Focused labels fit their cells at >=16px and do not intersect the quote card. [Results](../../../../output/market-heatmap/single-map/browser-results.json), [reproducible runner](../../../../scripts/qa/market-heatmap-browser.mjs).
- Search from map/table, opening FPT detail, exchange/industry filters, sector zoom, +/- controls, drag without accidental quote opening, Ctrl-wheel, reset, keyboard traversal, fullscreen, two-finger touch emulation, search miss, 503/retry and missing-% table behavior passed. Touch zoom affected the map rather than the browser page.
- Separate pure layout probe: 15 metric/viewport combinations, **8,810 focus targets**, minimum calculated font **20px**. These are mathematical checks, not 8,810 browser interactions. [Probe](../../../../output/market-heatmap/single-map/layout-probe.json).
- Visually inspected [desktop overview](../../../../output/market-heatmap/single-map/overview.png), [FPT focus](../../../../output/market-heatmap/single-map/focus.png), [390px overview](../../../../output/market-heatmap/single-map/overview-390.png) and [smallest GTGD stock focused at 390px](../../../../output/market-heatmap/single-map/smallest-390.png). The latter confirms the quote card leaves both ticker and % visible.
- QA used temporary auth/DB and copied real public quotes; no live user DB reset/mutation. The main local app and QA build both reference `index-CIERbOcE.js`. Existing watcher only; no push/deploy/main-app restart. Staged fingerprint remains `f1d152161b6aa20a2eedf98fcbcbe8af727d9bda231d2e3b7b1763398963d8b3`.

## Finishing review and limits

Inline source/screenshot review using the existing Impeccable direction, not an independent reviewer. **Disposition: ship.** The current user-approved requirement is recorded in PRODUCT and memory. One complete market universe replaces the fragmented pages; true weights, explicit data coverage and the incumbent terminal styling remain.

Small overview labels intentionally require zoom. There are 1,521 source rows but only 874 with positive GTGD/volume in the captured snapshot; capitalization coverage is only 14. No source coverage was invented. Updated weights or viewport sizes can rearrange the treemap. Physical iOS/Safari, live-position stability and full accessibility certification remain unverified.
