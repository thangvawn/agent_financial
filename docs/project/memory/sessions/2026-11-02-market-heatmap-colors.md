# 02/11/2026 — Heatmap palette from the user reference

Status: **verified**. Narrow color refinement; single-map weights, zoom/pan and filters remain unchanged.

- Inspected the supplied PNG and sampled its colors after ICC-to-sRGB conversion. Losses now interpolate orange `#c57b00` to dark red `#bb0000` (saturated at −7%); zero is yellow `#cccc00`; gains interpolate lime `#80cc00` to green `#44bb00` (saturated at +3%). Legend shows these percentage stops.
- Floor/ceiling tile colors now follow percentage change, as in the reference; actual exchange state remains in quote details. Removed the obsolete blue/purple state-color export. White labels have a thin dark outline that scales down with tiny text.
- Eight existing targeted heatmap tests, ESLint, CSS55 and build passed. Browser checked all 874 identities/two-line white labels, representative positive/negative/flat/floor/ceiling fills, percentage legend, widths1600/768/390 and search focus, with no page errors. An initial QA capture raced the layout worker during resize; the corrected capture waits for completion. No product logic was changed for that race.
- [Browser evidence](../../../../output/market-heatmap/colors/browser-results.json), [desktop](../../../../output/market-heatmap/colors/desktop.png), [mobile](../../../../output/market-heatmap/colors/mobile.png), [unit log](../../../../output/market-heatmap/colors/unit.log), [build](../../../../output/market-heatmap/colors/build.log). Visually inspected desktop/mobile. This is not accessibility certification.
- Existing watcher serves the same build as QA: `index-Ca71-u7t.js`. QA used temporary auth/DB and copied public quotes. No backend changes, live DB writes, deploy, push or main-app restart. Existing staged changes preserved.
