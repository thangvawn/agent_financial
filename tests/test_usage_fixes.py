from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.platform.database import clear_db_path_cache
from risk_dashboard.modules.market_portfolio.application import services as svc

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('RISK_DASHBOARD_DB_PATH', str(tmp_path/'usage.db'))
    monkeypatch.setenv('API_SECRET_KEY', '')
    clear_db_path_cache()
    with patch.object(svc,'quote_last_price',return_value=100000), patch.object(svc,'quote_details_map',return_value={}), patch.object(svc,'quote_map',return_value={'FPT':100000}):
        yield TestClient(create_app())
    clear_db_path_cache()

def register(client, name='one'):
    r=client.post('/api/v1/public/auth/register', json={'name':name,'email':f'{name}@qa.test','password':'test-only-2026'})
    assert r.status_code == 200
    return r.json()

BASE='/api/v1/market-portfolio'
def test_body_query_bearer_resolve_same_owner_and_reject_revoked(client):
    a=register(client); sid=a['session_id']; headers={'Authorization':f'Bearer {sid}'}
    assert client.post(f'{BASE}/watchlist/items',json={'session_id':sid,'symbol':'FPT'}).status_code==200
    assert len(client.get(f'{BASE}/watchlist',params={'session_id':sid}).json()['items'])==1
    assert client.post(f'{BASE}/orders',json={'session_id':sid,'symbol':'FPT','side':'BUY','order_type':'MP','quantity':100}).status_code==200
    assert len(client.get(f'{BASE}/portfolio',headers=headers).json()['positions'])==1
    client.post('/api/v1/public/auth/logout',headers=headers)
    assert client.post(f'{BASE}/watchlist/items',json={'session_id':sid,'symbol':'VCB'}).status_code==401

@pytest.mark.parametrize('credential', [None, 'acct_arbitrary', 'legacy-unknown'])
def test_unverified_owner_cannot_read_or_write(client,credential):
    body={'symbol':'FPT'}
    if credential: body['session_id']=credential
    assert client.post(f'{BASE}/watchlist/items',json=body).status_code==401
    assert client.get(f'{BASE}/portfolio',params={'session_id':credential} if credential else {}).status_code==401

def test_missing_quote_is_incomplete_not_zero(client):
    a=register(client); h={'Authorization':f"Bearer {a['session_id']}"}
    client.post(f'{BASE}/orders',headers=h,json={'symbol':'FPT','side':'BUY','order_type':'MP','quantity':100})
    with patch.object(svc,'quote_map',return_value={}):
        p=client.get(f'{BASE}/portfolio',headers=h).json()
    assert p['equity'] is None and p['total_pnl'] is None
    assert p['valuation_status']=='incomplete' and p['missing_symbols']==['FPT']
    assert p['cash_balance']==90000000

def test_profile_identity_stable_and_legacy_owner_recovery(client):
    a=register(client); sid=a['session_id']
    assert a['profile']['account_id']
    svc.MarketPortfolioService().add_watchlist(sid,'FPT')
    svc.MarketPortfolioService().place_order(session_id=sid,symbol='FPT',side='BUY',order_type='MP',quantity=100,limit_price=None)
    b=client.post('/api/v1/public/auth/login',json={'email':'one@qa.test','password':'test-only-2026'}).json()
    assert b['profile']['account_id']==a['profile']['account_id']
    h={'Authorization':f"Bearer {b['session_id']}"}
    for _ in range(2):
        assert len(client.get(f'{BASE}/watchlist',headers=h).json()['items'])==1
        p=client.get(f'{BASE}/portfolio',headers=h).json()
        assert p['cash_balance']==90000000 and p['positions'][0]['quantity']==100
    other=register(client,'two')
    assert client.get(f'{BASE}/portfolio',headers={'Authorization':f"Bearer {other['session_id']}"}).json()['positions']==[]
