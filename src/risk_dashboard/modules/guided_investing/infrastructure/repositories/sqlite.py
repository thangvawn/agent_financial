from __future__ import annotations

import sqlite3
import uuid
import json

from risk_dashboard.modules.guided_investing.domain.entities import (
    GuidedJournalEntry,
    GuidedPortfolioHolding,
    GuidedPortfolioReview,
    GuidedPortfolioReviewRecord,
    GuidedSavedPortfolio,
    GuidedWatchlistItem,
)
from risk_dashboard.modules.guided_investing.domain.ports import (
    GuidedJournalRepository,
    GuidedPortfolioRepository,
    GuidedWatchlistRepository,
)
from risk_dashboard.platform.database import open_app_state_db, reset_app_state_tables


class SqliteGuidedWatchlistRepository(GuidedWatchlistRepository):
    def list_items(self, *, user_id: str) -> list[GuidedWatchlistItem]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT item_id, user_id, ticker, label, reason_to_track, theme_tag, created_at, updated_at
                FROM guided_watchlist_items
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            GuidedWatchlistItem(
                item_id=row["item_id"],
                user_id=row["user_id"],
                ticker=row["ticker"],
                label=row["label"],
                reason_to_track=row["reason_to_track"],
                theme_tag=row["theme_tag"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def save_item(self, item: GuidedWatchlistItem) -> GuidedWatchlistItem:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO guided_watchlist_items (
                    item_id, user_id, ticker, label, reason_to_track, theme_tag, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    ticker = excluded.ticker,
                    label = excluded.label,
                    reason_to_track = excluded.reason_to_track,
                    theme_tag = excluded.theme_tag,
                    updated_at = excluded.updated_at
                """,
                (
                    item.item_id,
                    item.user_id,
                    item.ticker,
                    item.label,
                    item.reason_to_track,
                    item.theme_tag,
                    item.created_at,
                    item.updated_at,
                ),
            )
            conn.commit()
        return item


class SqliteGuidedJournalRepository(GuidedJournalRepository):
    def list_entries(self, *, user_id: str) -> list[GuidedJournalEntry]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT entry_id, user_id, ticker, title, thesis, uncertainties, review_condition, created_at, updated_at
                FROM guided_journal_entries
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            GuidedJournalEntry(
                entry_id=row["entry_id"],
                user_id=row["user_id"],
                ticker=row["ticker"],
                title=row["title"],
                thesis=row["thesis"],
                uncertainties=row["uncertainties"],
                review_condition=row["review_condition"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def save_entry(self, entry: GuidedJournalEntry) -> GuidedJournalEntry:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO guided_journal_entries (
                    entry_id, user_id, ticker, title, thesis, uncertainties, review_condition, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(entry_id) DO UPDATE SET
                    ticker = excluded.ticker,
                    title = excluded.title,
                    thesis = excluded.thesis,
                    uncertainties = excluded.uncertainties,
                    review_condition = excluded.review_condition,
                    updated_at = excluded.updated_at
                """,
                (
                    entry.entry_id,
                    entry.user_id,
                    entry.ticker,
                    entry.title,
                    entry.thesis,
                    entry.uncertainties,
                    entry.review_condition,
                    entry.created_at,
                    entry.updated_at,
                ),
            )
            conn.commit()
        return entry


class SqliteGuidedPortfolioRepository(GuidedPortfolioRepository):
    def get_saved_portfolio(self, *, user_id: str) -> GuidedSavedPortfolio | None:
        with open_app_state_db() as conn:
            row = conn.execute(
                """
                SELECT portfolio_id, user_id, name, holdings_json, created_at, updated_at
                FROM guided_saved_portfolios
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return GuidedSavedPortfolio(
            portfolio_id=row["portfolio_id"],
            user_id=row["user_id"],
            name=row["name"],
            holdings=[GuidedPortfolioHolding(**item) for item in json.loads(row["holdings_json"])],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_portfolio(self, portfolio: GuidedSavedPortfolio) -> GuidedSavedPortfolio:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO guided_saved_portfolios (
                    portfolio_id, user_id, name, holdings_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(portfolio_id) DO UPDATE SET
                    name = excluded.name,
                    holdings_json = excluded.holdings_json,
                    updated_at = excluded.updated_at
                """,
                (
                    portfolio.portfolio_id,
                    portfolio.user_id,
                    portfolio.name,
                    json.dumps([{"ticker": item.ticker, "weight_pct": item.weight_pct} for item in portfolio.holdings]),
                    portfolio.created_at,
                    portfolio.updated_at,
                ),
            )
            conn.commit()
        return portfolio

    def list_review_history(self, *, user_id: str) -> list[GuidedPortfolioReviewRecord]:
        with open_app_state_db() as conn:
            rows = conn.execute(
                """
                SELECT review_id, portfolio_id, user_id, scenario_label, holdings_json, review_json, created_at
                FROM guided_portfolio_review_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        records: list[GuidedPortfolioReviewRecord] = []
        for row in rows:
            review_payload = json.loads(row["review_json"])
            records.append(
                GuidedPortfolioReviewRecord(
                    review_id=row["review_id"],
                    portfolio_id=row["portfolio_id"],
                    user_id=row["user_id"],
                    scenario_label=row["scenario_label"],
                    holdings=[GuidedPortfolioHolding(**item) for item in json.loads(row["holdings_json"])],
                    review=GuidedPortfolioReview(
                        concentration_band=review_payload["concentration_band"],
                        top_holding_pct=review_payload["top_holding_pct"],
                        concentration_score=review_payload["concentration_score"],
                        warnings=review_payload["warnings"],
                        next_actions=review_payload["next_actions"],
                    ),
                    created_at=row["created_at"],
                )
            )
        return records

    def save_review_record(self, record: GuidedPortfolioReviewRecord) -> GuidedPortfolioReviewRecord:
        with open_app_state_db() as conn:
            conn.execute(
                """
                INSERT INTO guided_portfolio_review_history (
                    review_id, portfolio_id, user_id, scenario_label, holdings_json, review_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.review_id,
                    record.portfolio_id,
                    record.user_id,
                    record.scenario_label,
                    json.dumps([{"ticker": item.ticker, "weight_pct": item.weight_pct} for item in record.holdings]),
                    json.dumps(
                        {
                            "concentration_band": record.review.concentration_band,
                            "top_holding_pct": record.review.top_holding_pct,
                            "concentration_score": record.review.concentration_score,
                            "warnings": record.review.warnings,
                            "next_actions": record.review.next_actions,
                        }
                    ),
                    record.created_at,
                ),
            )
            conn.commit()
        return record


def new_watchlist_item_id() -> str:
    return f"gwi-{uuid.uuid4().hex[:12]}"


def new_journal_entry_id() -> str:
    return f"gje-{uuid.uuid4().hex[:12]}"


def new_portfolio_id() -> str:
    return f"gpf-{uuid.uuid4().hex[:12]}"


def new_review_id() -> str:
    return f"gpr-{uuid.uuid4().hex[:12]}"


def reset_guided_investing_state() -> None:
    reset_app_state_tables()
