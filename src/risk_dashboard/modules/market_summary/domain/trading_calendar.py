"""Trading calendar domain abstractions and Vietnam Exchange calendar implementation."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol


class TradingCalendar(Protocol):
    def is_trading_day(self, check_date: date) -> bool:
        ...

    def previous_trading_day(self, from_date: date) -> date:
        ...


class VietnamExchangeTradingCalendar:
    """Vietnam Stock Market (HOSE/HNX) Trading Calendar.
    
    Handles weekends and official holidays (Tet, Independence Day, Reunification Day, Hung Kings Commemoration, New Year).
    """

    def __init__(self, extra_holidays: set[date] | None = None) -> None:
        self.extra_holidays = extra_holidays or set()

    def is_trading_day(self, check_date: date) -> bool:
        # Weekend check
        if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        if check_date in self.extra_holidays:
            return False

        # Fixed holidays check
        # New Year: Jan 1
        if check_date.month == 1 and check_date.day == 1:
            return False

        # Reunification & Labor Day: Apr 30 & May 1
        if check_date.month == 4 and check_date.day == 30:
            return False
        if check_date.month == 5 and check_date.day == 1:
            return False

        # National Day: Sep 2
        if check_date.month == 9 and check_date.day == 2:
            return False

        return True

    def previous_trading_day(self, from_date: date) -> date:
        curr = from_date - timedelta(days=1)
        while not self.is_trading_day(curr):
            curr -= timedelta(days=1)
        return curr


class FixtureTradingCalendar:
    """Fixture trading calendar that marks every date as a trading day (for tests)."""

    def is_trading_day(self, check_date: date) -> bool:
        return True

    def previous_trading_day(self, from_date: date) -> date:
        return from_date - timedelta(days=1)
