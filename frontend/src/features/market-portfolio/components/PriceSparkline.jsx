import { useId, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useTheme } from '../../../shared/theme/appTheme'
import { sparklineGeometry } from '../services/sparklineModel'
import { useSparklineHistory } from '../hooks/useSparklineHistory'
import './price-sparkline.css'

const number = value => value.toLocaleString('vi-VN', { maximumFractionDigits: 2 })
const date = time => new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Asia/Ho_Chi_Minh' }).format(time)

export function PriceSparkline({ points = [], status = 'ready', label, width = 240, height = 60, interactive = true, freshness, unit = '', showPeriod = false }) {
  const { theme } = useTheme()
  const id = useId(), element = useRef(null)
  const [active, setActive] = useState(null), [anchor, setAnchor] = useState(null)
  const chart = useMemo(() => sparklineGeometry(points, width, height), [points, width, height])
  const selected = active === null ? null : chart?.points[Math.min(active, chart.points.length - 1)]
  const emptyLabel = status === 'loading' ? 'Đang tải' : status === 'error' ? 'Chưa tải được' : 'Chưa có lịch sử'
  function activate(index) {
    setActive(index)
    const rect = element.current.getBoundingClientRect()
    setAnchor({ left: Math.max(8, Math.min(window.innerWidth - 208, rect.left + rect.width / 2 - 100)), top: rect.top > 88 ? rect.top - 80 : rect.bottom + 6 })
  }
  function move(event) {
    if (!chart) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width))
    activate(Math.round(x * (chart.points.length - 1)))
  }
  function keyDown(event) {
    if (event.key === 'Escape') { setActive(null); event.stopPropagation(); return }
    if (!chart || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
    event.preventDefault(); event.stopPropagation()
    const last = chart.points.length - 1
    activate(event.key === 'Home' ? 0 : event.key === 'End' ? last : Math.max(0, Math.min(last, (active ?? last) + (event.key === 'ArrowLeft' ? -1 : 1))))
  }
  const description = chart ? `${label}, giá đóng cửa 1 tháng, ${date(points[0].time)} đến ${date(points.at(-1).time)}, ${chart.changePct >= 0 ? '+' : ''}${number(chart.changePct)}%${freshness === 'stale' ? ', dữ liệu lưu trước đó' : ''}` : `${label}: ${emptyLabel}`
  return <span ref={element} className={`price-sparkline is-${chart?.tone || 'empty'}`} data-state={chart ? 'ready' : status} style={{ '--spark-height': `${height}px` }} tabIndex={interactive && chart ? 0 : undefined} role={interactive && chart ? 'group' : 'img'} aria-label={description} aria-describedby={selected ? `${id}-tooltip` : undefined} onPointerMove={move} onPointerLeave={() => setActive(null)} onFocus={() => chart && activate(chart.points.length - 1)} onBlur={() => setActive(null)} onKeyDown={keyDown}>
    {chart ? <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="currentColor" stopOpacity=".18"/><stop offset="100%" stopColor="currentColor" stopOpacity="0"/></linearGradient></defs>
      <path className="price-sparkline__area" d={chart.area} fill={`url(#${id})`}/>
      <line className="price-sparkline__reference" x1="4" x2={width - 4} y1={chart.refY} y2={chart.refY} vectorEffect="non-scaling-stroke"/>
      <path className="price-sparkline__line" d={chart.path} vectorEffect="non-scaling-stroke"/>
      {selected && <line className="price-sparkline__crosshair" x1={selected.x} x2={selected.x} y1="3" y2={height - 3} vectorEffect="non-scaling-stroke"/>}
      <circle className="price-sparkline__dot" cx={(selected || chart.points.at(-1)).x} cy={(selected || chart.points.at(-1)).y} r={selected ? 2.7 : 1.9}/>
    </svg> : <span className="price-sparkline__empty" role="status">{emptyLabel}</span>}
    {showPeriod && <span className="price-sparkline__period"><span>1 tháng · Đóng cửa</span><span>{chart ? `${chart.changePct >= 0 ? '+' : ''}${number(chart.changePct)}%` : '—'}{freshness === 'stale' ? ' · Lưu trước đó' : ''}</span></span>}
    {selected && anchor && createPortal(<div id={`${id}-tooltip`} className="price-sparkline-tooltip theme-portal" data-theme={theme} role="tooltip" style={anchor}>
      <span>{label}<span>{date(selected.time)}</span></span><strong>{number(selected.price)} {unit}</strong><small>So với đầu kỳ: {number((selected.price / chart.reference - 1) * 100)}%{freshness === 'stale' ? ' · Dữ liệu lưu trước đó' : ''}</small>
    </div>, document.body)}
  </span>
}

export function InstrumentSparkline({ symbol, refreshToken = 0, pollMs = 0, ...props }) {
  const { elementRef, ...history } = useSparklineHistory(symbol, { refreshToken, pollMs })
  return <span ref={elementRef} className="instrument-sparkline"><PriceSparkline label={symbol} {...history} {...props}/></span>
}
