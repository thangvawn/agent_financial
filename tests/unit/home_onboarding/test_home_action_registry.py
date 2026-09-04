from __future__ import annotations

import pytest

from risk_dashboard.modules.home_onboarding.domain.home_action_registry import (
    ALLOWED_ACTION_TYPES,
    ALLOWED_CTA_PREFIXES,
    is_action_allowed,
    validate_action,
)


def test_action_and_prefix_coupling() -> None:
    # Valid pairings
    assert is_action_allowed("open_lesson", "/learn?lesson=101")
    assert is_action_allowed("continue_lesson", "/learn/course-1")
    assert is_action_allowed("view_research_memo", "/bctc?memo_id=m123")
    assert is_action_allowed("refresh_artifact", "/simulation?experiment_id=e456")
    assert is_action_allowed("read_news_brief", "/news?brief_id=b789")
    assert is_action_allowed("read_market_education", "/market?artifact_id=a001")

    # Mismatched action and prefix must be rejected
    assert not is_action_allowed("open_lesson", "/market?artifact_id=1")
    assert not is_action_allowed("view_research_memo", "/news?brief_id=1")
    assert not is_action_allowed("refresh_artifact", "/learn?lesson=101")
    assert not is_action_allowed("read_news_brief", "/simulation")


def test_path_boundary_enforcement() -> None:
    # Exact prefix or with subpath / query param is allowed
    assert is_action_allowed("read_market_education", "/market")
    assert is_action_allowed("read_market_education", "/market/")
    assert is_action_allowed("read_market_education", "/market/overview")
    assert is_action_allowed("read_market_education", "/market?tab=portfolio")

    # Loose prefix matching without boundary must be strictly rejected
    assert not is_action_allowed("read_market_education", "/market-evil")
    assert not is_action_allowed("read_market_education", "/market_hacked")
    assert not is_action_allowed("read_market_education", "/markets/123")
    assert not is_action_allowed("read_news_brief", "/news-breaking-scam")
    assert not is_action_allowed("open_lesson", "/learning-unauthorized")


def test_invalid_actions_and_unsafe_paths() -> None:
    assert not is_action_allowed("arbitrary_action", "/learn")
    assert not is_action_allowed("open_lesson", "javascript:alert(1)")
    assert not is_action_allowed("open_lesson", "/learn<script>")
    assert not is_action_allowed("open_lesson", "")

    with pytest.raises(ValueError, match="not allowed by server registry"):
        validate_action("unknown_action", "/learn")

    with pytest.raises(ValueError, match="not allowed by server registry"):
        validate_action("open_lesson", "/market-exploit")
