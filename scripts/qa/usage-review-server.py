"""Local QA backend: temporary SQLite, cached quotes, no background jobs. Run from repo root."""
import os
import tempfile
from pathlib import Path
import json
os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ['RISK_DASHBOARD_DB_PATH'] = str(Path(tempfile.mkdtemp(prefix='ns-review2-'))/'review.db')
os.environ['API_SECRET_KEY'] = ''
os.environ['ENABLE_TELEGRAM_NEWS_SCHEDULER'] = '0'
os.environ['ENABLE_VN_MARKET_SCHEDULER'] = '0'
os.environ['AI_ASSISTANT_AGENT_ENABLED'] = '0'
from risk_dashboard.modules.data_hub.application.vn_market_feed import VnMarketFeedProducer
cache = json.loads(Path('data/vn_market/snapshot.json').read_text())
universe = json.loads(Path('data/vn_market/universe.json').read_text())
VnMarketFeedProducer.snapshot = lambda self, **kw: cache
VnMarketFeedProducer.universe = lambda self, **kw: universe
from risk_dashboard.app.bootstrap.app_factory import create_app
import uvicorn
uvicorn.run(create_app(), host='127.0.0.1', port=5186, lifespan='off', access_log=False, log_level='warning')
