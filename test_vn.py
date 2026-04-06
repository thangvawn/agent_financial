from datetime import datetime, timedelta
from vnstock import stock_historical_data

today = datetime.now().strftime("%Y-%m-%d")
try:
    df = stock_historical_data(symbol="VNINDEX", start_date=today, end_date=today, resolution="1", type="index", source="VCI")
    print(df.tail(2))
except Exception as e:
    print(e)
try:
    df2 = stock_historical_data(symbol="VNINDEX", start_date=today, end_date=today, resolution="1", type="index", source="TCBS")
    print(df2.tail(2))
except Exception as e:
    print(e)
