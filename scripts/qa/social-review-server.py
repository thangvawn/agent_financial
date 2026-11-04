"""Isolated Social QA server. Real auth, API and database; no production services."""
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
scratch = Path(tempfile.mkdtemp(prefix="northstar-social-qa-"))
os.environ.update(
    PYTHON_DOTENV_DISABLED="1", RISK_DASHBOARD_DB_PATH=str(scratch / "state.db"),
    RISK_DASHBOARD_APP_STATE_DB=str(scratch / "state.db"), RISK_DASHBOARD_SQLITE=str(scratch / "state.db"),
    ENABLE_SOCIAL_WORKER="0", ENABLE_TELEGRAM_NEWS_SCHEDULER="0", ENABLE_VN_MARKET_SCHEDULER="0",
    SOCIAL_REACH_RUNTIME=str(scratch / "reach"),
)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from risk_dashboard.app.bootstrap.app_factory import SPAStaticFiles
from risk_dashboard.modules.auth.api.public import router as auth
from risk_dashboard.modules.news_intelligence.api.social import router as social
from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import save_posts
from risk_dashboard.platform.database.connection import open_db
import uvicorn

app = FastAPI()
app.include_router(auth, prefix="/api/v1/public")
app.include_router(social, prefix="/api/v1/public")
app.mount("/dashboard-static", SPAStaticFiles(directory=ROOT / "output/social-qa/dist"))
client = TestClient(app)
user = client.post("/api/v1/public/auth/register", json={
    "email": "social-qa@example.test", "name": "Social QA", "password": "QA-temporary-12345!",
}).json()

live_path = ROOT / "output/social-qa/live-posts.json"
if live_path.exists():
    with open_db() as conn:
        save_posts(conn, user["profile"]["account_id"], json.loads(live_path.read_text()))
output = ROOT / "output/social-qa"
output.mkdir(parents=True, exist_ok=True)
(output / "session.json").write_text(json.dumps({**user, "db": str(scratch / "state.db")}))
(output / "session.json").chmod(0o600)
print(f"Isolated QA database: {scratch / 'state.db'}", flush=True)
uvicorn.run(app, host="127.0.0.1", port=5187, log_level="warning")
