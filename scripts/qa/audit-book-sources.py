"""Read-only live source audit. Input: JSON list of books (or {books:[...]}).

Run with PYTHON_DOTENV_DISABLED=1 .venv/bin/python scripts/qa/audit-book-sources.py INPUT OUTPUT
Only metadata and the first 1024 bytes of remote documents are requested.
"""
import argparse
import concurrent.futures
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# App bootstrap imports can initialize storage; isolate that from the user's DB.
_audit_db = tempfile.TemporaryDirectory(prefix="northstar-source-audit-")
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["RISK_DASHBOARD_DB_PATH"] = str(Path(_audit_db.name) / "audit.db")

from fastapi import HTTPException
from risk_dashboard.app.bootstrap.app_factory import create_app  # Initialize existing app modules.
from risk_dashboard.modules.learning.api.reader_proxy import check_reader_content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    books = data['books'] if isinstance(data, dict) else data
    unique = {b.get('download_url') or b.get('pdf_url') or b.get('url'): b for b in books}

    def probe(pair):
        url, book = pair
        record = {'book_id': book.get('book_id') or book.get('id'), 'title': book.get('title'), 'url': url}
        if not url:
            return {**record, 'status': 'missing'}
        if url.startswith('/learning-assets/books/') and '..' not in url:
            path = Path('frontend/public' + url)
            prefix = path.read_bytes()[:4096] if path.is_file() else b''
            valid = prefix.lstrip().startswith(b'%PDF-') if path.suffix == '.pdf' else b'<html' in prefix.lower() or b'<!doctype' in prefix.lower()
            return {**record, 'status': 'ready' if valid else 'invalid' if prefix else 'missing', 'kind': path.suffix[1:]}
        try:
            return {**record, **check_reader_content(url=url)}
        except HTTPException as exc:
            return {**record, 'status': 'unavailable', 'http_status': exc.status_code, 'message': exc.detail}
        except Exception as exc:
            return {**record, 'status': 'unavailable', 'error': type(exc).__name__}

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pending = [pool.submit(probe, pair) for pair in unique.items()]
        for future in concurrent.futures.as_completed(pending):
            results.append(future.result())
            print(f"Checked {len(results)}/{len(unique)}: {results[-1]['status']}", flush=True)
    output = {'checked_at': datetime.now(timezone.utc).isoformat(), 'summary': dict(Counter(r['status'] for r in results)), 'books': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps(output['summary']))


if __name__ == '__main__':
    main()
