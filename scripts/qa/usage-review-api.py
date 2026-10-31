"""Standalone local audit; all writes use a fresh temporary SQLite database."""
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
os.environ['PYTHON_DOTENV_DISABLED']='1'
os.environ['API_SECRET_KEY']=''
os.environ['RISK_DASHBOARD_DB_PATH']=str(Path(tempfile.mkdtemp(prefix='ns-api-review-'))/'review.db')
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap.app_factory import create_app
from risk_dashboard.modules.market_portfolio.application import services as svc
client=TestClient(create_app())
import logging
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('risk_dashboard.api.middleware').setLevel(logging.WARNING)
base='/api/v1/market-portfolio'
evidence={}
with patch.object(svc,'quote_last_price',return_value=100000), patch.object(svc,'quote_details_map',return_value={}), patch.object(svc,'quote_map',return_value={'FPT':100000}):
    auth=client.post('/api/v1/public/auth/register',json={'name':'Audit','email':'local-audit@example.test','password':'test-only-2026'}).json()
    sid=auth['session_id']
    headers={'Authorization':f'Bearer {sid}'}
    write=client.post(f'{base}/watchlist/items',json={'session_id':sid,'symbol':'FPT'})
    read=client.get(f'{base}/watchlist',params={'session_id':sid})
    evidence['watchlist_body_vs_query']={'write_status':write.status_code,'read_status':read.status_code,'items':read.json()['items']}
    payload={'session_id':sid,'symbol':'FPT','side':'BUY','order_type':'MP','quantity':100}
    order=client.post(f'{base}/orders',json=payload)
    portfolio=client.get(f'{base}/portfolio',params={'session_id':sid})
    evidence['orders_body_vs_query']={'write_status':order.status_code,'fill_status':order.json()['status'],'visible_positions':portfolio.json()['positions']}
    correct=client.post(f'{base}/orders',json=payload,headers=headers)
    visible=client.get(f'{base}/portfolio',headers=headers)
    evidence['bearer_control']={'write_status':correct.status_code,'visible_positions':visible.json()['positions'],'equity':visible.json()['equity']}
    with patch.object(svc,'quote_map',return_value={}):
        missing=client.get(f'{base}/portfolio',headers=headers).json()
        evidence['missing_quote_valuation']={k:missing[k] for k in ('cash_balance','market_value','equity','total_pnl','positions')}
    logout=client.post('/api/v1/public/auth/logout',headers=headers)
    rejected=client.get(f'{base}/watchlist',params={'session_id':sid})
    after=client.post(f'{base}/watchlist/items',json={'session_id':sid,'symbol':'VCB'})
    evidence['revoked_body_session']={'logout_status':logout.status_code,'query_read_status':rejected.status_code,'body_write_status':after.status_code,'body_write_symbol':after.json().get('symbol')}
out=Path('output/playwright/review-2026-10-31/api-evidence.json')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(evidence,indent=2,ensure_ascii=False))
print(json.dumps(evidence,indent=2,ensure_ascii=False))

checks = {
    'watchlist_write_read_same_owner': len(evidence['watchlist_body_vs_query']['items']) == 1,
    'orders_write_read_same_owner': len(evidence['orders_body_vs_query']['visible_positions']) == 1,
    'revoked_body_credential_rejected': evidence['revoked_body_session']['body_write_status'] == 401,
    'missing_quote_not_false_loss': evidence['missing_quote_valuation']['total_pnl'] != -10000000,
}
print('FAILED EXPECTATIONS:', ', '.join(name for name, passed in checks.items() if not passed))
raise SystemExit(0 if all(checks.values()) else 1)
