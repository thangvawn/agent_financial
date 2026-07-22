/* Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V4 */

# News & Intelligence — Dark Shell and Period Highlights

**Date**: 2026-07-22  
**Type**: Feature implementation + single-page redesign  
**Status**: Ready for implementation  
**Context**: Preserve the existing React route/component boundaries and SQLite `news_articles` store while making News visually consistent with the dark financial workspace.

## Outcome

The `/news` and `/news-desk` routes keep their current navigation, reader, filters, save behavior, and article-detail flow. The News surface and its connected navbar become one continuous black/dark workspace, and the page gains a database-backed “Tin nổi bật” section that returns 5–10 ranked articles for `day`, `week`, or `month`.

The highlighted collection is a deterministic, persisted snapshot derived from `news_articles`, not a second article source. A request-driven refresh (the existing 600-second policy) upserts RSS results first, then rebuilds the current day/week/month snapshots. This keeps the selected 5–10 items stable across reloads and process restarts without adding an unnecessary scheduler.

## Scope and file contract

### Modify

- `frontend/src/styles/product-navigation.css` — remove the News route from the light-navbar override and add an explicit token-based black News navbar, including scrolled, dropdown, account, hover, active, and focus states.
- `frontend/src/styles/app-shell.css` — enforce a continuous dark News shell/content boundary and replace route-local `overflow-x: hidden` with `clip` where applicable; do not change public/light routes.
- `frontend/src/styles/retail-surfaces.css` — remove conflicting generic News navbar/card overrides so News consumes the existing dark tokens consistently.
- `frontend/src/styles/product-surfaces.css` — remove the late `!important` light News background/header bridge while leaving Global Terminal and Learning behavior unchanged.
- `frontend/src/features/news/pages/news.css` — consolidate News-only tokens/styles, responsive layout, period tabs, highlight cards, loading/empty/error states, and reduced-motion behavior; replace raw route colors with existing named app tokens.
- `frontend/src/features/news/pages/NewsPage.jsx` — add highlighted-period state and fetch lifecycle; preserve article selection, detail reader, filters, infinite feed, save actions, and route props.
- `frontend/src/features/news/pages/components/TodayBriefSection.jsx` — retain the production filename/component boundary, but evolve its UI into the period-selectable “Tin nổi bật” module instead of deleting/renaming it.
- `frontend/src/features/news/services/newsApi.js` — add `fetchNewsHighlights` with encoded, allow-listed query parameters.
- `frontend/src/features/news/services/index.js` — export the new client function.
- `src/risk_dashboard/modules/news_intelligence/application/services.py` — add period-window resolution, parameterized SQLite selection, deterministic ranking/diversification, and highlighted response assembly.
- `src/risk_dashboard/modules/news_intelligence/api/public.py` — add and validate the public highlights endpoint.
- `src/risk_dashboard/platform/database/migrate.py` — add ordered migration `004_news_highlight_snapshots`.
- `src/risk_dashboard/platform/database/app_state.py` — include highlight snapshots in test/reset cleanup while preserving `news_articles` rows outside explicit resets.
- `tests/test_news_intelligence.py` — add service/API/persistence/ranking/window/validation coverage.
- `tests/test_database_module.py` — assert migration creation/idempotency and snapshot constraints.
- `package.json` — add a root Playwright test script only; keep existing dependencies.

### Create

- `tests/e2e/news_highlights.spec.js` — Playwright checks for the critical desktop/mobile News flow.
- `playwright.config.js` — deterministic local web-server/base-URL and desktop/mobile projects for the new E2E spec.

### Delete

- None. Do not delete route files, components, stylesheets, SQLite data, or compatibility code.

### Explicitly unchanged

- `frontend/src/app/AppShell.jsx`, `frontend/src/app/productRegistry.js`, and `frontend/src/shared/navigation/ConnectedWorkspaceNav.jsx`: existing routes, view ids, auth gates, active-nav behavior, and markup ownership remain intact.
- `src/risk_dashboard/platform/database/schema/baseline.sql`: leave the baseline unchanged; ordered migration `004` creates snapshots for both fresh and existing databases. `news_articles` remains the canonical article source.
- Existing `/api/v1/public/news/feed`, article-detail, saved-news, pulse, source-health, and Finnhub contracts.

## API contract

### `GET /api/v1/public/news/highlights`

Query parameters:

| Parameter | Type | Rules | Default |
| --- | --- | --- | --- |
| `period` | enum | `day`, `week`, `month` | `day` |
| `limit` | integer | inclusive `5..10` | `5` |
| `force` | boolean | when true, refresh persisted articles before selection | `false` |

Period semantics use `Asia/Ho_Chi_Minh`: day is the local calendar day, week starts Monday, and month is the local calendar month. Store the resolved UTC bounds alongside a stable `period_key` (`YYYY-MM-DD`, `YYYY-Www`, or `YYYY-MM`) so boundary behavior is testable and unambiguous.

Success response (`200`):

```json
{
  "period": "week",
  "period_key": "2026-W30",
  "timezone": "Asia/Ho_Chi_Minh",
  "window_start": "2026-07-19T17:00:00+00:00",
  "window_end": "2026-07-26T17:00:00+00:00",
  "as_of": "2026-07-22T10:00:00+00:00",
  "requested_limit": 8,
  "count": 8,
  "items": [
    {
      "article_id": "…",
      "headline": "…",
      "summary": "…",
      "source": "…",
      "published_at": "…",
      "category": "markets",
      "region": "VN",
      "importance_score": 72,
      "importance_label": "high",
      "sentiment": "neutral",
      "impact": "medium",
      "why_it_matters": "…",
      "affected_markets": []
    }
  ],
  "generated_at": "2026-07-22T10:00:00+00:00",
  "freshness": "fresh",
  "data_quality": {},
  "safety": {}
}
```

Rules:

- Return fewer than five only when the selected persisted window genuinely has fewer candidates; never fabricate or duplicate news to fill the quota.
- Rank by `importance_score DESC`, then `sort_ts DESC`, `fetched_at DESC`, `article_id ASC`; cap a category at two items while alternatives exist and deduplicate by non-empty `content_hash`/normalized headline.
- Use parameterized SQL and the existing configured source map; do not interpolate user-controlled fields into SQL.
- Invalid `period` or out-of-range `limit` returns FastAPI `422`.
- Preserve existing safety/data-quality blocks and never present sentiment/impact as a buy/sell signal.

### SQLite snapshot model (`004_news_highlight_snapshots`)

`news_highlight_snapshots(snapshot_id TEXT PRIMARY KEY, period_kind TEXT CHECK day/week/month, period_key TEXT, timezone TEXT, window_start TEXT, window_end TEXT, items_json TEXT, item_count INTEGER CHECK 0..10, generated_at TEXT, source_run_id TEXT NULL, UNIQUE(period_kind, period_key))`, plus an index on `(period_kind, period_key)`. `items_json` stores at most ten article payloads/ids selected from `news_articles`; endpoint `limit` slices this stable snapshot. Build a missing current snapshot on demand; rebuild all three current-period rows after the existing TTL/manual refresh, using atomic upsert. Never delete historical `news_articles` or fabricate snapshot items.

## UI design and behavior

Hallmark direction: single-page editorial/institutional workbench; no new hero, ornamental gradients, fake chrome, or generic card wall. Existing Outfit/JetBrains Mono, 4px spacing scale, teal accent, and dark tokens remain the source of truth.

1. The route background, overscroll edge, surface panel, and navbar read as one black field (`--bg`/`--bg-deep`), separated only by the existing `--line` token.
2. Navbar identity, active tab, account, dropdown, and logout remain recognizable at dark contrast; teal is reserved for active/focus/status accents, not large background areas.
3. `TodayBriefSection` renders a compact heading, three period tabs (`Ngày`, `Tuần`, `Tháng`), a factual window/count label, and 5–10 highlighted rows/cards. Each item exposes source/time, importance, headline, concise “why it matters,” affected markets, open, and save controls.
4. Changing period refetches only highlights, shows an inline non-blocking loading state, preserves the feed/detail area, and moves focus neither to the top nor to the reader. Selecting a highlight sets `activeArticleId` even when that id is absent from the current feed array, then loads the existing detail endpoint and mobile detail tab; detail rendering must not fall back to the first feed article.
5. Refresh forces both feed and highlights to update from SQLite-backed ingestion; if refresh fails, retain the last successful highlighted items and show a retryable status instead of blanking the section.
6. Search, market lens, feed filters, infinite scroll, article reader, economic-calendar route, and saved-news behavior remain unchanged. Highlights are the desk-wide digest and do not silently change with feed filters.

## Responsive and accessibility acceptance

- Verify at 320, 375, 414, 768, 1024, and 1440px; `html`, `body`, shell, and News root have no page-level horizontal scroll. Use `overflow-x: clip`, never hide content with `hidden`.
- At 320–414px the heading controls stack, period tabs remain fully visible without scroll-jump, cards become one column with `min-width: 0`, and every clickable label stays on one line. The existing product-nav rail may retain its intentional internal horizontal scroll.
- At 768px highlights use at most two columns; desktop may use a restrained grid/list but must not exceed a readable 10-item scan area. Image-bearing grid tracks, if introduced later, use `minmax(0, 1fr)`.
- Period controls use `role="tablist"`, `role="tab"`, `aria-selected`, stable ids/`aria-controls`, and Left/Right/Home/End keyboard behavior. Loading uses `aria-busy`; result-count/status changes use a polite live region.
- Article selection uses a real button (not click-only `div`); nested Save remains a separate real button. All controls support default, hover, `:focus-visible`, active, disabled, loading, error, and success feedback where relevant.
- Focus ring contrast is at least 3:1; text/background contrast meets WCAG AA (4.5:1 normal, 3:1 large). Headings stay roman, long headlines use `overflow-wrap: anywhere`, and no button/nav label wraps to two lines.
- Motion affects only opacity/transform, uses existing duration/easing tokens, and becomes opacity-only at no more than 150ms under `prefers-reduced-motion: reduce`.

## Implementation phases (TDD)

### 1. Backend contract and persistence

1. Add failing migration/service/API tests for Vietnam calendar boundaries, `5..10` validation, deterministic ordering, category diversity, empty/sparse windows, and month retrieval from SQLite.
2. Add migration `004`, snapshot serialization/upsert/read helpers, and reset coverage.
3. Implement `NewsIntelligenceService.get_highlights(...)`: refresh only under the current request-driven TTL/`force`, rebuild current day/week/month snapshots after refresh, then read/slice the requested persisted snapshot.
4. Add `/news/highlights` and verify invalid parameters fail before service execution.
5. Add a persistence regression: populate SQLite/snapshots, instantiate a new service/process-equivalent with a failing/no-op producer, and prove the same snapshot remains available.

Acceptance: no in-memory-only highlight cache; service returns 5–10 when enough persisted candidates exist; all old endpoints/tests remain green.

### 2. React data flow

1. Add `fetchNewsHighlights` and export it.
2. Add independent `highlightPeriod`, payload, loading, and error state to `NewsPage`; cancel stale effects and ignore out-of-order responses.
3. Wire refresh to both requests without coupling highlights to market-lens/feed pagination state.
4. Preserve last successful data on transient errors and expose retry/refresh state to the component.

Acceptance: Day/Week/Month updates only the highlighted module; selecting/saving highlighted articles continues to use current handlers and reader behavior.

### 3. Dark shell and component redesign

1. Correct the News-specific light `!important` overrides in `product-navigation.css` and `product-surfaces.css`, then remove lower-priority conflicts in `retail-surfaces.css`.
2. Use route-scoped app tokens for black shell/navbar/surfaces and place the Hallmark stamp as the first non-empty line of the edited News CSS.
3. Refactor `TodayBriefSection` markup to semantic tabs/buttons and render all state variants; keep the filename/export stable.
4. Add mobile breakpoints and reduced-motion/focus treatments in `news.css`; do not introduce a new global theme or modify unrelated pages.

Acceptance: no white navbar/background seam on News; Market, Learning, BCTC, Home, and Pro Lab retain their existing skins.

### 4. Regression and visual verification

1. Run targeted pytest, full lint/build, then the full pytest suite/coverage.
2. Exercise the Playwright matrix with seeded deterministic API data and screenshots at desktop/mobile widths.
3. Inspect computed styles for News navbar/background and compare at least one unaffected light route and one unaffected dark route.
4. Run the Hallmark 58-gate post-build review; fix all active-genre failures before handoff.

## Test matrix

### Automated backend

- `pytest -q tests/test_news_intelligence.py tests/test_database_module.py`
- `pytest -q` and `pytest --cov=risk_dashboard --cov-report=term-missing`; new/changed backend paths must remain at least 80% covered.
- Assert exact UTC cutoffs with a frozen/injected clock; include Vietnam midnight, Monday-week, month rollover, and DST-independent UTC conversion cases.
- Assert SQL-injection-shaped filter input cannot alter queries and unknown source groups yield no unsafe dynamic SQL.

### Frontend/static

- `npm --prefix frontend run lint`
- `npm --prefix frontend run build`
- Browser request mocking verifies loading, success with 5 and 10 items, sparse/empty, 422, network failure with stale-data retention, and out-of-order period responses.

### E2E/manual browser

- Open `/news` with a valid session, confirm black shell/navbar and active News state.
- Switch Day → Week → Month by pointer and keyboard; verify request query, count, window label, reader selection, and no document scroll jump.
- Save/unsave a highlighted article and open its detail on desktop and mobile.
- Force refresh and confirm highlights re-read persisted results.
- At 320/375/414/768/1024/1440px assert no root overflow, no clipped focus ring, no two-line controls, and no white overscroll seam.
- Check reduced-motion and keyboard-only flows; run axe/Lighthouse accessibility checks with no serious/critical issues.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| CSS cascade reintroduces a light navbar | Fix the source override in `product-navigation.css`, keep News selectors route-scoped, and assert computed colors in browser verification. |
| Month tab has fewer than five rows on a new DB | Persist and return an honest sparse/empty snapshot; do not pad or fabricate. Historical availability grows naturally because `news_articles` persists. |
| Ranking starves topic diversity | Candidate pool larger than requested limit, category cap of two while alternatives exist, deterministic tie-breakers. |
| Period switch races overwrite newer choice | Abort/cancel request or sequence-token guard before setting state. |
| Forced refresh failure blanks useful data | Transactional existing upserts plus last-successful UI retention and retry status. |
| Snapshot becomes stale | Rebuild current three periods on the existing request-driven 600s refresh/`force`; expose `generated_at` and freshness. No scheduler in this scope. |

## Definition of done

- [ ] Exact API contract is implemented and documented by tests.
- [ ] Highlight selections are persisted in `news_highlight_snapshots`, trace back to `news_articles`, and survive service restart/fetch failure.
- [ ] Each period returns at most the requested 5–10 unique items and honest sparse states.
- [ ] News shell/navbar are black and visually continuous with token-based dark surfaces.
- [ ] Existing routes, components, endpoints, save/detail/feed behaviors, and SQLite rows are preserved.
- [ ] Responsive/a11y matrix passes, including 320/375/414/768px Hallmark floor.
- [ ] Backend tests, 80%+ changed-path coverage, frontend lint/build, critical E2E flow, and Hallmark slop test pass.
- [ ] No production files were deleted.

## Status

`PLAN_READY` · Implementation not started · Production files changed: none · Production files deleted: none
