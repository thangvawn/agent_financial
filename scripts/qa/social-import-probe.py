"""Process only queued imports in the isolated Social QA database."""

import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
output = ROOT / 'output/social-qa'
session = json.loads((output / 'session.json').read_text())
database = Path(session['db']).resolve()
assert database.parent.name.startswith('northstar-social-qa-')
assert database.name == 'state.db' and database.is_file()
os.environ.update(
    PYTHON_DOTENV_DISABLED='1', RISK_DASHBOARD_DB_PATH=str(database),
    RISK_DASHBOARD_APP_STATE_DB=str(database), RISK_DASHBOARD_SQLITE=str(database),
    ENABLE_SOCIAL_WORKER='0', ENABLE_TELEGRAM_NEWS_SCHEDULER='0', ENABLE_VN_MARKET_SCHEDULER='0',
    SOCIAL_REACH_RUNTIME=str(database.parent / 'reach'),
)
from risk_dashboard.modules.news_intelligence.application.social_worker import run_once
from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import list_posts
from risk_dashboard.modules.news_intelligence.infrastructure.social_repository import save_posts
from risk_dashboard.modules.news_intelligence.infrastructure.social_jobs import enqueue
from risk_dashboard.platform.database.connection import open_db

# Re-run just these QA imports after adapter fixes; discard only QA cached copies.
live = json.loads((output / 'live-posts.json').read_text())
selected = [next(p for p in live if p['platform'] == platform and p['market'] == 'global')
            for platform in ('youtube', 'reddit')]
owner = session['profile']['account_id']
with open_db() as conn:
    for post in selected:
        conn.execute('DELETE FROM social_posts WHERE account_id=? AND platform=? AND native_id=?',
                     (owner, post['platform'], post['native_id']))
        conn.execute("DELETE FROM social_jobs WHERE account_id=? AND action='read' AND target=?",
                     (owner, post['url']))
        save_posts(conn, owner, [post])
        conn.execute('DELETE FROM social_saved_posts WHERE account_id=?', (owner,))
        enqueue(conn, owner, post['platform'], 'read', post['url'], 'global')

results = []
for _ in range(2):
    started = time.monotonic()
    result = run_once()
    results.append({'job': result, 'elapsed_seconds': round(time.monotonic() - started, 2)})
    print(json.dumps(results[-1]), flush=True)
posts = list_posts(session['profile']['account_id'], saved=True)
report = {'results': results, 'saved': [{k: p[k] for k in (
    'id', 'platform', 'url', 'published_at', 'content_kind', 'transcript_status',
)} | {'transcript_length': len(p.get('transcript', ''))} for p in posts]}
(output / 'import-probe.json').write_text(json.dumps(report, indent=2))
assert len(posts) == sum(1 for r in results if r['job']['status'] == 'succeeded')
