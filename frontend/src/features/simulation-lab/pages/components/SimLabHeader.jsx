const POPULAR_TICKERS = [
  'FPT', 'HPG', 'SSI', 'MWG', 'VNM', 'VCB', 'MBB', 'TCB', 'VIC', 'DGC', 'VND', 'VNINDEX'
];

export default function SimLabHeader({
  ticker,
  setTicker,
  interval = '1d',
  setInterval,
  period = '1y',
  setPeriod,
  mode,
  setMode,
  onRun,
  isRunning,
  marketSourceInfo,
  onOpenCopilot,
  onOpenBlueprintModal,
}) {
  return (
    <header className="simlab-header">
      <div className="simlab-header-left">
        <div className="simlab-branding">
          <div className="branding-icon">⚡</div>
          <div className="branding-text">
            <h2>Quanta Studio</h2>
            <span className="branding-sub">Quantitative Research & Backtest Lab</span>
          </div>
        </div>

        <div className="simlab-controls">
          <div className="control-group">
            <label htmlFor="ticker-select">Mã CK</label>
            <select
              id="ticker-select"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              className="simlab-select ticker-select"
            >
              {POPULAR_TICKERS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label htmlFor="interval-select">Khung nến</label>
            <select
              id="interval-select"
              value={interval}
              onChange={(e) => setInterval && setInterval(e.target.value)}
              className="simlab-select interval-select"
            >
              <option value="1d">1D (Ngày)</option>
              <option value="1wk">1W (Tuần)</option>
              <option value="1h">1H (Giờ)</option>
            </select>
          </div>

          <div className="control-group">
            <label htmlFor="period-select">Khoảng</label>
            <select
              id="period-select"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="simlab-select period-select"
            >
              <option value="1y">1 Năm (1Y)</option>
              <option value="2y">2 Năm (2Y)</option>
              <option value="3y">3 Năm (3Y • ~750 nến)</option>
              <option value="5y">5 Năm (5Y • ~1.300 nến)</option>
              <option value="10y">10 Năm (10Y • ~2.600 nến)</option>
              <option value="max">Toàn bộ (MAX • 15Y+ ~4.000 nến)</option>
              <option value="6mo">6 Tháng (6M)</option>
              <option value="3mo">3 Tháng (3M)</option>
            </select>
          </div>

          {marketSourceInfo && (
            <div
              className={`feed-indicator ${marketSourceInfo.isReal ? 'real' : 'fallback'}`}
              title={
                marketSourceInfo.isReal
                  ? `Nguồn: ${marketSourceInfo.source.toUpperCase()} (${marketSourceInfo.count} nến thật${marketSourceInfo.firstDate ? ` từ ${marketSourceInfo.firstDate} đến ${marketSourceInfo.lastDate}` : ''})`
                  : 'Dữ liệu mẫu ngoại tuyến'
              }
            >
              <span className="feed-dot" />
              <span>
                {marketSourceInfo.isReal
                  ? `${marketSourceInfo.count} nến thật`
                  : 'Offline'}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="simlab-header-center">
        <nav className="mode-nav-pill">
          <button
            type="button"
            className={`mode-btn ${mode === 'studio' ? 'active' : ''}`}
            onClick={() => setMode('studio')}
            title="Môi trường code Quanta DSL & Sliders tương tác"
          >
            Quanta Studio
          </button>
          <button
            type="button"
            className={`mode-btn ${mode === 'visual' ? 'active' : ''}`}
            onClick={() => setMode('visual')}
            title="Bộ khối kéo thả điều kiện chiến lược"
          >
            Visual Builder
          </button>
          <button
            type="button"
            className={`mode-btn ${mode === 'tearsheet' ? 'active' : ''}`}
            onClick={() => setMode('tearsheet')}
            title="Báo cáo phân tích hiệu suất và lệnh chi tiết"
          >
            Quant Tearsheet
          </button>
        </nav>
      </div>

      <div className="simlab-header-right">
        {onOpenBlueprintModal && (
          <button
            type="button"
            className="copilot-action-btn"
            onClick={onOpenBlueprintModal}
            title="Quản lý và lưu bản thiết kế chiến lược cá nhân"
          >
            <span>📁</span>
            <span>Bản Lưu</span>
          </button>
        )}

        <button
          type="button"
          className="copilot-action-btn"
          onClick={onOpenCopilot}
          title="Trợ lý AI tối ưu tham số & soát lỗi chiến lược"
        >
          <span className="copilot-sparkle">✦</span>
          <span>AI Copilot</span>
        </button>

        <button
          type="button"
          className={`run-backtest-btn ${isRunning ? 'running' : ''}`}
          onClick={onRun}
          disabled={isRunning}
          title="Thực thi backtest (Phím tắt: F5 hoặc Ctrl+Enter)"
        >
          {isRunning ? (
            <>
              <span className="spinner-icon" />
              <span>Đang tính...</span>
            </>
          ) : (
            <>
              <span className="run-icon">▶</span>
              <span>Chạy Backtest</span>
              <kbd className="kbd-shortcut">F5</kbd>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
