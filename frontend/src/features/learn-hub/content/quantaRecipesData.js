export const QUANTA_RECIPES_DATA = {
  "first-strategy": {
    "title": "Bài 1 — EMA cross",
    "tags": [
      "trend",
      "beginner",
      "act"
    ],
    "demo_code": "strategy \"EMA Cross Starter\"\n@regime \"trending\"\n@style \"trend-following\"\n\nparams:\n  fast_len = 20 in [5..50]\n  slow_len = 50 in [20..200]\n  risk_pct = 5pct in [1pct..10pct]\n\ndetect:\n  c = market.close\n  fast = ema(c, fast_len)\n  slow = ema(c, slow_len)\n  buy_signal = fast crossover slow\n  sell_signal = fast crossunder slow\n\nact:\n  when buy_signal and not position.is_long:\n    enter long with wnav risk_pct tag \"EMA Golden Cross\"\n  when sell_signal and position.is_long:\n    close long tag \"EMA Death Cross\"\n\nrender:\n  panel main:\n    line fast as \"EMA Fast\" in cyan\n    line slow as \"EMA Slow\" in amber\n    mark buy_signal as \"BUY\" at below_bar in lime shaped arrow_up\n    mark sell_signal as \"SELL\" at above_bar in red shaped arrow_down",
    "body": "Chiến lược kinh điển giao cắt đường trung bình động hàm mũ (EMA). Khi đường nhanh vượt lên trên đường chậm, hệ thống mở vị thế Mua với tỷ trọng 5% NAV. Khi cắt xuống, hệ thống tất toán vị thế."
  },
  "bb-rsi-study": {
    "title": "Bài 2 — Study đa panel: BB + RSI",
    "tags": [
      "study",
      "momentum",
      "volatility"
    ],
    "demo_code": "study \"BB + RSI Multi-Panel\"\n\ndetect:\n  c = market.close\n  bb = bbands(c, 20, 2.0)\n  r = rsi(c, 14)\n\nrender:\n  panel main:\n    line bb.upper as \"BB Upper\" in cyan dashed\n    line bb.mid as \"BB Mid\" in white\n    line bb.lower as \"BB Lower\" in cyan dashed\n    band bb.upper to bb.lower as \"BB Cloud\" in cyan with opacity 8pct\n  panel rsi:\n    line r as \"RSI 14\" in amber\n    level 70 as \"Overbought\" in red dashed\n    level 30 as \"Oversold\" in lime dashed",
    "body": "Dùng từ khóa `study` để chỉ vẽ biểu đồ phân tích kỹ thuật mà không kích hoạt đặt lệnh tự động. Mỗi `panel` có trục tọa độ độc lập."
  },
  "regime-mean-reversion": {
    "title": "Bài 3 — Mean reversion + regime",
    "tags": [
      "mean-reversion",
      "sideway",
      "intermediate"
    ],
    "demo_code": "strategy \"Mean Reversion with ADX Regime\"\n@regime \"sideway\"\n@style \"contrarian\"\n\nparams:\n  rsi_len = 14 in [7..28]\n  adx_threshold = 20 in [15..30]\n\ndetect:\n  c = market.close\n  h = market.high\n  l = market.low\n  r = rsi(c, rsi_len)\n  trend_strength = adx(h, l, c, 14)\n  is_sideway = trend_strength < adx_threshold\n  oversold = r < 30\n  overbought = r > 70\n\nact:\n  when is_sideway and oversold and not position.is_long:\n    enter long with wnav 8pct tag \"Oversold Bounce\"\n  when overbought and position.is_long:\n    close long tag \"Overbought Target\"",
    "body": "Bộ lọc chế độ thị trường (Regime filter) sử dụng ADX. Chiến lược chỉ kích hoạt bắt đáy khi ADX < 20 (thị trường đi ngang, không có xu hướng mạnh) nhằm tránh bẫy bắt dao rơi khi downtrend."
  },
  "breakout-with-volume": {
    "title": "Bài 4 — Donchian + volume",
    "tags": [
      "breakout",
      "volume",
      "intermediate"
    ],
    "demo_code": "strategy \"Turtle Donchian Breakout\"\n@regime \"breakout\"\n@style \"momentum\"\n\nparams:\n  channel_len = 20 in [10..55]\n  vol_multiplier = 1.5 in [1.0..3.0]\n\ndetect:\n  c = market.close\n  h = market.high\n  v = market.volume\n  upper_band = hhv(h, channel_len)\n  vol_ma = sma(v, 20)\n  vol_spike = v > vol_ma * vol_multiplier\n  breakout = c > upper_band[1] and vol_spike\n\nact:\n  when breakout and not position.is_long:\n    enter long with wnav 10pct tag \"Vol Breakout\"",
    "body": "Chiến lược breakout trường phái Rùa (Turtle Trader) cải tiến với điều kiện Volume xác nhận (Vol spike > 150% trung bình 20 phiên) để lọc tín hiệu phá vỡ giả (Bull trap)."
  },
  "exit-management": {
    "title": "Bài 5 — Trailing ATR exit",
    "tags": [
      "risk",
      "trailing-stop",
      "exit"
    ],
    "demo_code": "strategy \"Trailing ATR Protector\"\n@regime \"trending\"\n@style \"trend\"\n\nparams:\n  atr_mult = 2.5 in [1.5..4.0]\n\ndetect:\n  c = market.close\n  h = market.high\n  l = market.low\n  volatility = atr(h, l, c, 14)\n  trailing_stop = hhv(c, 10) - (volatility * atr_mult)\n\nact:\n  when position.is_long and c < trailing_stop:\n    close long tag \"ATR Trailing Stop\"",
    "body": "Hệ thống dừng lỗ động (Trailing stop) bám sát theo độ biến động thực tế của cổ phiếu thay vì mức cố định. Khi giá tăng, ngưỡng cắt lỗ được nâng dần lên để bảo vệ lợi nhuận."
  },
  "pivot-trendline-chart": {
    "title": "Bài 6 — Pivot + trendline",
    "tags": [
      "pivot",
      "charting",
      "advanced"
    ],
    "demo_code": "study \"Auto Pivot High Low\"\n\ndetect:\n  h = market.high\n  l = market.low\n  sh = swinghigh(h, 5, 5)\n  sl = swinglow(l, 5, 5)\n\nrender:\n  panel main:\n    mark sh as \"H\" at above_bar in red shaped circle\n    mark sl as \"L\" at below_bar in lime shaped circle",
    "body": "Tự động phát hiện các đỉnh swing high và đáy swing low với lookback 5 nến trước và 5 nến sau để phục vụ phân tích cấu trúc thị trường (Market Structure)."
  },
  "momentum-12-1": {
    "title": "Ví dụ — Momentum 12-1",
    "tags": [
      "factor",
      "long-term"
    ],
    "demo_code": "study \"Momentum 12 Minus 1 Month\"\n\ndetect:\n  c = market.close\n  mom_12m = pctchange(c, 252)\n  mom_1m = pctchange(c, 21)\n  factor_score = mom_12m - mom_1m\n\nrender:\n  panel factor:\n    line factor_score as \"Mom 12-1 Factor\" in purple",
    "body": "Mô hình nhân tố đà tăng trưởng học thuật (Jegadeesh & Titman): Lấy lợi suất 12 tháng trừ đi lợi suất 1 tháng gần nhất để tránh hiện tượng đảo chiều ngắn hạn."
  },
  "volatility-targeting": {
    "title": "Ví dụ — Volatility targeting",
    "tags": [
      "portfolio",
      "risk-parity"
    ],
    "demo_code": "study \"Target Volatility Allocator\"\n\ndetect:\n  c = market.close\n  current_vol = rollstd(pctchange(c, 1), 20) * sqrt(252)\n  target_vol = 0.15\n  weight = clip(target_vol / safediv(current_vol, 1.0), 0.1, 1.0)\n\nrender:\n  panel weights:\n    line weight as \"NAV Weight Allocation\" in teal",
    "body": "Cân bằng tỷ trọng danh mục theo mục tiêu biến động cố định 15%/năm. Khi thị trường rung lắc mạnh, hệ thống tự động hạ đòn bẩy và tỷ trọng cổ phiếu."
  },
  "multi-condition-marker": {
    "title": "Ví dụ — Marker đa điều kiện",
    "tags": [
      "multi-condition",
      "signals"
    ],
    "demo_code": "study \"Composite Confluence Marker\"\n\ndetect:\n  c = market.close\n  r = rsi(c, 14)\n  vol_surge = market.volume > sma(market.volume, 20) * 2.0\n  rsi_bull = r > 50 and rising(r, 3)\n  confluence = vol_surge and rsi_bull\n\nrender:\n  panel main:\n    mark confluence as \"SURGE\" at below_bar in yellow shaped star",
    "body": "Đánh dấu tín hiệu hợp lưu (Confluence) khi thỏa mãn đồng thời: khối lượng gấp đôi trung bình và RSI bứt phá vượt ngưỡng 50 với 3 phiên dốc lên liên tiếp."
  }
};
