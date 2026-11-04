import { InstrumentSparkline, PriceSparkline } from './PriceSparkline'
import { finitePrice, normalizeSparklinePoints } from '../services/sparklineModel'

const format = value => value == null ? '—' : value.toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const signed = value => value == null ? '—' : `${value > 0 ? '+' : ''}${format(value)}`

export function IndexSparkline({ symbol = 'VNINDEX', history, ...props }) {
  return history ? <PriceSparkline points={normalizeSparklinePoints(history)} label={symbol} {...props}/> : <InstrumentSparkline symbol={symbol === 'UPCOM' ? 'UPCOMINDEX' : symbol === 'HNX30' ? 'HNXINDEX30' : symbol} {...props}/>
}

export function IndexSparklineCard({ item, isSelected = false, onSelect, compact = false }) {
  const changePct = finitePrice(item.change_pct ?? item.changePct)
  const change = finitePrice(item.change)
  const price = finitePrice(item.price)
  const tone = changePct == null ? '' : changePct > 0 ? 'is-pos' : changePct < 0 ? 'is-neg' : 'is-ref'
  const volume = finitePrice(item.volume_million), turnover = finitePrice(item.turnover_billion)
  return <button type="button" className={`sonar-index-card ${isSelected ? 'is-active' : ''}`} onClick={() => onSelect?.(item.symbol)} disabled={!onSelect} aria-pressed={isSelected} aria-label={`Mở chỉ số ${item.label || item.symbol}`}>
    <span className="sonar-card-heading"><strong>{item.label || item.symbol}</strong>{!compact && <span>PHIÊN GẦN NHẤT</span>}</span>
    <span className="sonar-card-quote"><strong className="sonar-price-large">{format(price)}</strong><span className={`sonar-card-change ${tone}`}><strong>{signed(changePct)}{changePct == null ? '' : '%'}</strong><small>{signed(change)} điểm</small></span></span>
    <span className="sonar-sparkline-box"><IndexSparkline symbol={item.symbol} history={item.history} height={48} interactive={false} showPeriod unit="điểm"/></span>
    {(volume !== null || turnover !== null || item.breadth) && <span className="sonar-card-details">
      {volume !== null && <span>{format(volume)} Triệu CP</span>}{turnover !== null && <span>{format(turnover)} Tỷ</span>}
      {!compact && item.breadth && <span className="sonar-breadth-line"><span className="is-pos">▲ {item.breadth.up ?? '—'}{item.breadth.ceil > 0 && <span> ({item.breadth.ceil})</span>}</span><span className="is-ref">● {item.breadth.flat ?? '—'}</span><span className="is-neg">▼ {item.breadth.down ?? '—'}{item.breadth.floor > 0 && <span> ({item.breadth.floor})</span>}</span></span>}
    </span>}
  </button>
}
