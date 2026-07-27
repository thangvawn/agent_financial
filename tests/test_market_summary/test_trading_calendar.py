"""Unit tests for VietnamExchangeTradingCalendar."""

from __future__ import annotations

from datetime import date
from risk_dashboard.modules.market_summary.domain.trading_calendar import VietnamExchangeTradingCalendar


def test_trading_calendar_weekdays():
    cal = VietnamExchangeTradingCalendar()
    # Monday 2026-07-27 is a trading day
    assert cal.is_trading_day(date(2026, 7, 27)) is True
    # Saturday 2026-07-25 is not a trading day
    assert cal.is_trading_day(date(2026, 7, 25)) is False


def test_trading_calendar_holidays():
    cal = VietnamExchangeTradingCalendar()
    # New Year Jan 1
    assert cal.is_trading_day(date(2026, 1, 1)) is False
    # Reunification Day Apr 30
    assert cal.is_trading_day(date(2026, 4, 30)) is False
    # Labor Day May 1
    assert cal.is_trading_day(date(2026, 5, 1)) is False
    # National Day Sep 2
    assert cal.is_trading_day(date(2026, 9, 2)) is False


def test_previous_trading_day():
    cal = VietnamExchangeTradingCalendar()
    # Previous trading day from Monday 2026-07-27 is Friday 2026-07-24
    prev = cal.previous_trading_day(date(2026, 7, 27))
    assert prev == date(2026, 7, 24)
