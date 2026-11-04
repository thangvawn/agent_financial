"""Download public reference data for UI QA only; never write the application DB."""
import json
from pathlib import Path
import yfinance as yf
out=Path('output/playwright/commodities')
out.mkdir(parents=True, exist_ok=True)
snapshot=json.loads(Path('data/global_market_prices/global_market_snapshot.json').read_text())
rows=[x for x in snapshot['items'] if x.get('group')=='commodities']
(out/'quotes.json').write_text(json.dumps({'items':rows,'as_of':snapshot['as_of'],'provider':'yahoo_finance','freshness':'stale','data_interval':snapshot.get('data_interval')}))
frames=yf.download([x['yahoo_symbol'] for x in rows], period='1y', interval='1d', auto_adjust=True, progress=False, threads=4)
result={}
for row in rows:
 try:
  frame=frames.xs(row['yahoo_symbol'],level=1,axis=1).dropna(subset=['Close'])
  points=[{'date':idx.isoformat(), 'open':float(r['Open']), 'high':float(r['High']), 'low':float(r['Low']), 'close':float(r['Close']), 'volume':float(r['Volume'])} for idx,r in frame.iterrows()]
  result[row['symbol']]={'symbol':row['symbol'],'points':points,'freshness':'fresh','source':'yahoo_finance'}
 except Exception as exc: print(row['symbol'],type(exc).__name__)
(out/'histories.json').write_text(json.dumps(result,allow_nan=False))
print({k:len(v['points']) for k,v in result.items()})
