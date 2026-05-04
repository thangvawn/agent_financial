# Insights Backend Design

Insights là interpretation layer của Northstar Finance: News trả lời "chuyện gì vừa xảy ra", còn Insights trả lời "điều đó có nghĩa gì với bối cảnh thị trường". Module này không phát tín hiệu mua/bán và không để frontend tự parse text tự do.

## Product Judgment

Backend Insights cần cung cấp một read model có cấu trúc cho toàn bộ page: market regime, snapshot cards, narrative, trend radar, cross-asset pulse, scenario monitor, sector rotation, macro calendar, watchlist impact, learn links và AI companion context. Đây không chỉ là API chart vì mỗi block cần source, freshness, confidence, fallback và guardrail public-safe.

## Domain Model

- `MarketSummary`: regime, risk level, cross-asset theme, top driver, alerts count, summary.
- `SnapshotCard`: typed card cho hero cards, có status/severity/explanation.
- `InsightNarrative`: headline, summary, key_points, caveats, what_to_monitor, confidence.
- `TrendRadarItem`: category, status, sparkline_series, signal_strength.
- `CrossAssetSeries`: raw values, normalized values base 100, latest_change_pct, freshness.
- `ScenarioItem`: probability, impact_level, affected themes, assumptions, recommended_review.
- `SectorRotationItem`: relative strength, momentum, breadth, flow, explanation.
- `WatchlistImpact`: empty state hoặc theme/ticker impact mapping.
- `LearnLink`: concept-to-lesson mapping.
- `InsightsSafety` và `InsightsDataQuality`: bắt buộc trên dashboard response.

Core enums nên giữ ổn định cho API: `fresh|delayed|stale|unavailable`, `high|medium|low`, `risk_on|neutral|neutral_cautious|risk_off|stressed`, `low|watch|elevated|high`, `improving|deteriorating|stable|volatile`.

## Data Source Strategy

- Market: VN-Index, VN30, sector indices, OHLCV, breadth, foreign flow khi sẵn có.
- FX/rates: USD/VND, DXY, policy/local rates, bond yields.
- Commodities/global: gold, oil, copper, S&P 500, Nasdaq, MSCI EM, China/HK.
- Macro: CPI, Fed/SBV, GDP, PMI, employment, policy events.
- Internal: watchlist, goals, risk profile, learning progress, saved insights, news clusters, BCTC sector signals, quant risk score.

Providers phải trả metadata chất lượng dữ liệu để service degrade gracefully khi thiếu hoặc stale.

## Scoring Logic

- Market regime score: equity momentum 20%, volatility/risk 20%, FX/rates pressure 25%, breadth/liquidity 20%, commodity/global risk 15%.
- Risk level: 0-30 low, 31-55 watch, 56-75 elevated, 76-100 high.
- Top driver: strength cao, recent change lớn, confidence đủ, liên quan nhiều markets.
- Cross-asset normalization: `raw_t / raw_start * 100`; latest change: `raw_latest / raw_start - 1`.
- Sector rotation: relative strength vs VN-Index, recent momentum, breadth, flow nếu có.
- Scenario monitor: MVP rule/config based; Phase 2 model-based probability.

Output luôn là risk context, không phải forecast chắc chắn.

## API Design

MVP implemented:

- `GET /api/v1/public/insights/dashboard`

Planned public endpoints:

- `GET /api/insights/market-regime`
- `GET /api/insights/trend-radar`
- `GET /api/insights/cross-asset-pulse?range=1M`
- `GET /api/insights/scenario-monitor`
- `GET /api/insights/sector-rotation`
- `GET /api/insights/macro-calendar`
- `GET /api/insights/learn-links`

Planned personalized/AI/admin:

- `GET /api/insights/watchlist-impact`
- `GET /api/insights/personalized-dashboard`
- `POST /api/insights/save/{insight_id}`
- `POST /api/insights/feedback`
- `GET /api/insights/ai-context`
- `POST /api/insights/ask-ai`
- `POST /api/admin/insights/refresh`
- `GET /api/admin/insights/data-quality`
- `GET /api/admin/insights/source-health`

Dashboard response must include `safety` and `data_quality` on every successful response.

## Storage / Read Models

Recommended tables:

- `insight_snapshots`: as_of, regime, risk_level, top_driver, summary, payload_json, data_quality_json.
- `market_driver_snapshots`: driver_key, category, strength, direction, explanation, confidence.
- `cross_asset_series`: asset_key, date, raw_value, normalized_value, source.
- `scenario_snapshots`: scenario_key, probability, impact_level, summary, assumptions_json.
- `sector_rotation_snapshots`: sector, views, relative_strength, momentum_score, breadth_score.
- `macro_events`: event_name, event_time, region, impact_level, related_themes_json, source.
- `user_insight_relevance`: user_id, insight_id, relevance_score, reasons_json, watchlist/goals mapping.
- `saved_insights`: user_id, insight_id, note, saved_at.

Cache TTL: market snapshot 5-15m, cross-asset 15m/EOD, macro 1-6h, narrative 30-60m, sector rotation EOD, watchlist impact 15-60m or on-demand.

## Service Architecture

Routes stay thin. Application services orchestrate read models:

- `GetInsightsDashboard`
- market regime, trend radar, cross-asset, scenario monitor, sector rotation, macro calendar, watchlist impact, learn link, narrative and companion context services.

Repositories own storage access. Providers own external/internal data source adapters. Jobs precompute read models:

- `refresh_cross_asset_job`
- `refresh_market_regime_job`
- `refresh_trend_radar_job`
- `refresh_sector_rotation_job`
- `refresh_scenario_monitor_job`
- `refresh_insight_narrative_job`
- `refresh_watchlist_impact_job`

## AI Narrative Design

Narrative output is structured: headline, summary, key_points, caveats, what_to_monitor, learn_links, confidence. Prompt inputs include market data summary, drivers, cross-asset changes, scenarios, sector rotation, data quality and safety policy.

Safety rules: no buy/sell language, no certainty framing, distinguish fact from interpretation, mention stale data, redirect unsafe "nên mua gì" prompts toward risk factors and learning.

## Watchlist Impact

No watchlist returns empty state with CTA. With watchlist, map current themes such as USD strength, rates up, commodity volatility, emerging outflow, risk-off and liquidity stress to affected tickers, exposure level, explanation and review action.

## Data Quality And Safety

Every important response includes source, last_updated, freshness_status, confidence, missing_fields, stale_fields and fallback_used. If data is stale or partial, return a usable response with warnings instead of crashing.

Safety block is mandatory:

- `no_buy_sell_recommendation: true`
- disclaimer that Insights is context, not buy/sell recommendation
- allowed CTAs: review exposure, learn more, open scenario, ask AI, save insight
- prohibited CTAs: buy, sell, all_in, short_now

## Testing Plan

- Unit: market regime scoring, cross-asset normalization, trend radar classification, scenario mapping, sector rotation, watchlist impact.
- Integration: dashboard endpoint returns all sections with `data_quality` and `safety`.
- Contract: typed schema shape is stable for frontend rendering.
- AI safety eval: no buy/sell recommendation in narrative; risky ask-ai prompts are redirected.

## Implementation Plan

- Sprint 1: dashboard endpoint, typed schemas, mock/read-model providers, frontend render, safety and data quality.
- Sprint 2: persistent read models, refresh jobs, real macro/calendar feed, personalized watchlist mapping.
- Sprint 3: AI narrative eval, source health admin, Pro Lab integration, saved insight/research memo flows.

## Acceptance Criteria

- Frontend renders the whole Insights page from typed API.
- API always returns `data_quality` and `safety`.
- No buy/sell recommendation.
- Cross-asset chart has normalized data.
- Market narrative has key points and caveats.
- Scenario monitor has probability and impact.
- Watchlist impact has empty state or personalized response.
- Learn links map from current drivers.
- Backend degrades gracefully when data is missing.
