"""The public exchange selector accepts provider labels HOSE and HSX equally."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from risk_dashboard.modules.data_hub.api import public


@pytest.mark.parametrize('exchange', ['HOSE', 'HSX'])
def test_snapshot_selector_accepts_both_provider_exchange_labels(monkeypatch, exchange):
    quotes = [
        {'symbol': 'AAA', 'exchange': 'HOSE', 'market_cap': 300, 'change_pct': 1},
        {'symbol': 'BBB', 'exchange': 'HSX', 'market_cap': 200, 'change_pct': -1},
        {'symbol': 'CCC', 'exchange': 'HNX', 'market_cap': 100, 'change_pct': 0},
    ]
    monkeypatch.setattr(public._vn_market, 'snapshot', lambda: {'items': quotes})
    app = FastAPI()
    app.include_router(public.router)
    with TestClient(app) as client:
        response = client.get('/data-hub/vn-market/snapshot', params={'exchange': exchange})
    assert response.status_code == 200
    assert [row['symbol'] for row in response.json()['items']] == ['AAA', 'BBB']
