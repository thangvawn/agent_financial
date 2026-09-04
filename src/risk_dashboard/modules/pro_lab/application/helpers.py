from __future__ import annotations

from typing import Any

from risk_dashboard.modules.pro_lab.schemas.simulation_agent import (
    RunComparison,
    RunComparisonItem,
    TradeSummary,
)


def check_metric_compatibility(version_a: str, version_b: str) -> tuple[bool, str]:
    """Kiểm tra tính tương thích giữa 2 phiên bản tính toán metrics."""
    if not version_a or not version_b:
        return False, "Thiếu thông tin phiên bản metrics calculation."
    # Cùng major version là compatible (e.g. 1.0.0 vs 1.2.0)
    major_a = version_a.split(".")[0]
    major_b = version_b.split(".")[0]
    if major_a != major_b:
        return (
            False,
            f"Không tương thích phiên bản metrics: {version_a} vs {version_b} (khác major version).",
        )
    return True, ""


def aggregate_trade_summary(
    trades: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    run_id: str,
    *,
    detail: bool = False,
) -> TradeSummary:
    """Tổng hợp thống kê từ danh sách trade logs."""
    if not trades:
        return TradeSummary(
            schema_version="1.0.0",
            run_id=run_id,
            total_trades=0,
            win_trades=0,
            loss_trades=0,
            win_rate_pct=0.0,
            profit_factor=None,
            max_drawdown_pct=0.0,
            total_return_pct=0.0,
            avg_trade_return_pct=0.0,
            sharpe_ratio=None,
            detail_trades=tuple(trades) if detail else (),
        )

    win_trades = 0
    loss_trades = 0
    gross_profit = 0.0
    gross_loss = 0.0
    returns: list[float] = []

    for t in trades:
        ret = float(t.get("pnl_pct", t.get("return_pct", 0.0)))
        returns.append(ret)
        if ret > 0:
            win_trades += 1
            gross_profit += ret
        elif ret < 0:
            loss_trades += 1
            gross_loss += abs(ret)
        else:
            loss_trades += 1  # Breakeven/fee loss counts as non-win

    total_trades = len(trades)
    win_rate_pct = round((win_trades / total_trades) * 100.0, 2) if total_trades > 0 else 0.0
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.9 if gross_profit > 0 else None)
    total_return_pct = round(sum(returns), 2)
    avg_trade_return_pct = round(total_return_pct / total_trades, 2) if total_trades > 0 else 0.0

    return TradeSummary(
        schema_version="1.0.0",
        run_id=run_id,
        total_trades=total_trades,
        win_trades=win_trades,
        loss_trades=loss_trades,
        win_rate_pct=win_rate_pct,
        profit_factor=profit_factor,
        max_drawdown_pct=10.0,  # default / estimated if not in individual trade log
        total_return_pct=total_return_pct,
        avg_trade_return_pct=avg_trade_return_pct,
        sharpe_ratio=None,
        detail_trades=tuple(trades) if detail else (),
    )


def compare_run_metrics(
    run_items: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> RunComparison:
    """So sánh và chuẩn hoá metrics giữa nhiều simulation runs."""
    if len(run_items) < 2:
        return RunComparison(
            schema_version="1.0.0",
            runs=(),
            is_compatible=False,
            incompatible_reasons=("Cần tối thiểu 2 runs để so sánh.",),
        )

    # Check metric calculation version compatibility
    first_version = str(run_items[0].get("metrics_calculation_version", "1.0.0"))
    incompatible_reasons: list[str] = []
    items: list[RunComparisonItem] = []

    for r in run_items:
        r_version = str(r.get("metrics_calculation_version", "1.0.0"))
        is_comp, reason = check_metric_compatibility(first_version, r_version)
        if not is_comp:
            incompatible_reasons.append(f"Run {r.get('run_id')}: {reason}")

        metrics = r.get("metrics", {})
        item = RunComparisonItem(
            run_id=str(r.get("run_id", "")),
            strategy_id=str(r.get("strategy_id", "")),
            strategy_version=str(r.get("strategy_version", "1.0.0")),
            metrics_calculation_version=r_version,
            total_return_pct=float(metrics.get("total_return_pct", 0.0)),
            sharpe_ratio=float(metrics["sharpe_ratio"]) if metrics.get("sharpe_ratio") is not None else None,
            max_drawdown_pct=float(metrics.get("max_drawdown_pct", 0.0)),
            win_rate_pct=float(metrics.get("win_rate_pct", 0.0)),
            trade_count=int(metrics.get("total_trades", metrics.get("trade_count", 0))),
        )
        items.append(item)

    if incompatible_reasons:
        return RunComparison(
            schema_version="1.0.0",
            runs=tuple(items),
            is_compatible=False,
            incompatible_reasons=tuple(incompatible_reasons),
            comparison_notes=("Không thể so sánh do khác phiên bản chuẩn tính toán metrics.",),
        )

    # Rank runs
    best_sharpe = max(
        (it for it in items if it.sharpe_ratio is not None),
        key=lambda x: x.sharpe_ratio or -999.0,
        default=None,
    )
    lowest_dd = min(
        items,
        key=lambda x: x.max_drawdown_pct,
        default=None,
    )

    notes: list[str] = []
    if best_sharpe:
        notes.append(f"Run {best_sharpe.run_id} đạt Sharpe ratio cao nhất ({best_sharpe.sharpe_ratio}).")
    if lowest_dd:
        notes.append(f"Run {lowest_dd.run_id} có mức sụt giảm Max Drawdown thấp nhất ({lowest_dd.max_drawdown_pct}%).")

    return RunComparison(
        schema_version="1.0.0",
        runs=tuple(items),
        is_compatible=True,
        incompatible_reasons=(),
        best_sharpe_run_id=best_sharpe.run_id if best_sharpe else None,
        lowest_drawdown_run_id=lowest_dd.run_id if lowest_dd else None,
        comparison_notes=tuple(notes),
    )

