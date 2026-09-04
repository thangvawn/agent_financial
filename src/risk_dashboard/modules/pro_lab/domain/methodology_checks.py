from __future__ import annotations

from typing import Any

from risk_dashboard.modules.pro_lab.schemas.simulation_agent import ReproducibilityManifest


def check_look_ahead_bias(manifest: ReproducibilityManifest) -> list[str]:
    """Kiểm tra rủi ro rò rỉ dữ liệu tương lai (Look-ahead bias / Data leakage)."""
    issues: list[str] = []
    params = manifest.parameters or {}

    # Check for close-price execution on same bar or non-lagged indicators
    if params.get("execute_on_same_bar_close", False):
        issues.append("Rủi ro Look-ahead bias: Khớp lệnh ngay tại giá Close của cùng cây nến tín hiệu (cần dùng Next Open hoặc delay).")

    if params.get("use_future_fundamental_data", False):
        issues.append("Rủi ro Look-ahead bias: Sử dụng dữ liệu BCTC trước ngày công bố chính thức.")

    return issues


def check_survivorship_bias(manifest: ReproducibilityManifest) -> list[str]:
    """Kiểm tra rủi ro thiên vị kẻ sống sót (Survivorship bias)."""
    issues: list[str] = []
    # Check if universe is fixed to current constituents (e.g. current VN30) backfilled 5-10 years
    if "VN30" in manifest.benchmark.upper() and manifest.data_start < "2020-01-01":
        issues.append("Cảnh báo Survivorship bias: Áp dụng danh mục VN30 hiện tại cho giai đoạn trước 2020 mà không điều chỉnh lịch sử thêm/bớt mã.")
    return issues


def check_overfitting_risk(manifest: ReproducibilityManifest, run_count: int = 1) -> list[str]:
    """Kiểm tra rủi ro quá khớp dữ liệu (Overfitting / Curve-fitting)."""
    issues: list[str] = []
    params = manifest.parameters or {}

    if len(params) > 8:
        issues.append(f"Cảnh báo Overfitting: Chiến lược sử dụng quá nhiều tham số tự do ({len(params)} tham số), tăng rủi ro curve-fitting.")

    if run_count >= 15:
        issues.append(f"Cảnh báo Multiple Testing: Đã thực hiện {run_count} lần lặp tham số trên cùng một tập dữ liệu, cần walk-forward validation.")

    return issues


def check_transaction_costs(manifest: ReproducibilityManifest) -> list[str]:
    """Kiểm tra việc tính toán phí giao dịch và trượt giá."""
    issues: list[str] = []
    if manifest.commission_pct <= 0.0:
        issues.append("Thiếu phí giao dịch: Commission = 0% dẫn đến kết quả backtest lạc quan phi thực tế.")
    elif manifest.commission_pct < 0.1:
        issues.append(f"Phí giao dịch ({manifest.commission_pct}%) thấp hơn mức thực tế thị trường VN (~0.15% - 0.25%).")

    if manifest.slippage_pct <= 0.0:
        issues.append("Thiếu trượt giá (Slippage = 0%): Chưa tính độ trượt thanh khoản khi khớp lệnh thị trường/ATC.")
    return issues


def check_benchmark_mismatch(manifest: ReproducibilityManifest, run_benchmark: str = "") -> list[str]:
    """Kiểm tra tính phù hợp của benchmark so với tài sản mục tiêu."""
    issues: list[str] = []
    if run_benchmark and run_benchmark.upper() != manifest.benchmark.upper():
        issues.append(f"Mâu thuẫn benchmark: Manifest khai báo {manifest.benchmark} nhưng kết quả chạy dùng {run_benchmark}.")
    return issues



def run_all_methodology_checks(
    manifest: ReproducibilityManifest,
    run_count: int = 1,
    run_benchmark: str = "",
) -> list[str]:
    """Chạy toàn bộ các kiểm tra phương pháp luận trước và sau simulation."""
    findings: list[str] = []
    findings.extend(check_look_ahead_bias(manifest))
    findings.extend(check_survivorship_bias(manifest))
    findings.extend(check_overfitting_risk(manifest, run_count=run_count))
    findings.extend(check_transaction_costs(manifest))
    findings.extend(check_benchmark_mismatch(manifest, run_benchmark=run_benchmark))
    return findings
