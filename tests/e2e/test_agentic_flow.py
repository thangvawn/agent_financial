"""E2E test scaffold for agentic workflow — requires running server + GEMINI_API_KEY.

Marked skipif when GEMINI_API_KEY not set or server not reachable.
Full implementation deferred to AT4B.
"""
import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="E2E agentic flow requires GEMINI_API_KEY and running server",
)

def test_agentic_run_lifecycle_placeholder():
    """Placeholder — implement after backend API is mounted."""
    assert True  # Scaffold only
