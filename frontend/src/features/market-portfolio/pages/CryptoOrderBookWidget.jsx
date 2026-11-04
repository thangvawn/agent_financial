import { useEffect, useMemo, useRef, useState, memo } from 'react'
import { ArrowDown, ArrowUp, Layers } from 'lucide-react'

/**
 * Format cryptocurrency prices according to their magnitude.
 */
function formatCryptoPrice(value) {
  if (value === null || value === undefined) return '—'
  const num = Number(value)
  if (!Number.isFinite(num)) return '—'
  if (num >= 1000) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (num >= 1) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
  if (num >= 0.01) return num.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 6 })
  if (num >= 0.0001) return num.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 8 })
  return num.toLocaleString('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 10 })
}

/**
 * Format quantity / volume for order book levels.
 */
function formatQty(value) {
  if (value === null || value === undefined) return '—'
  const num = Number(value)
  if (!Number.isFinite(num)) return '—'
  if (num >= 1000) return num.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (num >= 10) return num.toLocaleString('en-US', { maximumFractionDigits: 3 })
  if (num >= 1) return num.toLocaleString('en-US', { maximumFractionDigits: 4 })
  return num.toLocaleString('en-US', { maximumFractionDigits: 6 })
}

export function CryptoOrderBookWidget({
  symbol = 'BTC',
  basePrice = null,
  initialLimit = 10,
  compact = false,
}) {
  const [limit, setLimit] = useState(initialLimit)
  const [bids, setBids] = useState([])
  const [asks, setAsks] = useState([])
  const [lastPrice, setLastPrice] = useState(basePrice)
  const [priceDirection, setPriceDirection] = useState('flat') // 'up' | 'down' | 'flat'
  const [connectionStatus, setConnectionStatus] = useState('connecting') // 'live' | 'connecting' | 'rest' | 'error'
  const prevPriceRef = useRef(basePrice)

  const cleanSymbol = useMemo(() => {
    return String(symbol || 'BTC').replace(/USDT$/i, '').trim().toUpperCase()
  }, [symbol])

  const streamPair = useMemo(() => `${cleanSymbol.toLowerCase()}usdt`, [cleanSymbol])

  // Sync initial base price
  useEffect(() => {
    if (basePrice && Number.isFinite(Number(basePrice))) {
      setLastPrice(Number(basePrice))
      prevPriceRef.current = Number(basePrice)
    }
  }, [basePrice])

  // Connect to Binance Order Book stream (@depth10@100ms or @depth20@100ms)
  useEffect(() => {
    let ws = null
    let restTimer = null
    let isCancelled = false
    let retryTimeout = null
    let reconnectAttempts = 0

    // Fetch initial snapshot via REST to fill book immediately
    async function fetchRestSnapshot() {
      try {
        const resp = await fetch(`https://api.binance.com/api/v3/depth?symbol=${cleanSymbol}USDT&limit=${limit}`)
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
        const data = await resp.json()
        if (isCancelled) return
        if (Array.isArray(data.bids) && Array.isArray(data.asks)) {
          setBids(data.bids.slice(0, limit))
          setAsks(data.asks.slice(0, limit))
        }
      } catch {
        // Silently ignore or schedule retry
      }
    }

    function connectWs() {
      if (isCancelled || typeof window === 'undefined') return
      setConnectionStatus(reconnectAttempts > 0 ? 'connecting' : 'connecting')

      // Use limit for stream: 5, 10 or 20
      const depthStreamLimit = limit <= 5 ? 5 : limit <= 10 ? 10 : 20
      const wsUrl = `wss://stream.binance.com:9443/ws/${streamPair}@depth${depthStreamLimit}@100ms`

      try {
        ws = new window.WebSocket(wsUrl)
      } catch {
        scheduleFallback()
        return
      }

      ws.onopen = () => {
        if (isCancelled) return
        reconnectAttempts = 0
        setConnectionStatus('live')
      }

      ws.onmessage = (event) => {
        if (isCancelled) return
        try {
          const payload = JSON.parse(event.data)
          const newBids = payload?.bids || payload?.data?.bids
          const newAsks = payload?.asks || payload?.data?.asks

          if (Array.isArray(newBids) && Array.isArray(newAsks)) {
            const slicedBids = newBids.slice(0, limit)
            const slicedAsks = newAsks.slice(0, limit)
            setBids(slicedBids)
            setAsks(slicedAsks)

            // Derive mid or match price
            const topBid = Number(slicedBids[0]?.[0])
            const topAsk = Number(slicedAsks[0]?.[0])
            if (topBid && topAsk) {
              const currentMid = (topBid + topAsk) / 2
              setLastPrice((prev) => {
                const prevNum = Number(prev) || currentMid
                if (topBid > prevNum) setPriceDirection('up')
                else if (topAsk < prevNum) setPriceDirection('down')
                return prevNum
              })
            }
          }
        } catch {
          // ignore parsing error
        }
      }

      ws.onerror = () => {
        scheduleFallback()
      }

      ws.onclose = () => {
        if (!isCancelled) {
          scheduleFallback()
        }
      }
    }

    function scheduleFallback() {
      if (isCancelled) return
      setConnectionStatus('rest')
      if (ws) {
        try { ws.close() } catch {
          // ignore socket close errors
        }
        ws = null
      }
      // Poll via REST every 1.5s as robust fallback
      fetchRestSnapshot()
      restTimer = window.setInterval(fetchRestSnapshot, 1500)

      // Try reconnecting WS after delay
      reconnectAttempts += 1
      const delay = Math.min(20000, 1500 * (2 ** Math.min(reconnectAttempts, 4)))
      retryTimeout = window.setTimeout(() => {
        if (!isCancelled && document.visibilityState === 'visible') {
          if (restTimer) clearInterval(restTimer)
          connectWs()
        }
      }, delay)
    }

    fetchRestSnapshot()
    connectWs()

    return () => {
      isCancelled = true
      if (ws) {
        try { ws.close() } catch {
          // ignore socket close errors
        }
      }
      if (restTimer) clearInterval(restTimer)
      if (retryTimeout) clearTimeout(retryTimeout)
    }
  }, [cleanSymbol, streamPair, limit])

  // Calculate cumulative totals and depth percentages
  const { processedAsks, processedBids, spread, spreadPct, totalBidVol, totalAskVol, buyRatio, sellRatio } = useMemo(() => {
    let cumAsk = 0
    const askRows = asks.map(([pStr, qStr]) => {
      const p = Number(pStr)
      const q = Number(qStr)
      cumAsk += q
      return { price: p, qty: q, total: cumAsk }
    })

    let cumBid = 0
    const bidRows = bids.map(([pStr, qStr]) => {
      const p = Number(pStr)
      const q = Number(qStr)
      cumBid += q
      return { price: p, qty: q, total: cumBid }
    })

    const maxCum = Math.max(cumAsk, cumBid, 0.0001)

    const topBid = bidRows[0]?.price || 0
    const topAsk = askRows[0]?.price || 0
    const rawSpread = topAsk && topBid ? topAsk - topBid : 0
    const rawSpreadPct = topAsk && rawSpread > 0 ? (rawSpread / topAsk) * 100 : 0

    const tBid = cumBid
    const tAsk = cumAsk
    const sumVol = tBid + tAsk || 1
    const bRatio = Math.round((tBid / sumVol) * 100)
    const aRatio = 100 - bRatio

    return {
      // In professional trading interfaces, Asks are rendered with highest price at top, down to lowest ask
      processedAsks: askRows.slice().reverse().map((r) => ({
        ...r,
        fillPct: Math.min(100, Math.round((r.total / maxCum) * 100)),
      })),
      processedBids: bidRows.map((r) => ({
        ...r,
        fillPct: Math.min(100, Math.round((r.total / maxCum) * 100)),
      })),
      spread: rawSpread,
      spreadPct: rawSpreadPct,
      totalBidVol: tBid,
      totalAskVol: tAsk,
      buyRatio: bRatio,
      sellRatio: aRatio,
    }
  }, [asks, bids])

  return (
    <div className={`crypto-orderbook ${compact ? 'is-compact' : ''}`}>
      {/* Top Header */}
      <div className="crypto-orderbook__head">
        <div className="crypto-orderbook__title">
          <Layers size={13} className="text-accent" />
          <span>SỔ LỆNH L2 (ORDER BOOK)</span>
          <span className={`crypto-orderbook__pill ${connectionStatus === 'live' ? 'is-live' : 'is-rest'}`}>
            <span />
            {connectionStatus === 'live' ? 'WS 100ms' : 'REST Poll'}
          </span>
        </div>
        <div className="crypto-orderbook__limits">
          {[5, 10, 20].map((num) => (
            <button
              key={num}
              type="button"
              className={`crypto-orderbook__limit-btn ${limit === num ? 'is-active' : ''}`}
              onClick={() => setLimit(num)}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      {/* Columns Header */}
      <div className="crypto-orderbook__table-head">
        <span className="col-price">Giá (USDT)</span>
        <span className="col-qty">Số lượng ({cleanSymbol})</span>
        <span className="col-total">Tổng</span>
      </div>

      {/* Asks (Sell Orders - Red, Highest to Lowest) */}
      <div className="crypto-orderbook__rows is-asks" role="table" aria-label="Lệnh Bán">
        {processedAsks.map((row) => (
          <div key={`ask-${row.price}`} className="crypto-orderbook__row is-ask" role="row">
            <div
              className="crypto-orderbook__depth-bar is-ask"
              style={{ width: `${row.fillPct}%` }}
              aria-hidden="true"
            />
            <span className="col-price is-neg">{formatCryptoPrice(row.price)}</span>
            <span className="col-qty">{formatQty(row.qty)}</span>
            <span className="col-total">{formatQty(row.total)}</span>
          </div>
        ))}
        {!processedAsks.length && (
          <div className="crypto-orderbook__empty">Đang kết nối sổ lệnh bán...</div>
        )}
      </div>

      {/* Mid Market Spread & Match Price Rail */}
      <div className="crypto-orderbook__spread-rail">
        <div className="crypto-orderbook__mid-price">
          <strong className={priceDirection === 'up' ? 'is-pos' : priceDirection === 'down' ? 'is-neg' : ''}>
            {formatCryptoPrice(lastPrice || bids[0]?.[0] || asks[0]?.[0])}
          </strong>
          {priceDirection === 'up' && <ArrowUp size={14} className="is-pos" />}
          {priceDirection === 'down' && <ArrowDown size={14} className="is-neg" />}
        </div>
        <div className="crypto-orderbook__spread-meta">
          <span>Chênh lệch:</span>
          <strong>${formatCryptoPrice(spread)}</strong>
          <small>({spreadPct.toFixed(3)}%)</small>
        </div>
      </div>

      {/* Bids (Buy Orders - Green, Highest to Lowest) */}
      <div className="crypto-orderbook__rows is-bids" role="table" aria-label="Lệnh Mua">
        {processedBids.map((row) => (
          <div key={`bid-${row.price}`} className="crypto-orderbook__row is-bid" role="row">
            <div
              className="crypto-orderbook__depth-bar is-bid"
              style={{ width: `${row.fillPct}%` }}
              aria-hidden="true"
            />
            <span className="col-price is-pos">{formatCryptoPrice(row.price)}</span>
            <span className="col-qty">{formatQty(row.qty)}</span>
            <span className="col-total">{formatQty(row.total)}</span>
          </div>
        ))}
        {!processedBids.length && (
          <div className="crypto-orderbook__empty">Đang kết nối sổ lệnh mua...</div>
        )}
      </div>

      {/* Bottom Imbalance Gauge / Flow Ratio */}
      <div className="crypto-orderbook__gauge">
        <div className="crypto-orderbook__gauge-labels">
          <span className="is-pos">Mua {buyRatio}% ({formatQty(totalBidVol)})</span>
          <span className="is-neg">Bán {sellRatio}% ({formatQty(totalAskVol)})</span>
        </div>
        <div className="crypto-orderbook__gauge-bar">
          <div className="gauge-fill is-pos" style={{ width: `${buyRatio}%` }} />
          <div className="gauge-fill is-neg" style={{ width: `${sellRatio}%` }} />
        </div>
      </div>
    </div>
  )
}

export default memo(CryptoOrderBookWidget)
