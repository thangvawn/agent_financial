"""Read a bounded public sample; write only QA artifacts, never the application DB."""
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["SOCIAL_REACH_RUNTIME"] = str(ROOT / ".local-dev/social-live-probe")
from risk_dashboard.modules.news_intelligence.infrastructure.agent_reach_adapter import AgentReachAdapter, ReachFailure

adapter = AgentReachAdapter()
jobs = [
    {"platform": "youtube", "action": "search", "target": "chứng khoán Việt Nam tháng 11 2026", "market": "vietnam"},
    {"platform": "youtube", "action": "search", "target": "global economy November 2026 interest rates", "market": "global"},
    {"platform": "reddit", "action": "search", "target": "stock market November 2026", "market": "global"},
]
posts, results = [], []
for job in jobs:
    start = time.monotonic()
    try:
        batch, partial = adapter.collect(job)
        posts.extend(batch)
        results.append({**job, "count": len(batch), "partial": partial, "elapsed_seconds": round(time.monotonic() - start, 2)})
    except ReachFailure as error:
        results.append({**job, "error": error.code, "elapsed_seconds": round(time.monotonic() - start, 2)})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    output = ROOT / "output/social-qa"
    output.mkdir(parents=True, exist_ok=True)
    (output / "live-posts.json").write_text(json.dumps(posts, ensure_ascii=False, indent=2))
    (output / "live-probe.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
