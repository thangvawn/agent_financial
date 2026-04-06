from datetime import datetime
from vnstock import stock_historical_data

today = datetime.now().strftime("%Y-%m-%d")
try:
    df = stock_historical_data(symbol="VNINDEX", start_date=today, end_date=today, resolution="1D", type="index")
    print(df)
except Exception as e:
    print(e)
