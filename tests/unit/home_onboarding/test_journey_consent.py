from __future__ import annotations

from unittest.mock import MagicMock

from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal, ConsentSnapshot
from risk_dashboard.modules.home_onboarding.application.journey_consent import (
    resolve_home_consent,
)
from risk_dashboard.modules.home_onboarding.application.journey_context import (
    build_home_journey_context,
)


def _make_principal(consent: ConsentSnapshot | None = None) -> AuthPrincipal:
    return AuthPrincipal(
        account_id="acc_test",
        session_id="sess_test",
        consent=consent,
        resolved_at="2026-09-01T00:00:00Z",
    )


def test_none_consent_returns_false_false():
    principal = _make_principal(consent=None)
    pers, mem = resolve_home_consent(principal)
    assert pers is False
    assert mem is False


def test_memory_true_returns_true_true():
    consent = ConsentSnapshot(
        memory=True,
        analytics=False,
        policy_version="1.0.0",
        consented_at="2026-09-01T00:00:00Z",
    )
    principal = _make_principal(consent=consent)
    pers, mem = resolve_home_consent(principal)
    assert pers is True
    assert mem is True


def test_memory_false_returns_false_false():
    consent = ConsentSnapshot(
        memory=False,
        analytics=True,
        policy_version="1.0.0",
        consented_at="2026-09-01T00:00:00Z",
    )
    principal = _make_principal(consent=consent)
    pers, mem = resolve_home_consent(principal)
    assert pers is False
    assert mem is False


def test_no_consent_skips_summary_readers():
    principal = _make_principal(consent=None)
    mock_reader = MagicMock()
    mock_reader.surface = "learn"

    context = build_home_journey_context(
        principal=principal,
        consent=(False, False),
        summary_readers=(mock_reader,),
    )
    assert context.personalization_consented is False
    assert context.summaries == ()
    mock_reader.list_reviewed_summaries.assert_not_called()

