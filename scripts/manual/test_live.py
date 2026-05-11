import requests
import time

def get_dnse():
    now = int(time.time())
    start = now - 86400 * 2 # 2 days ago
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/index?resolution=1&symbol=VNINDEX&from={start}&to={now}"
    try:
        res = requests.get(url, timeout=5).json()
        if res and 'c' in res and len(res['c']) > 0:
            return res['c'][-1]
    except Exception as e:
        print("Error:", e)
    return None

print(get_dnse())
