"""
analytics.py — Institutional-grade Quant Analytics Engine
=========================================================
Tất cả công thức toán học & kinh tế lượng cho hệ thống quản trị rủi ro.
Bao gồm: VaR, CVaR, Monte Carlo, GARCH, Beta, Sharpe, Sortino,
Information Ratio, Correlation Matrix, và Adaptive Conformal Prediction.

Nguyên tắc: Vectorized computation (Pandas/NumPy), không dùng vòng lặp Python.
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)


# ══════════════════════════════════════════════════════════
#  1. VALUE AT RISK (VaR) & CONDITIONAL VaR (CVaR)
# ══════════════════════════════════════════════════════════

def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    VaR lịch sử (Historical Simulation).
    
    Công thức: VaR_α = -Percentile(returns, 1-α)
    Ý nghĩa kinh tế: Với xác suất α%, mức lỗ tối đa trong 1 ngày không vượt quá giá trị này.
    
    Args:
        returns: Chuỗi lợi nhuận hàng ngày (log returns hoặc simple returns).
        confidence: Mức tin cậy (mặc định 95%).
    Returns:
        VaR dưới dạng số dương (ví dụ: 0.025 = lỗ tối đa 2.5%).
    """
    if returns.empty or len(returns) < 30:
        return float("nan")
    alpha = 1 - confidence
    return float(-np.percentile(returns.dropna(), alpha * 100))


def historical_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Conditional VaR (Expected Shortfall / CVaR).
    
    Công thức: CVaR_α = -E[R | R ≤ -VaR_α]
    Ý nghĩa kinh tế: Nếu lỗ vượt qua ngưỡng VaR, thì trung bình sẽ lỗ bao nhiêu?
    CVaR luôn ≥ VaR, phản ánh "tail risk" (rủi ro đuôi) tốt hơn VaR.
    """
    if returns.empty or len(returns) < 30:
        return float("nan")
    alpha = 1 - confidence
    var_threshold = np.percentile(returns.dropna(), alpha * 100)
    # Lấy trung bình của tất cả các ngày lỗ nặng hơn VaR
    tail_losses = returns[returns <= var_threshold]
    return float(-tail_losses.mean()) if not tail_losses.empty else float("nan")


def monte_carlo_var(
    returns: pd.Series,
    confidence: float = 0.95,
    n_simulations: int = 10_000,
    horizon_days: int = 1,
) -> dict:
    """
    Monte Carlo VaR — Giả lập n_simulations kịch bản tương lai.
    
    Phương pháp: Giả định returns ~ N(μ, σ²), sinh ngẫu nhiên n_simulations đường giá,
    sau đó lấy percentile α của phân phối lợi nhuận mô phỏng.
    
    Đây là phương pháp mạnh hơn Historical VaR vì có thể mở rộng sang nhiều ngày (horizon).
    
    Returns:
        Dict chứa VaR, CVaR, và phân phối mô phỏng (để vẽ histogram trên Dashboard).
    """
    if returns.empty or len(returns) < 30:
        return {"var": float("nan"), "cvar": float("nan")}
    
    clean = returns.dropna()
    mu = float(clean.mean())
    sigma = float(clean.std())
    
    # Sinh ma trận ngẫu nhiên: (n_simulations, horizon_days)
    # Công thức: R_cumulative = Σ(r_i) với r_i ~ N(μ, σ²)
    rng = np.random.default_rng(seed=42)
    simulated = rng.normal(mu, sigma, size=(n_simulations, horizon_days))
    
    # Lợi nhuận tích lũy qua horizon_days
    cumulative_returns = simulated.sum(axis=1)
    
    alpha = 1 - confidence
    var = float(-np.percentile(cumulative_returns, alpha * 100))
    cvar_mask = cumulative_returns <= -var
    cvar = float(-cumulative_returns[cvar_mask].mean()) if cvar_mask.any() else var
    
    return {
        "var": round(var, 6),
        "cvar": round(cvar, 6),
        "horizon_days": horizon_days,
        "n_simulations": n_simulations,
        "confidence": confidence,
        "percentile_5": round(float(np.percentile(cumulative_returns, 5)), 6),
        "percentile_95": round(float(np.percentile(cumulative_returns, 95)), 6),
    }


# ══════════════════════════════════════════════════════════
#  2. GARCH(1,1) VOLATILITY FORECASTING
# ══════════════════════════════════════════════════════════

def garch_forecast(returns: pd.Series, horizon: int = 5) -> dict:
    """
    GARCH(1,1) — Generalized Autoregressive Conditional Heteroskedasticity.
    
    Mô hình: σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
    
    Ý nghĩa kinh tế: Volatility có tính "di truyền" — ngày hôm nay biến động mạnh
    thì ngày mai cũng có xu hướng biến động mạnh (Volatility Clustering).
    GARCH giúp dự báo rủi ro chính xác hơn Standard Deviation thông thường.
    
    Args:
        returns: Chuỗi lợi nhuận hàng ngày.
        horizon: Số ngày dự báo (mặc định 5 ngày giao dịch = 1 tuần).
    """
    if returns.empty or len(returns) < 100:
        return {"error": "Cần ít nhất 100 quan sát để fit GARCH."}
    
    try:
        from arch import arch_model
        
        # Scale returns lên 100 (arch library cần scale lớn hơn)
        scaled = returns.dropna() * 100
        
        model = arch_model(scaled, vol="Garch", p=1, q=1, mean="AR", lags=1)
        result = model.fit(disp="off", show_warning=False)
        
        # Dự báo volatility cho horizon ngày tới
        forecast = result.forecast(horizon=horizon)
        variance_forecast = forecast.variance.iloc[-1].values  # shape: (horizon,)
        
        # Chuyển về daily volatility (chia 100 để scale lại)
        vol_forecast = np.sqrt(variance_forecast) / 100
        
        return {
            "model": "GARCH(1,1)",
            "omega": round(float(result.params.get("omega", 0)), 8),
            "alpha": round(float(result.params.get("alpha[1]", 0)), 6),
            "beta": round(float(result.params.get("beta[1]", 0)), 6),
            "persistence": round(float(result.params.get("alpha[1]", 0) + result.params.get("beta[1]", 0)), 6),
            "current_volatility_daily": round(float(vol_forecast[0]), 6),
            "forecast_volatility": [round(float(v), 6) for v in vol_forecast],
            "horizon_days": horizon,
            "aic": round(float(result.aic), 2),
            "bic": round(float(result.bic), 2),
        }
    except Exception as e:
        return {"error": f"GARCH fit thất bại: {e}"}


# ══════════════════════════════════════════════════════════
#  3. BETA & PERFORMANCE RATIOS
# ══════════════════════════════════════════════════════════

def compute_beta(stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Beta (β) — Hệ số rủi ro hệ thống.
    
    Công thức: β = Cov(R_stock, R_market) / Var(R_market)
    
    Ý nghĩa kinh tế:
    - β > 1: Cổ phiếu biến động mạnh hơn thị trường (rủi ro cao, lợi nhuận kỳ vọng cao).
    - β < 1: Cổ phiếu ít biến động hơn thị trường (phòng thủ).
    - β ≈ 1: Biến động tương đương thị trường.
    """
    aligned = pd.DataFrame({"stock": stock_returns, "bench": benchmark_returns}).dropna()
    if len(aligned) < 30:
        return float("nan")
    cov = aligned["stock"].cov(aligned["bench"])
    var_bench = aligned["bench"].var()
    return round(float(cov / var_bench), 4) if var_bench > 0 else float("nan")


def sharpe_ratio(returns: pd.Series, risk_free_annual: float = 0.045) -> float:
    """
    Sharpe Ratio — Lợi nhuận điều chỉnh rủi ro.
    
    Công thức: SR = (R_p - R_f) / σ_p  (annualized)
    
    Ý nghĩa: Mỗi đơn vị rủi ro bạn chấp nhận, bạn được bao nhiêu lợi nhuận thừa?
    SR > 1: Tốt, SR > 2: Xuất sắc, SR < 0: Lỗ ròng sau điều chỉnh.
    """
    if returns.empty or returns.std() == 0:
        return float("nan")
    excess = returns.mean() - risk_free_annual / 252
    return round(float(excess / returns.std() * np.sqrt(252)), 4)


def sortino_ratio(returns: pd.Series, risk_free_annual: float = 0.045) -> float:
    """
    Sortino Ratio — Chỉ phạt rủi ro GIẢM (downside), không phạt rủi ro TĂNG.
    
    Công thức: Sortino = (R_p - R_f) / σ_downside
    
    Ý nghĩa: Sharpe Ratio phạt cả khi giá tăng mạnh (volatility tăng = xấu).
    Sortino chỉ phạt khi giá giảm, phù hợp hơn cho nhà đầu tư.
    """
    if returns.empty:
        return float("nan")
    excess = returns.mean() - risk_free_annual / 252
    downside = returns[returns < 0]
    if downside.empty or downside.std() == 0:
        return float("nan")
    return round(float(excess / downside.std() * np.sqrt(252)), 4)


def information_ratio(
    returns: pd.Series, benchmark_returns: pd.Series
) -> float:
    """
    Information Ratio — Đánh giá năng lực "đánh bại" benchmark.
    
    Công thức: IR = Mean(R_p - R_b) / σ(R_p - R_b)
    
    Ý nghĩa: IR > 0.5 là quỹ tốt, IR > 1 là quỹ xuất sắc.
    """
    active = returns - benchmark_returns
    active = active.dropna()
    if active.empty or active.std() == 0:
        return float("nan")
    return round(float(active.mean() / active.std() * np.sqrt(252)), 4)


# ══════════════════════════════════════════════════════════
#  4. CORRELATION MATRIX
# ══════════════════════════════════════════════════════════

def compute_correlation_matrix(price_dict: dict[str, pd.Series]) -> dict:
    """
    Ma trận tương quan giữa các tài sản.
    
    Input: Dict {"VCB": pd.Series(prices), "FPT": pd.Series(prices), ...}
    Output: Dict chứa correlation matrix và gợi ý đa dạng hóa.
    
    Ý nghĩa kinh tế: Hai tài sản có tương quan thấp (< 0.3) giúp giảm rủi ro danh mục
    khi kết hợp (Diversification Effect).
    """
    if len(price_dict) < 2:
        return {"error": "Cần ít nhất 2 tài sản để tính tương quan."}
    
    # Tính return từ price
    returns_df = pd.DataFrame({
        ticker: prices.pct_change().dropna()
        for ticker, prices in price_dict.items()
    }).dropna()
    
    if returns_df.empty or len(returns_df) < 30:
        return {"error": "Không đủ dữ liệu để tính tương quan."}
    
    corr = returns_df.corr()
    
    # Tìm cặp tương quan thấp nhất (tốt nhất cho đa dạng hóa)
    pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], round(float(corr.iloc[i, j]), 4)))
    pairs.sort(key=lambda x: abs(x[2]))
    
    return {
        "correlation_matrix": corr.round(4).to_dict(),
        "best_diversification_pair": pairs[0] if pairs else None,
        "worst_diversification_pair": pairs[-1] if pairs else None,
        "n_assets": len(cols),
        "n_observations": len(returns_df),
    }


# ══════════════════════════════════════════════════════════
#  5. ADAPTIVE CONFORMAL PREDICTION (Robbins-Monro)
# ══════════════════════════════════════════════════════════

class AdaptiveConformalVaR:
    """
    Adaptive Conformal VaR — Tự động điều chỉnh α để đảm bảo
    tỷ lệ vi phạm (Violation Rate) tiệm cận mục tiêu.
    
    Thuật toán: Robbins-Monro Stochastic Approximation
    
    Công thức cập nhật:
        α_{t+1} = α_t + γ_t · (hit_t - target)
    
    Trong đó:
        - α_t: Miscoverage rate hiện tại (1 - confidence).
        - hit_t: 1 nếu thua lỗ thực tế > VaR dự báo (vi phạm), 0 nếu không.
        - target: Tỷ lệ vi phạm mục tiêu (mặc định 5% = 0.05).
        - γ_t: Learning rate (giảm dần theo 1/√t để đảm bảo hội tụ).
    
    Ý nghĩa kinh tế:
        Nếu mô hình VaR của bạn đang quá lạc quan (violation > 5%),
        thuật toán sẽ TỰ ĐỘNG nới rộng dải rủi ro.
        Nếu quá bi quan (violation < 5%), thuật toán sẽ thu hẹp lại.
        Đây là chuẩn mực MỚI trong quản trị rủi ro, vượt xa Basel III truyền thống.
    """
    
    def __init__(self, target_miscoverage: float = 0.05, gamma_0: float = 0.1):
        self.target = target_miscoverage  # α mục tiêu (5%)
        self.gamma_0 = gamma_0            # Learning rate ban đầu
        self.alpha = target_miscoverage   # α hiện tại (khởi tạo = target)
        self.t = 0                        # Bộ đếm thời gian
        self.history: list[dict] = []     # Lưu lại lịch sử cập nhật
    
    def update(self, actual_loss: float, predicted_var: float) -> dict:
        """
        Cập nhật α sau mỗi ngày giao dịch.
        
        Args:
            actual_loss: Mức lỗ thực tế ngày hôm qua (số dương = lỗ).
            predicted_var: VaR dự báo ngày hôm qua (số dương).
        
        Returns:
            Dict chứa α mới, trạng thái vi phạm, và thống kê.
        """
        self.t += 1
        
        # hit = 1 nếu lỗ thực tế vượt VaR (vi phạm)
        hit = 1.0 if actual_loss > predicted_var else 0.0
        
        # Robbins-Monro: γ_t giảm dần theo 1/√t để đảm bảo hội tụ
        # (Điều kiện Robbins-Monro: Σγ_t = ∞, Σγ_t² < ∞)
        gamma_t = self.gamma_0 / np.sqrt(self.t)
        
        # Cập nhật α: nếu hit=1 (vi phạm) → α tăng → VaR mở rộng
        # Nếu hit=0 (an toàn) → α giảm → VaR thu hẹp
        alpha_new = self.alpha + gamma_t * (hit - self.target)
        
        # Clamp α trong khoảng hợp lý [0.01, 0.20]
        alpha_new = float(np.clip(alpha_new, 0.01, 0.20))
        
        record = {
            "step": self.t,
            "alpha_before": round(self.alpha, 6),
            "alpha_after": round(alpha_new, 6),
            "confidence": round(1 - alpha_new, 6),
            "hit": int(hit),
            "actual_loss": round(actual_loss, 6),
            "predicted_var": round(predicted_var, 6),
            "gamma_t": round(gamma_t, 6),
            "cumulative_violation_rate": round(
                sum(h["hit"] for h in self.history + [record]) / self.t, 4
            ) if self.t > 0 else 0,
        }
        
        self.alpha = alpha_new
        self.history.append(record)
        
        return record
    
    def get_current_confidence(self) -> float:
        """Trả về mức tin cậy hiện tại (1 - α)."""
        return round(1 - self.alpha, 6)
    
    def get_violation_rate(self) -> float:
        """Tỷ lệ vi phạm tích lũy."""
        if not self.history:
            return 0.0
        return round(sum(h["hit"] for h in self.history) / len(self.history), 4)
    
    def get_summary(self) -> dict:
        """Tóm tắt trạng thái bộ hiệu chỉnh."""
        return {
            "total_days": self.t,
            "current_alpha": round(self.alpha, 6),
            "current_confidence": self.get_current_confidence(),
            "target_violation_rate": self.target,
            "actual_violation_rate": self.get_violation_rate(),
            "convergence_status": (
                "✅ HỘI TỤ" if abs(self.get_violation_rate() - self.target) < 0.015
                else "⏳ ĐANG ĐIỀU CHỈNH"
            ),
        }


# ══════════════════════════════════════════════════════════
#  6. CONVENIENCE: Full Risk Report
# ══════════════════════════════════════════════════════════

def full_risk_report(returns: pd.Series, confidence: float = 0.95) -> dict:
    """
    Tạo báo cáo rủi ro toàn diện từ một chuỗi lợi nhuận.
    Gộp tất cả chỉ số vào một dict duy nhất để Agent có thể đọc.
    """
    report = {
        "n_observations": len(returns),
        "annualized_return_pct": round(float(returns.mean() * 252 * 100), 2),
        "annualized_volatility_pct": round(float(returns.std() * np.sqrt(252) * 100), 2),
        "max_drawdown_pct": round(float(_max_drawdown(returns) * 100), 2),
        "historical_var": round(historical_var(returns, confidence), 6),
        "historical_cvar": round(historical_cvar(returns, confidence), 6),
        "monte_carlo": monte_carlo_var(returns, confidence),
        "sharpe_ratio": sharpe_ratio(returns),
        "sortino_ratio": sortino_ratio(returns),
        "garch": garch_forecast(returns),
        "confidence_level": confidence,
    }
    return report


def _max_drawdown(returns: pd.Series) -> float:
    """Tính Maximum Drawdown từ chuỗi returns."""
    cumulative = (1 + returns).cumprod()
    peak = cumulative.expanding().max()
    drawdown = (cumulative - peak) / peak
    return float(drawdown.min()) if not drawdown.empty else 0.0


# ══════════════════════════════════════════════════════════
#  7. BACKTESTING KIỂM ĐỊNH VaR (Basel III Compliance)
# ══════════════════════════════════════════════════════════

def kupiec_pof_test(violations: int, n_observations: int, confidence: float = 0.95) -> dict:
    """
    Kupiec Proportion of Failures (POF) Test.
    
    Kiểm định H₀: Tỷ lệ vi phạm VaR đúng bằng (1 - confidence).
    
    Thống kê kiểm định (Likelihood Ratio):
        LR_POF = -2·ln[(1-p)^(n-x) · p^x] + 2·ln[(1-x/n)^(n-x) · (x/n)^x]
    
    Trong đó:
        - p = 1 - confidence (tỷ lệ vi phạm kỳ vọng, vd: 0.05)
        - x = số lần vi phạm (violations)
        - n = tổng số quan sát (n_observations)
    
    LR_POF ~ χ²(1). Nếu p-value < 0.05 → BÁC BỎ mô hình VaR (không đạt chuẩn Basel).
    
    Ý nghĩa Basel III:
        - Green zone:  x/n ≈ p → Mô hình đạt chuẩn.
        - Yellow zone:  x/n hơi lệch → Cần theo dõi.
        - Red zone:    x/n lệch nhiều → Phải nâng vốn dự phòng.
    """
    from scipy import stats
    
    x = violations
    n = n_observations
    p = 1 - confidence  # Expected violation rate
    
    if n == 0 or x < 0:
        return {"error": "Dữ liệu không hợp lệ."}
    
    observed_rate = x / n
    
    # Tránh log(0) bằng clipping
    eps = 1e-10
    p_clip = np.clip(p, eps, 1 - eps)
    obs_clip = np.clip(observed_rate, eps, 1 - eps)
    
    # Likelihood Ratio statistic
    lr = -2 * ((n - x) * np.log(1 - p_clip) + x * np.log(p_clip)) \
         + 2 * ((n - x) * np.log(1 - obs_clip) + x * np.log(obs_clip))
    
    p_value = float(1 - stats.chi2.cdf(lr, df=1))
    
    # Basel III Traffic Light
    if observed_rate <= p * 1.5:
        zone = "🟢 GREEN (Đạt chuẩn Basel)"
    elif observed_rate <= p * 2.5:
        zone = "🟡 YELLOW (Cần theo dõi)"
    else:
        zone = "🔴 RED (Phải nâng vốn dự phòng)"
    
    return {
        "test": "Kupiec POF",
        "n_observations": n,
        "n_violations": x,
        "expected_violation_rate": round(p, 4),
        "observed_violation_rate": round(observed_rate, 4),
        "lr_statistic": round(float(lr), 4),
        "p_value": round(p_value, 6),
        "reject_h0": p_value < 0.05,
        "conclusion": "BÁC BỎ (Mô hình VaR không chính xác)" if p_value < 0.05
                      else "CHẤP NHẬN (Mô hình VaR đạt chuẩn)",
        "basel_zone": zone,
    }


def christoffersen_interval_test(violation_sequence: list[int]) -> dict:
    """
    Christoffersen's Interval Forecast Test (Conditional Coverage).
    
    Không chỉ kiểm tra TỶ LỆ vi phạm (Kupiec), mà còn kiểm tra
    TÍNH ĐỘC LẬP giữa các vi phạm (không cluster liên tiếp).
    
    Ý nghĩa: Nếu vi phạm xảy ra liên tiếp nhiều ngày → mô hình VaR
    không nắm bắt được Volatility Clustering → FAIL.
    
    Ma trận chuyển đổi (Transition Matrix):
        T = [[n_00, n_01],   (0→0: an toàn→an toàn, 0→1: an toàn→vi phạm)
             [n_10, n_11]]   (1→0: vi phạm→an toàn, 1→1: vi phạm→vi phạm)
    
    H₀: Xác suất vi phạm không phụ thuộc vào trạng thái hôm trước.
    LR_IND ~ χ²(1)
    """
    from scipy import stats
    
    seq = np.array(violation_sequence)
    if len(seq) < 10:
        return {"error": "Cần ít nhất 10 quan sát."}
    
    # Đếm transition matrix
    n_00 = n_01 = n_10 = n_11 = 0
    for i in range(1, len(seq)):
        prev, curr = seq[i-1], seq[i]
        if prev == 0 and curr == 0: n_00 += 1
        elif prev == 0 and curr == 1: n_01 += 1
        elif prev == 1 and curr == 0: n_10 += 1
        elif prev == 1 and curr == 1: n_11 += 1
    
    eps = 1e-10
    
    # Xác suất chuyển đổi
    pi_01 = n_01 / max(n_00 + n_01, 1)  # P(violation | prev safe)
    pi_11 = n_11 / max(n_10 + n_11, 1)  # P(violation | prev violation)
    pi = (n_01 + n_11) / max(len(seq) - 1, 1)  # Unconditional P(violation)
    
    # Log-likelihood under independence (H₀)
    pi_c = np.clip(pi, eps, 1 - eps)
    ll_ind = (n_00 + n_10) * np.log(1 - pi_c) + (n_01 + n_11) * np.log(pi_c)
    
    # Log-likelihood under dependence (H₁)
    pi_01_c = np.clip(pi_01, eps, 1 - eps)
    pi_11_c = np.clip(pi_11, eps, 1 - eps)
    ll_dep = 0.0
    if n_00 + n_01 > 0:
        ll_dep += n_00 * np.log(1 - pi_01_c) + n_01 * np.log(pi_01_c)
    if n_10 + n_11 > 0:
        ll_dep += n_10 * np.log(1 - pi_11_c) + n_11 * np.log(pi_11_c)
    
    lr_ind = -2 * (ll_ind - ll_dep)
    p_value = float(1 - stats.chi2.cdf(max(lr_ind, 0), df=1))
    
    is_clustered = pi_11 > pi_01 * 1.5
    
    return {
        "test": "Christoffersen Independence",
        "transition_matrix": {"n_00": n_00, "n_01": n_01, "n_10": n_10, "n_11": n_11},
        "p_violation_after_safe": round(pi_01, 4),
        "p_violation_after_violation": round(pi_11, 4),
        "lr_independence": round(float(lr_ind), 4),
        "p_value": round(p_value, 6),
        "reject_h0": p_value < 0.05,
        "violations_clustered": is_clustered,
        "conclusion": (
            "BÁC BỎ (Vi phạm có tính cụm — Volatility Clustering not captured)"
            if p_value < 0.05
            else "CHẤP NHẬN (Vi phạm phân tán độc lập — Mô hình tốt)"
        ),
    }


# ══════════════════════════════════════════════════════════
#  8. AMIHUD ILLIQUIDITY (Rủi ro Thanh khoản)
# ══════════════════════════════════════════════════════════

def amihud_illiquidity(returns: pd.Series, volume: pd.Series, window: int = 20) -> dict:
    """
    Amihud Illiquidity Ratio (2002).
    
    Công thức: ILLIQ_t = (1/D) · Σ(|R_d| / VOLD_d)
    
    Ý nghĩa kinh tế:
        - Đo lường "tác động giá" (Price Impact) của mỗi đơn vị khối lượng.
        - ILLIQ cao → Cổ phiếu kém thanh khoản → Khi bán ra, giá bị trượt nhiều.
        - ILLIQ thấp → Thanh khoản tốt → An toàn khi vào/ra lệnh lớn.
    
    Trong thị trường ASEAN, đây là "kẻ giết người thầm lặng".
    Một cổ phiếu có thể rẻ (P/E thấp) nhưng nếu ILLIQ cao, bạn không thể
    bán ra lúc cần → kẹt vốn.
    
    Args:
        returns: Chuỗi lợi nhuận hàng ngày.
        volume: Chuỗi khối lượng giao dịch (VND hoặc cổ phiếu).
        window: Cửa sổ tính rolling (mặc định 20 ngày = 1 tháng giao dịch).
    """
    if returns.empty or volume.empty or len(returns) < window:
        return {"error": "Không đủ dữ liệu để tính Amihud."}
    
    # Tránh chia cho 0
    vol_safe = volume.replace(0, np.nan)
    
    # Vectorized: |R| / Volume
    daily_illiq = returns.abs() / vol_safe
    
    # Rolling mean
    rolling_illiq = daily_illiq.rolling(window=window).mean()
    
    current = float(rolling_illiq.iloc[-1]) if not np.isnan(rolling_illiq.iloc[-1]) else None
    avg = float(rolling_illiq.mean())
    
    # Phân loại thanh khoản
    if current is not None:
        if current < avg * 0.5:
            liquidity_grade = "🟢 THANH KHOẢN TỐT"
        elif current < avg * 1.5:
            liquidity_grade = "🟡 THANH KHOẢN TRUNG BÌNH"
        else:
            liquidity_grade = "🔴 THANH KHOẢN KÉM (Cẩn thận trượt giá)"
    else:
        liquidity_grade = "N/A"
    
    return {
        "indicator": "Amihud Illiquidity Ratio",
        "current_illiq": round(current, 10) if current else None,
        "historical_avg": round(avg, 10),
        "window_days": window,
        "liquidity_grade": liquidity_grade,
    }


# ══════════════════════════════════════════════════════════
#  9. HMM MODEL SELECTION (AIC/BIC cho số trạng thái)
# ══════════════════════════════════════════════════════════

def hmm_select_n_states(returns: pd.Series, max_states: int = 5) -> dict:
    """
    Chọn số trạng thái tối ưu cho HMM bằng AIC và BIC.
    
    AIC = -2·ln(L) + 2·k
    BIC = -2·ln(L) + k·ln(n)
    
    Trong đó:
        - L: Log-likelihood của model.
        - k: Số tham số (phụ thuộc vào n_states).
        - n: Số quan sát.
    
    Quy tắc: Chọn n_states có BIC THẤP NHẤT.
    BIC phạt nặng hơn AIC → ưu tiên mô hình đơn giản (Occam's Razor).
    """
    from hmmlearn.hmm import GaussianHMM
    
    if returns.empty or len(returns) < 100:
        return {"error": "Cần ít nhất 100 quan sát để chọn HMM."}
    
    clean = returns.dropna().values.reshape(-1, 1)
    n_obs = len(clean)
    
    results = []
    for n in range(2, max_states + 1):
        try:
            model = GaussianHMM(
                n_components=n, covariance_type="full",
                n_iter=200, random_state=42, tol=1e-4,
            )
            model.fit(clean)
            log_likelihood = float(model.score(clean))
            
            # k = n_states² - n_states (transition) + 2·n_states (means + vars) - 1
            k = n * n - n + 2 * n - 1
            aic = -2 * log_likelihood + 2 * k
            bic = -2 * log_likelihood + k * np.log(n_obs)
            
            results.append({
                "n_states": n,
                "log_likelihood": round(log_likelihood, 2),
                "aic": round(aic, 2),
                "bic": round(bic, 2),
                "n_params": k,
            })
        except Exception:
            continue
    
    if not results:
        return {"error": "Không fit được HMM nào."}
    
    best_bic = min(results, key=lambda x: x["bic"])
    best_aic = min(results, key=lambda x: x["aic"])
    
    return {
        "all_models": results,
        "best_by_bic": best_bic,
        "best_by_aic": best_aic,
        "recommendation": f"Dùng {best_bic['n_states']} trạng thái (BIC thấp nhất = {best_bic['bic']})",
        "n_observations": n_obs,
    }


# ══════════════════════════════════════════════════════════
#  10. STRESS TESTING (Kịch bản Thiên Nga Đen)
# ══════════════════════════════════════════════════════════

def stress_test_portfolio(
    returns: pd.Series,
    scenarios: dict[str, float] | None = None,
) -> dict:
    """
    Stress Testing — Đánh giá danh mục dưới các kịch bản cực đoan.
    
    Phương pháp: Áp shock multiplier lên chuỗi returns gần nhất,
    sau đó tái tính VaR, CVaR, Drawdown.
    
    Scenarios mặc định mô phỏng các sự kiện lịch sử:
        - COVID Crash (2020):  -7% / ngày
        - Lehman (2008):       -9% / ngày
        - ASEAN Crisis (1997): -12% / ngày
        - Black Monday (1987): -22% / ngày
        - FX Shock +5%:        Tác động gián tiếp qua beta
    """
    if returns.empty or len(returns) < 30:
        return {"error": "Cần ít nhất 30 quan sát."}
    
    if scenarios is None:
        scenarios = {
            "COVID-19 Crash (-7%/ngày)": -0.07,
            "Lehman Brothers (-9%/ngày)": -0.09,
            "ASEAN Crisis 1997 (-12%/ngày)": -0.12,
            "Black Monday 1987 (-22%/ngày)": -0.22,
            "Mild Correction (-3%/ngày)": -0.03,
        }
    
    results = []
    current_price = 100  # Normalize
    
    for name, shock in scenarios.items():
        # Tạo chuỗi returns giả lập: shock ngày đầu + tiếp tục với phân phối gốc
        simulated = returns.copy()
        sim_returns = pd.concat([pd.Series([shock]), simulated.tail(20)]).reset_index(drop=True)
        
        cumulative = (1 + sim_returns).cumprod()
        max_dd = float(((cumulative / cumulative.expanding().max()) - 1).min())
        
        portfolio_value_after = current_price * (1 + shock)
        recovery_days = _estimate_recovery_days(returns, shock)
        
        results.append({
            "scenario": name,
            "shock_pct": round(shock * 100, 2),
            "portfolio_value_after": round(portfolio_value_after, 2),
            "loss_amount_per_100": round((current_price - portfolio_value_after), 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "estimated_recovery_days": recovery_days,
        })
    
    return {
        "stress_test": results,
        "worst_case": min(results, key=lambda x: x["shock_pct"]),
        "note": "Stress test dựa trên các sự kiện lịch sử. Kết quả mang tính ước lượng.",
    }


def _estimate_recovery_days(returns: pd.Series, shock: float) -> int:
    """Ước lượng số ngày phục hồi dựa trên mean daily return."""
    mean_daily = float(returns.mean())
    if mean_daily <= 0:
        return 999  # Không phục hồi được nếu mean ≤ 0
    return int(abs(shock) / mean_daily)

