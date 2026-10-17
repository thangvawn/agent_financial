/**
 * 6 Classic Quant Strategy Presets for Quanta Workshop Studio (< 200 lines)
 */

export const QUANTA_STRATEGY_PRESETS = [
  {
    id: 'aurora-pulse',
    name: 'Aurora Liquidity Pulse v2',
    category: 'Momentum & Volatility',
    ticker: 'FPT',
    timeframe: '1D',
    description: 'Chiến lược cốt lõi kết hợp EMA Trend Cross, RSI Filter và ATR Volatility Breath.',
    code: `strategy "Aurora Liquidity Pulse v2"
@watchlist  "FPT, VNM, HPG"
@timeframe  "1D"
@regime     "trending"
@style      "momentum"

params:
  fast_len = 21 in [5..80]
  slow_len = 55 in [20..200]
  atr_len = 14 in [7..50]
  risk_size = 6pct in [1pct..20pct]

detect:
  c = market.close
  h = market.high
  l = market.low
  fast = ema(c, fast_len)
  slow = ema(c, slow_len)
  drift = fast - slow
  pulse = rsi(c, 14)
  breath = atr(h, l, c, atr_len)
  long_setup = fast crossover slow and pulse < 72
  take_profit = pulse > 78
  stop_line = slow - 1.8 * breath

score:
  sig_score = 0.85 when long_setup else (0.35 when c > fast else -0.35)

act:
  when long_setup and not position.is_long:
    enter long with size risk_size tag "Aurora Entry"
  when position.is_long and (take_profit or c < stop_line):
    close long tag "Aurora Exit"

render:
  panel main:
    line fast as "Fast EMA" in cyan
    line slow as "Slow EMA" in amber
    mark long_setup as "BUY" at below_bar in lime shaped arrow_up
  panel pulse:
    hist drift as "Drift" in purple
    line pulse as "RSI" in teal
    level 70 in red dashed
    level 30 in green dashed`,
  },
  {
    id: 'tide-cross',
    name: 'Tide Reclaim Pulse (EMA Cross)',
    category: 'Trend Following',
    ticker: 'HPG',
    timeframe: '1D',
    description: 'Bắt sóng trung hạn khi EMA ngắn cắt lên EMA dài kết hợp quản trị vốn wnav 5%.',
    code: `strategy "Tide Reclaim Pulse"
@regime "trending"
@style "momentum"

params:
  fast_len = 20 in [5..100]
  slow_len = 50 in [20..200]
  risk_pct = 5pct in [1pct..20pct]

detect:
  c = market.close
  tide_fast = ema(c, fast_len)
  tide_slow = ema(c, slow_len)
  long_setup = tide_fast crossover tide_slow
  short_setup = tide_fast crossunder tide_slow

act:
  when long_setup and not position.is_long:
    enter long with wnav risk_pct tag "Tide Long"
  when short_setup and position.is_long:
    close long tag "Trend Lost"

render:
  panel main:
    line tide_fast as "Fast Tide" in cyan
    line tide_slow as "Slow Tide" in amber
    mark long_setup as "LONG" at below_bar in lime shaped arrow_up`,
  },
  {
    id: 'turtle-breakout',
    name: 'Turtle Donchian Breakout',
    category: 'Breakout',
    ticker: 'SSI',
    timeframe: '1D',
    description: 'Chiến lược Turtle kinh điển: mua khi giá vượt đỉnh n phiên và thoát khi thủng đáy.',
    code: `strategy "Turtle Donchian Breakout"
@style "breakout"

params:
  channel_len = 20 in [10..60]
  exit_len = 10 in [5..30]

detect:
  c = market.close
  h = market.high
  l = market.low
  upper = donchian(h, l, channel_len).upper
  lower = donchian(h, l, exit_len).lower
  breakout_up = c > upper[1]
  breakout_down = c < lower[1]

act:
  when breakout_up and not position.is_long:
    enter long with wnav 8pct tag "Turtle Enter"
  when breakout_down and position.is_long:
    close long tag "Turtle Exit"

render:
  panel main:
    line upper as "Upper Channel" in cyan
    line lower as "Lower Exit" in red
    mark breakout_up as "BREAKOUT" at below_bar in lime shaped triangle_up`,
  },
  {
    id: 'bollinger-squeeze',
    name: 'Bollinger Band Squeeze',
    category: 'Mean Reversion',
    ticker: 'VNM',
    timeframe: '1D',
    description: 'Khai thác thời điểm dải Bollinger thắt hẹp trước khi bùng nổ xung lực.',
    code: `strategy "Bollinger Band Squeeze"
@style "mean_reversion"

params:
  bb_len = 20 in [10..50]
  bb_mult = 2.0 in [1.5..3.0]
  rsi_filter = 14 in [7..28]

detect:
  c = market.close
  bb = bbands(c, bb_len, bb_mult)
  r = rsi(c, rsi_filter)
  oversold = c < bb.lower and r < 35
  overbought = c > bb.upper or r > 70

act:
  when oversold and not position.is_long:
    enter long with wnav 5pct tag "BB Squeeze Buy"
  when overbought and position.is_long:
    close long tag "BB Exit"

render:
  panel main:
    band bb as "Bollinger Bands" in blue dotted with opacity 10pct
    mark oversold as "OVERSOLD" at below_bar in teal shaped circle`,
  },
];

export const DEFAULT_QUANTA_CODE = QUANTA_STRATEGY_PRESETS[0].code;
