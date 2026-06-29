import sys
sys.path.insert(0, "/Users/mac/Documents/Dự án Agent Tài chính/src")
from pathlib import Path
import pandas as pd

def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

path = Path("data/financial_uploads/bctc-fba91462c92205c2/document.md")
rows = []
in_table = False
for line in path.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if stripped == "| page | code | metric | label | current_value | previous_value | confidence |":
        in_table = True
        continue
    if in_table and stripped.startswith("| ---"):
        continue
    if in_table and not stripped.startswith("|"):
        break
    if not in_table or not stripped.startswith("|"):
        continue
    cells = [cell.strip().replace("\\|", "|") for cell in stripped.strip("|").split("|")]
    if len(cells) < 7:
        continue
    rows.append({
        "metric": cells[2] or None,
        "current_value": _safe_float(cells[4]),
        "previous_value": _safe_float(cells[5]),
    })

mapped = [r for r in rows if r["metric"]]
print("Mapped rows count:", len(mapped))

current_bucket = {}
previous_bucket = {}
for row in mapped:
    metric = str(row.get("metric") or "")
    if row.get("current_value") is not None and current_bucket.get(metric) is None:
        current_bucket[metric] = row.get("current_value")
    if row.get("previous_value") is not None and previous_bucket.get(metric) is None:
        previous_bucket[metric] = row.get("previous_value")

print("Current:", current_bucket)
print("Previous:", previous_bucket)
