import { useState } from 'react'

export default function SimLabTearsheet({ metrics, trades = [] }) {
  const [filterType, setFilterType] = useState('all');

  if (!metrics) {
    return (
      <div className="tearsheet-empty">
        <p>Chưa có dữ liệu kiểm thử. Hãy nhấn [F5] hoặc Chạy Backtest để xem Tearsheet.</p>
      </div>
    );
  }

  const isPositive = (metrics.totalReturnPct || 0) >= 0;
  const filteredTrades = trades.filter((t) => {
    if (filterType === 'win') return (t.pnl || 0) > 0;
    if (filterType === 'loss') return (t.pnl || 0) < 0;
    return true;
  });

  const cards = [
    {
      label: 'Tổng lợi nhuận',
      val: `${(metrics.totalReturnPct || 0) >= 0 ? '+' : ''}${metrics.totalReturnPct?.toFixed(2)}%`,
      cls: isPositive ? 'profit' : 'loss',
      sub: `Vốn: ${metrics.finalEquity?.toLocaleString('vi-VN')} đ`,
    },
    {
      label: 'CAGR (Hàng năm)',
      val: metrics.cagr == null ? '—' : `${metrics.cagr >= 0 ? '+' : ''}${metrics.cagr.toFixed(2)}%`,
      cls: (metrics.cagr || 0) >= 0 ? 'profit' : 'loss',
      sub: 'Tăng trưởng kép',
    },
    {
      label: 'Sharpe Ratio',
      val: metrics.sharpeRatio?.toFixed(2) ?? '—',
      cls: (metrics.sharpeRatio || 0) >= 1 ? 'accent' : '',
      sub: 'Giả định Rf = 4,5%/năm; — nếu không xác định',
    },
    {
      label: 'Sortino Ratio',
      val: metrics.sortinoRatio?.toFixed(2) ?? '—',
      cls: (metrics.sortinoRatio || 0) >= 1.5 ? 'accent' : '',
      sub: 'Độ lệch giảm so với Rf giả định',
    },
    {
      label: 'Max Drawdown (MDD)',
      val: `-${Math.abs(metrics.maxDrawdown || 0).toFixed(2)}%`,
      cls: 'loss',
      sub: 'Sụt giảm đỉnh sâu nhất',
    },
    {
      label: 'Win Rate / Tỉ lệ thắng',
      val: `${metrics.winRate?.toFixed(1)}%`,
      cls: (metrics.winRate || 0) >= 50 ? 'profit' : '',
      sub: `${metrics.winningTrades || 0}/${metrics.totalTrades || 0} lệnh`,
    },
    {
      label: 'Profit Factor',
      val: metrics.profitFactor?.toFixed(2) ?? '—',
      cls: (metrics.profitFactor || 0) >= 1.5 ? 'profit' : '',
      sub: 'Tổng lãi / Tổng lỗ',
    },
    {
      label: 'Kỳ hạn nắm giữ TB',
      val: `${(metrics.avgHoldingDays || 0).toFixed(1)} ngày`,
      cls: '',
      sub: 'Quy tắc T+2 thị trường VN',
    },
  ];

  return (
    <div className="simlab-tearsheet">
      <div className="tearsheet-header">
        <div className="tearsheet-title-group">
          <h3>Báo Cáo Hiệu Suất Định Lượng (Quant Tearsheet)</h3>
          <span className="tearsheet-badge">Mô phỏng khớp lệnh T+2</span>
        </div>
      </div>

      <div className="tearsheet-grid">
        {cards.map((c, i) => (
          <div key={i} className={`tearsheet-metric-card ${c.cls}`}>
            <span className="metric-label">{c.label}</span>
            <div className="metric-value">{c.val}</div>
            <span className="metric-sub">{c.sub}</span>
          </div>
        ))}
      </div>

      <div className="tearsheet-trades-section">
        <div className="trades-toolbar">
          <h4>Nhật ký giao dịch ({trades.length} lệnh)</h4>
          <div className="filter-pills">
            <button
              type="button"
              className={filterType === 'all' ? 'active' : ''}
              onClick={() => setFilterType('all')}
            >
              Tất cả ({trades.length})
            </button>
            <button
              type="button"
              className={filterType === 'win' ? 'active' : ''}
              onClick={() => setFilterType('win')}
            >
              Lãi ({metrics.winningTrades || 0})
            </button>
            <button
              type="button"
              className={filterType === 'loss' ? 'active' : ''}
              onClick={() => setFilterType('loss')}
            >
              Lỗ ({(metrics.totalTrades || 0) - (metrics.winningTrades || 0)})
            </button>
          </div>
        </div>

        <div className="trades-table-wrap">
          <table className="trades-table">
            <thead>
              <tr>
                <th>Lệnh</th>
                <th>Ngày mua</th>
                <th>Giá mua</th>
                <th>Ngày bán</th>
                <th>Giá bán</th>
                <th>Khối lượng</th>
                <th>Hiệu suất</th>
                <th>PnL (VNĐ)</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-row">
                    Không có lệnh nào thỏa mãn bộ lọc
                  </td>
                </tr>
              ) : (
                filteredTrades.map((t, idx) => {
                  const isWin = (t.pnl || 0) > 0;
                  return (
                    <tr key={idx} className={isWin ? 'win-row' : 'loss-row'}>
                      <td>#{t.id || idx + 1}</td>
                      <td>{typeof t.entryDate === 'number' ? new Date(t.entryDate * 1000).toISOString().slice(0,16).replace('T',' ') : t.entryDate}</td>
                      <td>{t.entryPrice?.toLocaleString('vi-VN')} đ</td>
                      <td>{typeof t.exitDate === 'number' ? new Date(t.exitDate * 1000).toISOString().slice(0,16).replace('T',' ') : t.exitDate || 'Đang giữ'}</td>
                      <td>{t.exitPrice ? `${t.exitPrice.toLocaleString('vi-VN')} đ` : '-'}</td>
                      <td>{t.volume?.toLocaleString('vi-VN')} cp</td>
                      <td className={isWin ? 'profit-text' : 'loss-text'}>
                        {isWin ? '+' : ''}{t.returnPct?.toFixed(2)}%
                      </td>
                      <td className={isWin ? 'profit-text' : 'loss-text'}>
                        {isWin ? '+' : ''}{t.pnl?.toLocaleString('vi-VN')} đ
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
