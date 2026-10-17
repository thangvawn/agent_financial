import React, { useState } from 'react';

export default function SimLabVisualBuilder({ onApplyToQuantaCode }) {
  const [fastPeriod, setFastPeriod] = useState(9);
  const [slowPeriod, setSlowPeriod] = useState(21);
  const [takeProfit, setTakeProfit] = useState(8);
  const [stopLoss, setStopLoss] = useState(4);
  const [trailing, setTrailing] = useState(2.5);
  const [positionSize, setPositionSize] = useState(30);

  const handleSyncToDSL = () => {
    const generatedDSL = `strategy:
  name: "Visual Custom Strategy"
  description: "Chiến lược sinh tự động từ Visual Builder"

universe:
  symbols: ["VN30"]
  liquidity_min: "10B"

params:
  fast_period: ${fastPeriod}
  slow_period: ${slowPeriod}
  take_profit_pct: ${takeProfit}
  stop_loss_pct: ${stopLoss}
  trailing_stop: ${trailing}

entry:
  when:
    - "EMA(fast_period) crosses_above EMA(slow_period)"
    - "volume > SMA(volume, 20) * 1.2"
  action: "BUY_MARKET"
  allocation: "${positionSize}%"

exit:
  when:
    - "gain >= take_profit_pct"
    - "loss >= stop_loss_pct"
    - "drawdown_from_peak >= trailing_stop"
  action: "SELL_MARKET"

risk:
  max_portfolio_risk: "2%"
  settlement_rule: "T+2"
`;
    if (onApplyToQuantaCode) {
      onApplyToQuantaCode(generatedDSL);
    }
  };

  return (
    <div className="simlab-visual-builder">
      <div className="builder-header">
        <div className="builder-title">
          <h3>Trình Thiết Kế Chiến Lược Trực Quan (Visual Block Builder)</h3>
          <p>Thiết lập điều kiện vào/ra lệnh bằng khối tham số và tự động dịch sang mã Quanta DSL.</p>
        </div>
        <button type="button" className="sync-dsl-btn" onClick={handleSyncToDSL}>
          <span>Đồng bộ sang Quanta DSL ➔</span>
        </button>
      </div>

      <div className="builder-blocks-grid">
        <div className="builder-card">
          <div className="card-badge">Khối 01: Vũ trụ & Tín hiệu Vào lệnh</div>
          <h4>Entry Rules (Tín hiệu Mua)</h4>
          <div className="card-field">
            <label>Chu kỳ Đường nhanh (Fast EMA): {fastPeriod}</label>
            <input
              type="range"
              min="3"
              max="30"
              value={fastPeriod}
              onChange={(e) => setFastPeriod(Number(e.target.value))}
            />
          </div>
          <div className="card-field">
            <label>Chu kỳ Đường chậm (Slow EMA): {slowPeriod}</label>
            <input
              type="range"
              min="10"
              max="100"
              value={slowPeriod}
              onChange={(e) => setSlowPeriod(Number(e.target.value))}
            />
          </div>
          <div className="rule-preview">
            <code>EMA({fastPeriod}) Cắt lên EMA({slowPeriod}) & Vol &gt; MA20(Vol) * 1.2</code>
          </div>
        </div>

        <div className="builder-card">
          <div className="card-badge">Khối 02: Quản trị Rủi ro & Thoát lệnh</div>
          <h4>Exit Rules (Chốt lời / Cắt lỗ)</h4>
          <div className="card-field">
            <label>Mục tiêu Chốt lời (Take Profit): +{takeProfit}%</label>
            <input
              type="range"
              min="3"
              max="25"
              step="0.5"
              value={takeProfit}
              onChange={(e) => setTakeProfit(Number(e.target.value))}
            />
          </div>
          <div className="card-field">
            <label>Ngưỡng Cắt lỗ (Stop Loss): -{stopLoss}%</label>
            <input
              type="range"
              min="2"
              max="15"
              step="0.5"
              value={stopLoss}
              onChange={(e) => setStopLoss(Number(e.target.value))}
            />
          </div>
          <div className="card-field">
            <label>Trailing Stop từ đỉnh: {trailing}%</label>
            <input
              type="range"
              min="1"
              max="8"
              step="0.5"
              value={trailing}
              onChange={(e) => setTrailing(Number(e.target.value))}
            />
          </div>
        </div>

        <div className="builder-card">
          <div className="card-badge">Khối 03: Phân bổ Vốn & Quy chế Thị trường</div>
          <h4>Vốn & Chu kỳ T+2</h4>
          <div className="card-field">
            <label>Tỷ trọng mỗi lệnh: {positionSize}% danh mục</label>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={positionSize}
              onChange={(e) => setPositionSize(Number(e.target.value))}
            />
          </div>
          <div className="market-note-box">
            <div className="note-title">⚡ Quy chuẩn thị trường Việt Nam</div>
            <p>Khớp lệnh lô chẵn 100 cp, chu kỳ T+2 chiều bán, phí giao dịch 0.15% và thuế TNCN 0.1%.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
