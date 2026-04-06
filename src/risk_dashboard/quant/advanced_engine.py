import numpy as np
import pandas as pd
import warnings
from hmmlearn.hmm import GaussianHMM
from arch import arch_model

# Ignore statsmodels/arch warnings for clean logs
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

_advanced_cache = {"date_key": None, "regime": None, "vol_dict": None}

def compute_market_regime(df: pd.DataFrame) -> str:
    """
    Sử dụng Hidden Markov Model (HMM) để nhận diện trạng thái thị trường.
    Nhận diện 3 Regime: Bull (Tăng), Sideways (Đi ngang), Bear (Giảm).
    """
    date_key = df['date'].iloc[-1].strftime("%Y-%m-%d") if 'date' in df.columns else None
    
    if _advanced_cache["date_key"] == date_key and _advanced_cache["regime"] is not None:
        return _advanced_cache["regime"]
        
    if df.empty or len(df) < 50:
        return "Not Enough Data"
    
    returns = df['vn_index'].pct_change().dropna()
    volatility = returns.rolling(window=10).std().dropna()
    
    # Ghép dữ liệu (đảm bảo cùng chiều dài)
    min_len = min(len(returns), len(volatility))
    train_data = np.column_stack([
        returns.iloc[-min_len:].values.reshape(-1, 1), 
        volatility.iloc[-min_len:].values.reshape(-1, 1)
    ])
    
    # Train HMM với 3 trạng thái
    model = GaussianHMM(n_components=3, covariance_type="full", n_iter=100, random_state=42)
    model.fit(train_data)
    
    # Dự đoán trạng thái của ngày cuối cùng
    last_obs = train_data[-1].reshape(1, -1)
    hidden_states = model.predict(train_data)
    current_state = hidden_states[-1]
    
    # Phân loại trạng thái dựa vào kỳ vọng lợi nhuận trung bình của các cluster
    means = model.means_[:, 0] # Lấy cột lợi nhuận làm gốc
    sorted_idx = np.argsort(means)
    
    bear_state = sorted_idx[0]
    sideways_state = sorted_idx[1]
    bull_state = sorted_idx[2]
    
    if current_state == bear_state:
        res = "Bear (Thị trường Gấu)"
    elif current_state == bull_state:
        res = "Bull (Thị trường Bò)"
    else:
        res = "Sideways (Đi ngang)"
        
    _advanced_cache["date_key"] = date_key
    _advanced_cache["regime"] = res
    return res

def compute_garch_volatility(df: pd.DataFrame) -> dict:
    """
    Sử dụng GARCH(1,1) để dự báo biến động kỳ vọng của ngày giao dịch tiếp theo.
    """
    date_key = df['date'].iloc[-1].strftime("%Y-%m-%d") if 'date' in df.columns else None
    if _advanced_cache["date_key"] == date_key and _advanced_cache["vol_dict"] is not None:
        # Re-scale bounds dựa theo giá live gần nhất để dải GARCH chạy theo real-time nhẹ, 
        # nhưng KHÔNG fit lại model tốn CPU!
        cached_dict = _advanced_cache["vol_dict"]
        last_price = df['vn_index'].iloc[-1]
        ev = cached_dict["expected_volatility"]
        return {
            "expected_volatility": ev,
            "lower_bound": float(last_price * (1 - 1.96 * ev)),
            "upper_bound": float(last_price * (1 + 1.96 * ev)),
        }

    if df.empty or len(df) < 50:
        return {"expected_volatility": 0.0, "lower_bound": df['vn_index'].iloc[-1], "upper_bound": df['vn_index'].iloc[-1]}
    
    # Lấy chuỗi log returns (nhân 100 để GARCH dễ hội tụ)
    returns = 100 * np.log(df['vn_index'] / df['vn_index'].shift(1)).dropna()
    
    am = arch_model(returns, vol='Garch', p=1, q=1, rescale=False)
    # Tắt hiển thị log rối mắt
    res = am.fit(disp='off', last_obs=returns.index[-1])
    
    # Dự báo 1 ngày tiếp theo
    forecasts = res.forecast(horizon=1, align='origin')
    
    # expected variance là giá trị phương sai, vol là căn bậc hai
    expected_variance = forecasts.variance.iloc[-1, 0]
    expected_vol = np.sqrt(expected_variance) / 100.0 # trả lại tỉ lệ thập phân
    
    last_price = df['vn_index'].iloc[-1]
    
    # Khoảng tin cậy 95% (1.96 * vol)
    upper_bound = last_price * (1 + 1.96 * expected_vol)
    lower_bound = last_price * (1 - 1.96 * expected_vol)
    
    res_dict = {
        "expected_volatility": float(expected_vol),
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound)
    }
    
    _advanced_cache["date_key"] = date_key
    _advanced_cache["vol_dict"] = res_dict
    return res_dict

def optimize_portfolio_allocation(risk_score: float, expected_vol: float) -> dict:
    """
    Mô phỏng thu gọn của Black-Litterman kết hợp Mean-Variance.
    - risk_score: từ 0 tới 1. Biểu diễn "góc nhìn chủ quan" (Investor View) về xác suất sập.
    - expected_vol: Biến động GARCH. Rủi ro thực tế của thị trường.
    """
    # Khẩu vị rủi ro cơ bản (Risk Aversion)
    gamma = 3.0 
    
    # Nếu risk score cao, expected return thị trường tụt giảm, thậm chí âm
    # Một baseline expected return cơ sở của VNINDEX khoảng 12%/năm ~ 0.046%/ngày
    base_return_daily = 0.00046
    
    # Scale nó qua risk_score. Risk 0.5 -> Expected = 0.
    investor_view_return = base_return_daily * (0.5 - risk_score) * 10
    
    # Dùng công thức Mean-Variance: Trọng số w = E[R] / (gamma * Variance)
    variance = max((expected_vol ** 2), 0.000001)
    
    w_stock = investor_view_return / (gamma * variance)
    
    # Ràng buộc Short-selling và Margin (chỉ từ 0% đến 100%)
    w_stock = max(0.0, min(1.0, w_stock))
    w_cash = 1.0 - w_stock
    
    return {
        "stock_pct": float(w_stock * 100),
        "cash_pct": float(w_cash * 100)
    }
