"""Global-theme browser QA: temp auth DB and a copy of the public snapshot."""
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'output/global-theme'
scratch = Path(tempfile.mkdtemp(prefix='northstar-theme-qa-'))
os.environ.update(
    PYTHON_DOTENV_DISABLED='1', RISK_DASHBOARD_DB_PATH=str(scratch / 'state.db'),
    RISK_DASHBOARD_APP_STATE_DB=str(scratch / 'state.db'), RISK_DASHBOARD_SQLITE=str(scratch / 'state.db'),
    ENABLE_SOCIAL_WORKER='0', ENABLE_TELEGRAM_NEWS_SCHEDULER='0', ENABLE_VN_MARKET_SCHEDULER='0',
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap.app_factory import SPAStaticFiles
from risk_dashboard.modules.auth.api.public import router as auth
from risk_dashboard.modules.data_hub.api import public
import uvicorn

snapshot = json.loads((ROOT / 'output/market-heatmap/live-snapshot.json').read_text())
public._vn_market.snapshot = lambda **kwargs: deepcopy(snapshot)
app = FastAPI()
app.include_router(auth, prefix='/api/v1/public')
# The rest of the market shell is outside this QA's provider scope.
@app.get('/api/v1/public/data-hub/global-terminal')
def shell_quotes():
    return {'items': [], 'groups': [], 'as_of': snapshot['as_of'], 'freshness': 'stale', 'source': 'QA shell'}
app.include_router(public.router, prefix='/api/v1/public')
app.mount('/dashboard-static', SPAStaticFiles(directory=OUTPUT / 'dist'))
user = TestClient(app).post('/api/v1/public/auth/register', json={
    'email': 'heatmap-qa@example.test', 'name': 'Heatmap QA', 'password': 'QA-only-temporary-12345!',
}).json()
session = OUTPUT / 'session.json'
session.write_text(json.dumps(user))
session.chmod(0o600)
uvicorn.run(app, host='127.0.0.1', port=5190, log_level='warning')
