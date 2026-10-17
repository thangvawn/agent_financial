/**
 * Symbol mapping from North Star internal symbols to TradingView exchange:symbol format.
 */
export const SYMBOL_MAP = {
  // Commodities
  XAU: 'OANDA:XAUUSD',
  GOLD: 'OANDA:XAUUSD',
  WTI: 'TVC:USOIL',
  BRENT: 'TVC:UKOIL',
  SILVER: 'OANDA:XAGUSD',
  COPPER: 'CAPITALCOM:COPPER',
  NATGAS: 'TVC:NGAS',

  // Global Indices
  SPX: 'FOREXCOM:SPXUSD',
  NDX: 'NASDAQ:NDX',
  DJI: 'DJ:DJI',
  DAX: 'INDEX:DAX',
  FTSE: 'INDEX:FTSE',
  NIKKEI: 'INDEX:NKY',
  HANGSENG: 'INDEX:HSI',
  KOSPI: 'INDEX:KS11',
  SSEC: 'INDEX:SSEC',

  // FX / Currencies
  DXY: 'TVC:DXY',
  EUR: 'FX:EURUSD',
  EURUSD: 'FX:EURUSD',
  JPY: 'FX:USDJPY',
  USDJPY: 'FX:USDJPY',
  GBP: 'FX:GBPUSD',
  GBPUSD: 'FX:GBPUSD',
  AUD: 'FX:AUDUSD',
  USDVND: 'FX_IDC:USDVND',

  // Crypto
  BTC: 'BINANCE:BTCUSDT',
  ETH: 'BINANCE:ETHUSDT',
  BNB: 'BINANCE:BNBUSDT',
  SOL: 'BINANCE:SOLUSDT',
  XRP: 'BINANCE:XRPUSDT',
  DOGE: 'BINANCE:DOGEUSDT',
  ADA: 'BINANCE:ADAUSDT',
  TRX: 'BINANCE:TRXUSDT',
  LINK: 'BINANCE:LINKUSDT',
  AVAX: 'BINANCE:AVAXUSDT',
  SUI: 'BINANCE:SUIUSDT',
  NEAR: 'BINANCE:NEARUSDT',
  DOT: 'BINANCE:DOTUSDT',
  PEPE: 'BINANCE:PEPEUSDT',
  LTC: 'BINANCE:LTCUSDT',
  BCH: 'BINANCE:BCHUSDT',
  UNI: 'BINANCE:UNIUSDT',
  APT: 'BINANCE:APTUSDT',
  ARB: 'BINANCE:ARBUSDT',
  OP: 'BINANCE:OPUSDT',
  FIL: 'BINANCE:FILUSDT',
  ICP: 'BINANCE:ICPUSDT',
  HBAR: 'BINANCE:HBARUSDT',
  XLM: 'BINANCE:XLMUSDT',
  TON: 'BINANCE:TONUSDT',
  SHIB: 'BINANCE:SHIBUSDT',
  MKR: 'BINANCE:MKRUSDT',
  INJ: 'BINANCE:INJUSDT',

  // VN Indices & Stocks
  VNINDEX: 'INDEX:VNINDEX',
  VN30: 'INDEX:VN30',
  HNXINDEX: 'INDEX:HNX',
  HNX: 'INDEX:HNX',
  UPCOM: 'HNX:UPCOMINDEX',
  UPCOMINDEX: 'HNX:UPCOMINDEX',
}

export const TRADINGVIEW_SUPPORTED_SYMBOLS = new Set([
  // Commodities
  'XAU', 'GOLD', 'WTI', 'BRENT', 'SILVER', 'COPPER', 'PLATINUM', 'PALLADIUM', 'NATGAS',
  'CORN', 'WHEAT', 'SOYBEAN', 'SUGAR', 'COFFEE', 'COCOA', 'COTTON', 'HEATINGOIL', 'GASOLINE',
  'OATS', 'RICE', 'LIVE_CATTLE', 'FEEDER_CATTLE', 'LEAN_HOGS', 'ORANGE_JUICE',

  // Global Indices
  'SPX', 'NDX', 'DJI', 'RUT', 'NASDAQ', 'DAX', 'EUROSTOXX', 'CAC40', 'FTSE', 'NIKKEI',
  'HANGSENG', 'KOSPI', 'ASX200', 'TSX', 'BOVESPA', 'NIFTY50', 'SSEC',

  // FX / Currencies
  'DXY', 'EUR', 'EURUSD', 'JPY', 'USDJPY', 'GBP', 'GBPUSD', 'AUD', 'AUDUSD', 'USDCNH',
  'USDCHF', 'USDCAD', 'NZDUSD', 'USDHKD', 'USDMXN', 'USDTRY', 'USDINR', 'EURGBP', 'EURJPY',
  'USDVND',

  // Crypto
  'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'USDT', 'USDC', 'DOGE', 'ADA', 'TRX', 'LINK',
  'AVAX', 'SUI', 'NEAR', 'DOT', 'PEPE', 'LTC', 'BCH', 'UNI', 'APT', 'ARB', 'OP',
  'FIL', 'ICP', 'HBAR', 'XLM', 'TON', 'SHIB', 'MKR', 'INJ', 'CRO',

  // Major global tech/stocks
  'AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'META'
])

export function isTradingViewSupported(symbol = '') {
  if (!symbol) return false
  const norm = String(symbol).toUpperCase().trim()
  return TRADINGVIEW_SUPPORTED_SYMBOLS.has(norm)
}

export function resolveTradingViewSymbol(symbol = '') {
  const norm = String(symbol).toUpperCase().trim()
  if (SYMBOL_MAP[norm]) return SYMBOL_MAP[norm]
  // If it's a 3-letter VN stock, prefix with HOSE
  if (/^[A-Z]{3}$/.test(norm)) {
    return `HOSE:${norm}`
  }
  return norm
}
