# Northstar Finance Lab

<!-- impeccable:product-schema 1 -->

## Platform

Web application, React frontend and Python/FastAPI backend, used on desktop and mobile browsers.

## Product Purpose

The existing product connects market observation, personal watchlists, financial statements, news, learning materials and simulation. The user has approved a Social extension to News covering Vietnam and international markets (02/11/2026).

## Confirmed Social Workflow

Read public discussions and videos, filter by market/platform/topic, follow sources, save posts per account, inspect the original source and see related news. Aggregation must preserve attribution, show missing data honestly and keep personal state scoped to the authenticated account.

## Constraints

The Market & Portfolio overview prioritizes a Vietnam sector heatmap. The user clarified on 02/11/2026 that the supplied image is only an example: every colored stock cell must contain one ticker and its numeric percentage change. The user rejected pagination and explicitly chose one complete map with zoom/pan, true traded-value weights and small labels becoming readable on zoom. Use a rectangular squarified treemap with no anonymous/aggregate cells, weight floors, hidden labels or pages. Use the shared Global Terminal palette for surfaces and sector headers in both light and dark modes. Area defaults to actual traded value across the complete filtered map, with volume and available capitalization as alternatives; disclose metric coverage and missing data. Ticker search and sector-header clicks navigate within the same map; explicit exchange/industry controls filter the universe. Provide zoom controls, drag/pinch, reset to overview and table access on desktop/mobile. Quotes open the existing stock detail view. The map uses the existing SSI snapshot and Vietcap ICB classifications.

The user supplied a new heatmap color reference on 02/11/2026: orange through dark red for losses, yellow at zero, lime/green for gains and white labels. Use a percentage-based legend matching these colors; ceiling/floor retain their actual quote status in details, while tile color follows percentage change. Preserve the single-map zoom/pan behavior.

Preserve the current News interface identity and compact controls. Use real collected content; display empty/error states when sources are unavailable. Collection runs outside interactive API requests. Do not publish or deploy without an explicit request. Private social account connections and unsupported Facebook group/image collection require a later capability check.

## Open Decisions

Specific curated author/channel lists and a paid translation/summarization provider have not been selected. The initial implementation uses source excerpts with attribution.

All application workspaces share a compact, accessible light/dark switch in the main navigation (02/11/2026, expanded from the earlier Market-only scope). Default to dark; migrate the former Market preference, persist the choice locally and synchronize open tabs. Market & Portfolio (all tabs), Learn Hub, BCTC, News/Social/calendar, Simulation/Backtest Studio and public/auth surfaces use the shared palette. Reader chrome follows the preference; PDFs, images and A4 note paper retain their own colors. Switching theme preserves active tabs, edited text and chart/map zoom.

## Market overview update — 03/11/2026

The Market overview was simplified on 03/11/2026: remove the redundant page hero and separate freshness header; use compact map controls and disclose source/time/help in a details section, keeping stale/error warnings visible. Quote-only ticks update their own keyed cells without rebuilding layout. Keep treemap rows stable per sector, resize with actual weights, retain the viewport and last-good map during background work/failure, and reconcile membership only when a complete layout is ready. Explicit filters or viewport resizing can rebuild the relevant layout.

## Market overview reference refinement —03/11/2026

After reviewing FireAnt /thi-truong, the implemented reading order is compact domestic indices, a market breadth/turnover strip, the full map, sector turnover shares and tabbed movers, then global indices. Mobile indices use a horizontal rail. Breadth details expand by exchange. Stock statistics and the map share the complete heatmap snapshot; exclude unmatched/missing quotes from breadth and apply the optional 1-billion-VND liquidity threshold before ranking movers. Sector bars represent turnover share, not sector returns. Index sparklines retain their daily one-month label.
