# 02/11/2026 — One weighted map with zoom and pan

Status: **verified**, supersedes the paginated layout in [the preceding session](2026-11-02-market-heatmap-readable.md).

- User rejected 15 pages and explicitly chose: “Một bản đồ có zoom/kéo, giữ diện tích theo GTGD; mã nhỏ đọc rõ khi phóng to”. Small labels at overview are therefore intentional; do not reintroduce pagination, weight floors or aggregate cells to enforce a minimum overview font.
- One complete sector treemap retains every eligible stock and its actual positive weight. Both ticker and numeric % remain present. Zoom/pan only changes the camera; offscreen projection is culled without changing the map universe. Search navigates to a stock (including from table mode), sector headings zoom to a sector, and explicit exchange/industry controls filter.
- Added +/- controls, Ctrl-wheel, drag, two-finger pinch and overview reset. Search/focus allows enough zoom for the smallest actual quote, including thin capitalization cells. Pinned quote cards avoid the selected label and move below the map when side space is insufficient.
- Captured source: 1,521 rows, 874 positive GTGD/volume rows, only 14 positive capitalization rows. No backend/feed changes in this turn. [Report and evidence](../../qa/results/MARKET_HEATMAP_SINGLE_MAP_2026_11_02.md).
- Verification: 173 frontend tests; lint, CSS55 and build pass; 10 Chromium groups pass without page errors. All eligible identities/labels retained at five viewport widths; actual focused glyph bounds fit and remain unobscured. Separate pure layout probe checked 8,810 focus targets, minimum calculated font 20px; this is not a browser count.
- Existing local watcher serves the tested asset `index-CIERbOcE.js`. No deploy/push/restart of the main app. QA used a temporary auth DB and copied public quotes, without touching the user DB. Staged fingerprint unchanged.

Limits: small labels deliberately need zoom; geometry may move on resize or updated market weights; physical iOS/Safari are unverified. This is the existing snapshot feed, not full capitalization coverage or a live exchange connection.
