from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Literal

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.schemas.agent_tools import (
    FreshnessStampV1,
    FreshnessState,
    MarketSession,
    PositionV1,
)


class ResourceNotFoundError(LookupError):
    """Non-disclosing error when a resource is not found or belongs to another account."""
    pass


class StaleDataBlockedError(ValueError):
    """Raised when an operation requires fresh data but data is stale and allow_stale is False."""
    pass


class CurrencyMismatchError(ValueError):
    """Raised when portfolio positions contain mixed currencies without authorized FX rates."""
    pass


class AdvisoryPolicyViolationError(ValueError):
    """Raised when generated text contains forbidden advisory or recommendation terms."""
    pass


FORBIDDEN_ADVISORY_PATTERNS: tuple[str, ...] = (
    r"\bkhuyến\s+nghị\s+(mua|bán|nắm\s+giữ)\b",
    r"\bkhuyên\s+(mua|bán)\b",
    r"\bhãy\s+(mua|bán|vào\s+lệnh)\b",
    r"\bnên\s+(mua|bán|tất\s+tay)\b",
    r"\bmúc\b",
    r"\bbắt\s+đáy\b",
    r"\btất\s+tay\b",
    r"\ball[- ]?in\b",
    r"\bbuy\s+now\b",
    r"\bsell\s+now\b",
    r"\bstrong\s+(buy|sell)\b",
    r"\btarget\s+price\b",
    r"\bgiá\s+mục\s+tiêu\b",
    r"\bchốt\s+lời\s+ngay\b",
    r"\bcắt\s+lỗ\s+ngay\b",
)


def check_portfolio_ownership(principal: AuthPrincipal, portfolio_id: str) -> str:
    """Ensure principal owns the requested portfolio. Returns the canonical account_id.

    Non-disclosing: raises ResourceNotFoundError if portfolio_id does not belong to principal.
    Strictly accepts principal.account_id or 'paper:{principal.account_id}'.
    """
    if not principal.account_id:
        raise ResourceNotFoundError("Resource not found.")
    clean_pid = portfolio_id.strip()
    if clean_pid in (principal.account_id, f"paper:{principal.account_id}"):
        return principal.account_id
    raise ResourceNotFoundError("Resource not found.")


def check_order_ownership(principal: AuthPrincipal, order_account_id: str) -> None:
    """Ensure principal owns the requested order. Non-disclosing on mismatch."""
    if not principal.account_id or order_account_id != principal.account_id:
        raise ResourceNotFoundError("Resource not found.")


def check_currency_consistency(positions: tuple[PositionV1, ...], portfolio_currency: str) -> None:
    """Ensure all positions have the same currency as the portfolio; mixed currencies not allowed without FX."""
    for pos in positions:
        if pos.avg_cost and pos.avg_cost.currency != portfolio_currency:
            raise CurrencyMismatchError(
                f"Position currency {pos.avg_cost.currency} does not match portfolio currency {portfolio_currency}."
            )
        if pos.mark_price and pos.mark_price.currency != portfolio_currency:
            raise CurrencyMismatchError(
                f"Mark price currency {pos.mark_price.currency} does not match portfolio currency {portfolio_currency}."
            )


def check_advisory_safety(text: str) -> list[str]:
    """Scan text for forbidden advisory or execution directive language."""
    violations: list[str] = []
    text_lower = text.lower()
    for pattern in FORBIDDEN_ADVISORY_PATTERNS:
        if re.search(pattern, text_lower):
            violations.append(pattern)
    return violations


def _resolve_hose_market_session(now_dt: datetime) -> MarketSession:
    """Compute HOSE market trading session in Vietnam local time (UTC+7)."""
    ict = timezone(timedelta(hours=7))
    vn_dt = now_dt.astimezone(ict)
    if vn_dt.weekday() >= 5:
        return "closed"

    minute = vn_dt.hour * 60 + vn_dt.minute
    if minute < 540:  # Before 09:00
        return "pre_open"
    if 540 <= minute < 555:  # 09:00 - 09:15 ATO
        return "pre_open"
    if 555 <= minute < 690:  # 09:15 - 11:30 Continuous Morning
        return "open"
    if 690 <= minute < 780:  # 11:30 - 13:00 Lunch Intermission
        return "closed"
    if 780 <= minute <= 885:  # 13:00 - 14:45 Continuous Afternoon + ATC
        return "open"
    if 885 < minute <= 900:  # 14:45 - 15:00 Post-trading
        return "post_close"
    return "closed"


def build_freshness_stamp(
    as_of: str,
    source: str,
    state: FreshnessState | None = None,
    ttl_seconds: int = 60,
    age_seconds: int | None = None,
    confidence_label: str | None = None,
    stale_reason: str | None = None,
    market_session: MarketSession | None = None,
    now_dt: datetime | None = None,
) -> FreshnessStampV1:
    """Dynamically compute data freshness, age, market session, and confidence."""
    now_dt = now_dt or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    # Parse as_of to calculate age dynamically
    computed_age = 0
    try:
        as_of_clean = as_of.replace("Z", "+00:00")
        as_of_dt = datetime.fromisoformat(as_of_clean)
        if as_of_dt.tzinfo is None:
            as_of_dt = as_of_dt.replace(tzinfo=timezone.utc)
        computed_age = max(0, int((now_dt - as_of_dt).total_seconds()))
    except (ValueError, TypeError):
        computed_age = ttl_seconds + 1

    final_age = computed_age if age_seconds is None else max(0, age_seconds)
    effective_ttl = max(1, ttl_seconds)

    # Dynamic state calculation if not explicitly forced
    if state is None:
        if final_age > effective_ttl:
            final_state: FreshnessState = "stale"
            stale_reason = stale_reason or f"Data age ({final_age}s) exceeds TTL ({effective_ttl}s)."
        else:
            final_state = "fresh"
    else:
        final_state = state
        if final_state == "stale" and not stale_reason:
            stale_reason = f"Data age ({final_age}s) exceeds TTL ({effective_ttl}s)."

    # Dynamic session
    final_session = market_session or _resolve_hose_market_session(now_dt)

    # Dynamic confidence label
    if confidence_label is not None:
        final_confidence = confidence_label
    elif final_state in ("stale", "unavailable"):
        final_confidence = "low"
    elif final_state == "partial" or final_session in ("closed", "weekend"):
        final_confidence = "medium"
    else:
        final_confidence = "high"

    return FreshnessStampV1(
        schema_version="1.0.0",
        as_of=as_of,
        source=source,
        state=final_state,
        ttl_seconds=effective_ttl,
        age_seconds=final_age,
        confidence_label=final_confidence,
        stale_reason=stale_reason,
        market_session=final_session,
    )
