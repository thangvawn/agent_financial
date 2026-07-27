# Implementation Plan: Daily Market Summary Telegram Bot

Technical documentation for the Daily Market Summary Telegram Bot feature.

## Architecture Overview

```text
MarketDataProvider Protocol (Vnstock / Fixture)
              │
              ▼
   SessionCompletionPolicy (Validate Market Open/Close Data Quality)
              │
              ▼
       Domain Metrics (Pure Python Math: 20d SMA, Breadth, Contributions, Net Foreign Flow)
              │
              ▼
     MarketSummaryReport + DataQuality Metadata
              │
     ┌────────┴──────────────────────────┐
     ▼                                   ▼
[Mode: Fast / No-LLM]          [Mode: Analytical / Sub-Agent]
Deterministic Summarizer       MarketEditorialAgent (Structured Output)
                                         │
                                         ▼
                               NarrativeValidator (Number Grounding & Banned Words)
                                         │ (Fallback on Failure)
                                         └───────────► Deterministic Summarizer
                                                             │
                                                             ▼
                                                TelegramHtmlRenderer & SectionPacker
                                                             │
                                                             ▼
                                                Delivery State Machine (SQLite)
                                                             │
                                                             ▼
                                                TelegramClient (Classified Retry)
```

## Directory Structure

- Models: [`domain/models.py`](../../src/risk_dashboard/modules/market_summary/domain/models.py)
- Metrics: [`domain/metrics.py`](../../src/risk_dashboard/modules/market_summary/domain/metrics.py)
- Technical Indicators: [`domain/technical_analysis.py`](../../src/risk_dashboard/modules/market_summary/domain/technical_analysis.py)
- Trading Calendar: [`domain/trading_calendar.py`](../../src/risk_dashboard/modules/market_summary/domain/trading_calendar.py)
- Policies: [`domain/policies.py`](../../src/risk_dashboard/modules/market_summary/domain/policies.py)
- Data Providers: [`infrastructure/data_provider.py`](../../src/risk_dashboard/modules/market_summary/infrastructure/data_provider.py)
- Delivery Repository: [`infrastructure/delivery_repository.py`](../../src/risk_dashboard/modules/market_summary/infrastructure/delivery_repository.py)
- Telegram Client: [`infrastructure/telegram_client.py`](../../src/risk_dashboard/modules/market_summary/infrastructure/telegram_client.py)
- Summarizer: [`application/summarizer.py`](../../src/risk_dashboard/modules/market_summary/application/summarizer.py)
- Runner: [`application/runner.py`](../../src/risk_dashboard/modules/market_summary/application/runner.py)
- Telegram HTML Renderer: [`presentation/telegram_renderer.py`](../../src/risk_dashboard/modules/market_summary/presentation/telegram_renderer.py)
- CLI Entrypoint: [`cli/market_telegram.py`](../../src/risk_dashboard/cli/market_telegram.py)
