import { memo, useMemo } from 'react'
import { Activity, ArrowDown, ArrowUp, BarChart2, CheckCircle2, ShieldCheck, TrendingUp, Users } from 'lucide-react'

function formatVnPrice(val) {
  if (val === null || val === undefined || Number.isNaN(Number(val))) return '—'
  const num = Number(val)
  // VN stock quotes are typically in thousands of VND (e.g. 115.5 for 115,500 VND) or raw VND
  if (num > 1000) {
    return (num / 1000).toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  return num.toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatVnVol(val) {
  if (val === null || val === undefined || Number.isNaN(Number(val))) return '—'
  const num = Number(val)
  return num.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
}

export function VnOrderBookWidget({ quote = {}, symbol = '' }) {
  const refPrice = Number(quote?.ref_price ?? quote?.tc ?? 0)
  const ceiling = Number(quote?.ceiling ?? quote?.tran ?? (refPrice ? refPrice * 1.07 : 0))
  const floor = Number(quote?.floor ?? quote?.san ?? (refPrice ? refPrice * 0.93 : 0))
  const matchPrice = Number(quote?.price ?? quote?.match_price ?? refPrice)
  const matchVol = Number(quote?.match_vol ?? 0)
  const changePct = Number(quote?.change_pct ?? quote?.changePct ?? 0)
  const changeVal = Number(quote?.change ?? 0)

  // Color helper according to Vietnamese stock exchanges (HOSE / HNX / UPCOM)
  const getPriceClass = (price) => {
    if (!price || !Number.isFinite(price)) return ''
    const p = Number(price)
    if (ceiling && Math.abs(p - ceiling) < 0.05) return 'is-ceiling' // Tím trần
    if (floor && Math.abs(p - floor) < 0.05) return 'is-floor'     // Xanh lơ sàn
    if (refPrice && Math.abs(p - refPrice) < 0.05) return 'is-ref' // Vàng tham chiếu
    if (refPrice && p > refPrice) return 'is-up'                  // Xanh lá tăng
    if (refPrice && p < refPrice) return 'is-down'                // Đỏ giảm
    return ''
  }

  // 3 Bid levels
  const bids = useMemo(() => [
    { level: 1, price: quote?.bid_1_price, vol: quote?.bid_1_volume },
    { level: 2, price: quote?.bid_2_price, vol: quote?.bid_2_volume },
    { level: 3, price: quote?.bid_3_price, vol: quote?.bid_3_volume },
  ].filter(b => b.price != null || b.vol != null), [quote])

  // 3 Ask levels
  const asks = useMemo(() => [
    { level: 1, price: quote?.ask_1_price, vol: quote?.ask_1_volume },
    { level: 2, price: quote?.ask_2_price, vol: quote?.ask_2_volume },
    { level: 3, price: quote?.ask_3_price, vol: quote?.ask_3_volume },
  ].filter(a => a.price != null || a.vol != null), [quote])

  // Totals & maximum volume for depth bars
  const { totalBidVol, totalAskVol, maxVol, bidRatio, askRatio } = useMemo(() => {
    const tBid = bids.reduce((sum, b) => sum + (Number(b.vol) || 0), 0)
    const tAsk = asks.reduce((sum, a) => sum + (Number(a.vol) || 0), 0)
    const allVols = [...bids.map(b => Number(b.vol) || 0), ...asks.map(a => Number(a.vol) || 0)]
    const mVol = Math.max(...allVols, 1)
    const sumTotal = tBid + tAsk || 1
    const bRat = Math.round((tBid / sumTotal) * 100)
    const aRat = 100 - bRat
    return {
      totalBidVol: tBid,
      totalAskVol: tAsk,
      maxVol: mVol,
      bidRatio: bRat,
      askRatio: aRat,
    }
  }, [bids, asks])

  const foreignBuy = Number(quote?.foreign_buy_volume ?? quote?.foreign_buy ?? 0)
  const foreignSell = Number(quote?.foreign_sell_volume ?? quote?.foreign_sell ?? 0)
  const foreignNet = foreignBuy - foreignSell

  return (
    <div className="vn-orderbook-container">
      {/* Header Info */}
      <div className="vn-orderbook__header">
        <div className="vn-orderbook__title">
          <BarChart2 size={16} className="text-accent" />
          <span>SỔ LỆNH ĐỘ SÂU THỊ TRƯỜNG (DOM) · {symbol || quote?.symbol || 'CP'}</span>
        </div>
        <div className="vn-orderbook__limits-info">
          <span className="vn-pill is-ceiling">Trần: {formatVnPrice(ceiling)}</span>
          <span className="vn-pill is-ref">TC: {formatVnPrice(refPrice)}</span>
          <span className="vn-pill is-floor">Sàn: {formatVnPrice(floor)}</span>
        </div>
      </div>

      {/* Main Order Book Grid: Bids (Left) | Match (Center) | Asks (Right) */}
      <div className="vn-orderbook__grid">
        {/* Left Side: BIDS (Dư Mua - 3 bước giá) */}
        <div className="vn-orderbook__column is-bids">
          <div className="vn-orderbook__col-head">
            <span className="col-side is-up">BÊN MUA (BIDS)</span>
            <span className="col-side-vol">Tổng: {formatVnVol(totalBidVol)}</span>
          </div>

          <div className="vn-orderbook__list">
            {bids.map((bid) => {
              const fillPct = Math.min(100, Math.round(((Number(bid.vol) || 0) / maxVol) * 100))
              const cls = getPriceClass(bid.price)
              return (
                <div key={`bid-${bid.level}`} className="vn-orderbook__step is-bid">
                  <div className="vn-orderbook__fill is-bid" style={{ width: `${fillPct}%` }} />
                  <span className="step-tag">Giá {bid.level}</span>
                  <span className={`step-price ${cls}`}>
                    {formatVnPrice(bid.price)}
                  </span>
                  <span className="step-vol">{formatVnVol(bid.vol)}</span>
                </div>
              )
            })}
            {!bids.length && (
              <div className="vn-orderbook__empty">Không có lệnh dư mua</div>
            )}
          </div>
        </div>

        {/* Center: MATCH (Khớp lệnh hiện tại) */}
        <div className="vn-orderbook__center-match">
          <span className="match-label">KHỚP LỆNH</span>
          <div className={`match-price ${getPriceClass(matchPrice)}`}>
            {formatVnPrice(matchPrice)}
          </div>
          <div className={`match-chg ${changePct >= 0 ? 'is-up' : 'is-down'}`}>
            {changePct >= 0 ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
            <span>{changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%</span>
            <small>({changeVal >= 0 ? '+' : ''}{changeVal.toFixed(2)})</small>
          </div>
          <div className="match-vol">
            <span>KL Khớp:</span>
            <strong>{formatVnVol(matchVol)}</strong>
          </div>
        </div>

        {/* Right Side: ASKS (Dư Bán - 3 bước giá) */}
        <div className="vn-orderbook__column is-asks">
          <div className="vn-orderbook__col-head">
            <span className="col-side is-down">BÊN BÁN (ASKS)</span>
            <span className="col-side-vol">Tổng: {formatVnVol(totalAskVol)}</span>
          </div>

          <div className="vn-orderbook__list">
            {asks.map((ask) => {
              const fillPct = Math.min(100, Math.round(((Number(ask.vol) || 0) / maxVol) * 100))
              const cls = getPriceClass(ask.price)
              return (
                <div key={`ask-${ask.level}`} className="vn-orderbook__step is-ask">
                  <div className="vn-orderbook__fill is-ask" style={{ width: `${fillPct}%` }} />
                  <span className="step-tag">Giá {ask.level}</span>
                  <span className={`step-price ${cls}`}>
                    {formatVnPrice(ask.price)}
                  </span>
                  <span className="step-vol">{formatVnVol(ask.vol)}</span>
                </div>
              )
            })}
            {!asks.length && (
              <div className="vn-orderbook__empty">Không có lệnh dư bán</div>
            )}
          </div>
        </div>
      </div>

      {/* Order Imbalance Ratio Bar (Cung / Cầu 3 bước giá) */}
      <div className="vn-orderbook__imbalance">
        <div className="imbalance-labels">
          <span className="is-up">Tổng Dư Mua: {formatVnVol(totalBidVol)} ({bidRatio}%)</span>
          <span className="is-down">Tổng Dư Bán: {formatVnVol(totalAskVol)} ({askRatio}%)</span>
        </div>
        <div className="imbalance-bar">
          <div className="imbalance-fill is-bid" style={{ width: `${bidRatio}%` }} />
          <div className="imbalance-fill is-ask" style={{ width: `${askRatio}%` }} />
        </div>
      </div>

      {/* Foreign Investors Flow Box (Giao dịch khối ngoại) */}
      <div className="vn-orderbook__foreign-box">
        <div className="foreign-item">
          <span>Khối ngoại mua:</span>
          <strong className="is-up">{formatVnVol(foreignBuy)}</strong>
        </div>
        <div className="foreign-item">
          <span>Khối ngoại bán:</span>
          <strong className="is-down">{formatVnVol(foreignSell)}</strong>
        </div>
        <div className="foreign-item">
          <span>Mua ròng:</span>
          <strong className={foreignNet >= 0 ? 'is-up' : 'is-down'}>
            {foreignNet >= 0 ? '+' : ''}{formatVnVol(foreignNet)}
          </strong>
        </div>
      </div>
    </div>
  )
}

export default memo(VnOrderBookWidget)
