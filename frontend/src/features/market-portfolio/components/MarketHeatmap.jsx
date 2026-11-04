import { memo, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowUpRight, Expand, Minus, Plus, Scan, List, Map as MapIcon, RefreshCw, Search, X } from 'lucide-react'
import useHeatmapLayout from '../hooks/useHeatmapLayout'
import useHeatmapCamera from '../hooks/useHeatmapCamera'
import { projectCells, projectSectors, focusBounds } from '../services/marketHeatmapViewport'
import { buildHeatmap, formatChange, formatMetric, formatNumber, METRICS, priceState, STATE_LABEL, HEATMAP_COLOR_LEGEND, tileColor } from '../services/marketHeatmapModel'
import './market-heatmap.css'

const EMPTY = []
const timeLabel = value => {
  const date = new Date(value || '')
  return Number.isNaN(date.valueOf()) ? 'Chưa rõ thời gian' : new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Ho_Chi_Minh',
  }).format(date)
}
const HeatmapCell = memo(function HeatmapCell({ id, sector, label, color, x, y, width, height, font, index, active, tabIndex }) {
  return <g data-cell-id={id} data-cell-index={index} role="button" tabIndex={tabIndex}
    aria-label={`${id}, ${label}, ${sector}`}>
    <rect x={x} y={y} width={width} height={height} fill={color}
      style={{ strokeWidth: Math.min(1, width * .08, height * .08) }} className={active ? 'is-active' : ''} />
    <text textAnchor="middle" dominantBaseline="central" className="vn-heatmap__cell-label"
      style={{ transform: `translate(${x + width / 2}px, ${y + height / 2}px)`, fontSize: font, strokeWidth: Math.min(.8, font * .045) }}>
      <tspan x="0" dy="-.6em" fontWeight="700">{id}</tspan>
      <tspan x="0" dy="1.2em" fontWeight="500">{label}</tspan>
    </text>
  </g>
})

export default function MarketHeatmap({ onSelectSymbol, feed }) {
  const { data, error, loading, refresh } = feed
  const [metric, setMetric] = useState('value')
  const [exchange, setExchange] = useState('')
  const [sector, setSector] = useState('')
  const [query, setQuery] = useState('')
  const [table, setTable] = useState(false)
  const [hover, setHover] = useState(null)
  const [focusId, setFocusId] = useState('')
  const [width, setWidth] = useState(0)
  const [fullscreen, setFullscreen] = useState(false)
  const [screenError, setScreenError] = useState('')
  const panelRef = useRef(null), plotRef = useRef(null), svgRef = useRef(null)
  const items = data?.items || EMPTY
  const mobile = width > 0 && width < 640
  const height = mobile ? 540 : fullscreen ? Math.max(500, window.innerHeight - 210) : 650
  const model = useMemo(() => buildHeatmap(items, { metric, exchange, sector }), [items, metric, exchange, sector])
  const scope = `${metric}:${exchange}:${sector}`
  const { layout, error: layoutError, computing, retry: retryLayout } = useHeatmapLayout(model.groups, width, height, { focused: Boolean(sector), scope })
  const sectors = useMemo(() => {
    const map = new Map()
    for (const item of items) if (!exchange || item.exchange === exchange) map.set(item.sector_id, item.sector)
    return [...map].sort((a, b) => a[1].localeCompare(b[1], 'vi'))
  }, [items, exchange])
  const byId = useMemo(() => new Map(model.groups.flatMap(g => g.children.map(c => [c.id, c]))), [model])
  const [painted, setPainted] = useState({ layout: null, source: null, quotes: new Map() })
  if (painted.layout !== layout || painted.source !== byId) {
    // Pair removal/addition with the completed layout. Existing cells can show
    // new prices immediately, but must not disappear while the worker is busy.
    const quotes = new Map((layout?.cells || EMPTY).flatMap(cell => {
      const item = byId.get(cell.id) || painted.quotes.get(cell.id)
      return item ? [[cell.id, item]] : []
    }))
    setPainted({ layout, source: byId, quotes })
  }
  const displayById = painted.quotes
  const camera = useHeatmapCamera(width, height, layout, scope, () => setHover(null), hover?.pinned ? hover.id : null)
  const visibleCells = useMemo(() => projectCells(layout?.cells || EMPTY, camera.view, width, height, displayById).filter(cell => displayById.has(cell.id)), [layout, camera.view, width, height, displayById])
  const visibleSectors = useMemo(() => projectSectors(layout?.sectors || EMPTY, camera.view, width, height), [layout, camera.view, width, height])
  const visibleById = useMemo(() => new Map(visibleCells.map(cell => [cell.id, cell])), [visibleCells])
  const viewKey = `${scope}:${width}:${height}:${camera.view.scale}:${camera.view.x}:${camera.view.y}`
  const [motion, setMotion] = useState({ layout: null, viewKey: '', animate: false })
  if (motion.layout !== layout || motion.viewKey !== viewKey) {
    setMotion({ layout, viewKey, animate: Boolean(layout && motion.layout && motion.viewKey === viewKey) })
  }
  const needle = query.trim().toLocaleLowerCase('vi-VN')
  const matches = needle ? model.mapRows.filter(item => `${item.symbol} ${item.name}`.toLocaleLowerCase('vi-VN').includes(needle))
    .sort((a, b) => Number(b.symbol.toLowerCase() === needle) - Number(a.symbol.toLowerCase() === needle)).slice(0, 8) : EMPTY
  const tipCell = hover && visibleCells.find(c => c.id === hover.id)
  const tip = tipCell && displayById.get(hover.id)
  const tipWidth = Math.min(290, width - 16)
  const labelHalfWidth = tipCell ? tipCell.font * tipCell.columns * .31 : 0
  const rightOfLabel = tipCell ? tipCell.center[0] + labelHalfWidth + 12 : 0
  const leftOfLabel = tipCell ? tipCell.center[0] - labelHalfWidth - 12 - tipWidth : 0
  const pinnedLeft = rightOfLabel + tipWidth <= width - 8 ? rightOfLabel : leftOfLabel >= 8 ? leftOfLabel : null
  const inlineTip = hover?.pinned && pinnedLeft === null
  const activeId = visibleCells.some(c => c.id === focusId) ? focusId : visibleCells[0]?.id

  useEffect(() => {
    const element = plotRef.current
    if (!element) return
    const observer = new ResizeObserver(entries => setWidth(Math.max(0, Math.round(entries[0].contentRect.width))))
    observer.observe(element)
    const changed = () => setFullscreen(document.fullscreenElement === panelRef.current)
    document.addEventListener('fullscreenchange', changed)
    return () => { observer.disconnect(); document.removeEventListener('fullscreenchange', changed) }
  }, [])

  function change(setter, value) { setter(value); setHover(null); setFocusId(''); setQuery('') }
  function reload() { refresh(); if (layoutError) retryLayout() }
  function drill(id) { change(setSector, id); setQuery('') }
  function showTip(cell, event, pinned = false) {
    const rect = plotRef.current.getBoundingClientRect()
    setFocusId(cell.id)
    setHover({ id: cell.id, pinned, x: event?.clientX ? event.clientX - rect.left : cell.center[0], y: event?.clientY ? event.clientY - rect.top : cell.center[1] })
  }
  function focusCell(id) {
    const target = layout?.cells.find(c => c.id === id)
    if (!target) return
    const next = focusBounds(target, width, height, layout.maxScale)
    const projected = projectCells([target], next, width, height)[0]
    camera.focus(target); setTable(false); setQuery(''); showTip(projected, null, true)
  }
  function activate(cell, event) { if (cell.font < 12) focusCell(cell.id); else showTip(cell, event, true) }

  function eventCell(event) { return visibleById.get(event.target.closest('[data-cell-id]')?.dataset.cellId) }

  function navigate(event, cell) {
    if (event.key === 'Escape') { setHover(null); return }
    if (['Enter', ' '].includes(event.key)) { event.preventDefault(); activate(cell); return }
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) return
    event.preventDefault()
    const index = visibleCells.findIndex(c => c.id === cell.id)
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? visibleCells.length - 1
      : (index + (['ArrowLeft', 'ArrowUp'].includes(event.key) ? -1 : 1) + visibleCells.length) % visibleCells.length
    const nextCell = visibleCells[next]
    setFocusId(nextCell.id)
    plotRef.current.querySelector(`[data-cell-index="${next}"]`)?.focus()
  }
  useEffect(() => {
    const element = svgRef.current
    if (!element) return
    const wheel = event => {
      if (!event.ctrlKey && !event.metaKey) return
      event.preventDefault()
      const rect = element.getBoundingClientRect()
      camera.zoom(Math.exp(-event.deltaY * .006), { x: event.clientX - rect.left, y: event.clientY - rect.top })
    }
    element.addEventListener('wheel', wheel, { passive: false })
    return () => element.removeEventListener('wheel', wheel)
  }, [camera, computing, table])

  async function expand() {
    setScreenError('')
    try {
      if (document.fullscreenElement === panelRef.current) await document.exitFullscreen()
      else if (panelRef.current.requestFullscreen) await panelRef.current.requestFullscreen()
      else setScreenError('Trình duyệt chưa hỗ trợ toàn màn hình. Bạn có thể chọn một ngành để xem rõ hơn.')
    } catch { setScreenError('Không mở được toàn màn hình. Bạn có thể chọn một ngành để xem rõ hơn.') }
  }

  return <section className="vn-heatmap" ref={panelRef} aria-labelledby="vn-heatmap-title" onKeyDown={event => { if (event.key === 'Escape') setHover(null) }}>
    <header className="vn-heatmap__heading">
      <h2 id="vn-heatmap-title">Bản đồ thị trường</h2>
      <div className="vn-heatmap__toolbar">
        <label><span className="sr-only">Diện tích ô</span><select aria-label="Diện tích ô" title="Diện tích ô" value={metric} onChange={e => change(setMetric, e.target.value)}>{Object.entries(METRICS).map(([id, m]) => <option key={id} value={id}>{m.label}</option>)}</select></label>
        <label><span className="sr-only">Sàn</span><select aria-label="Sàn giao dịch" value={exchange} onChange={e => { change(setExchange, e.target.value); setSector('') }}><option value="">Tất cả sàn</option>{['HOSE', 'HNX', 'UPCOM'].map(id => <option key={id}>{id}</option>)}</select></label>
        <label><span className="sr-only">Ngành</span><select aria-label="Ngành trên bản đồ" value={sector} onChange={e => change(setSector, e.target.value)}><option value="">Tất cả ngành</option>{sectors.map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select></label>
        <div className="vn-heatmap__search"><label><span className="sr-only">Tìm và đi tới mã</span><Search size={15} aria-hidden="true" /><input aria-label="Tìm mã trên bản đồ" placeholder="Tìm mã…" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={event => { if (event.key === 'Enter' && matches[0]) { event.preventDefault(); focusCell(matches[0].symbol) } if (event.key === 'Escape') setQuery('') }} maxLength={100} /></label>
          {needle && <div className="vn-heatmap__search-results" aria-label="Kết quả tìm mã">{matches.length ? matches.map(item => <button key={item.symbol} onClick={() => focusCell(item.symbol)}><strong>{item.symbol}</strong><span>{item.name}</span><small>{formatChange(item.change_pct)}</small></button>) : <p>Không có mã đủ dữ liệu trong bộ lọc hiện tại.</p>}</div>}
        </div>
      </div>
      <div className="vn-heatmap__actions">
        <button type="button" onClick={() => { setTable(v => !v); setHover(null) }} aria-pressed={table} aria-label={table ? 'Xem bản đồ' : 'Xem dạng bảng'} title={table ? 'Xem bản đồ' : 'Xem dạng bảng'}>{table ? <MapIcon size={16} /> : <List size={16} />}</button>
        <button type="button" onClick={reload} disabled={loading} aria-label="Tải lại bản đồ" title="Tải lại dữ liệu"><RefreshCw size={16} /></button>
        <button type="button" onClick={expand} aria-label={fullscreen ? 'Thu nhỏ bản đồ' : 'Phóng to bản đồ'} title="Toàn màn hình"><Expand size={16} /></button>
      </div>
    </header>
    <div className="vn-heatmap__summary">
      <div className="vn-heatmap__caption">
        {sector && <button type="button" onClick={() => drill('')} aria-label="Bỏ lọc ngành"><ArrowLeft size={13} />Tất cả ngành</button>}
        <span>{formatNumber(table ? model.eligible : model.mapRows.length, 0)}/{formatNumber(model.selected, 0)} mã · {formatMetric(table ? model.total : model.mapTotal, metric)}</span>
        {data && data.freshness !== 'fresh' && <span className="vn-heatmap__stale">{data.freshness === 'stale' ? 'Dữ liệu lưu trước' : 'Nguồn gián đoạn'}</span>}
      </div>
      {!table && model.mapRows.length > 0 && <div className="vn-heatmap__view-controls" aria-label="Điều khiển bản đồ">
        <button onClick={() => camera.zoom(.5)} disabled={camera.view.scale <= 1 || !layout} aria-label="Thu nhỏ" title="Thu nhỏ"><Minus size={16} /></button>
        <output aria-label="Mức phóng đại">{formatNumber(camera.view.scale, 1)}×</output>
        <button onClick={() => camera.zoom(2)} disabled={!layout || camera.view.scale >= (layout?.maxScale || 1)} aria-label="Phóng to" title="Phóng to"><Plus size={16} /></button>
        <button onClick={camera.reset} disabled={!layout} aria-label="Về toàn cảnh" title="Về toàn cảnh"><Scan size={15} /><span>Toàn cảnh</span></button>
      </div>}
    </div>
    {(error || screenError) && <div className="vn-heatmap__message" role="alert">{error || screenError}{error && <button onClick={reload}>Thử lại</button>}</div>}
    {layoutError && layout && <div className="vn-heatmap__message" role="alert">Chưa cập nhật được diện tích ô; đang giữ bố cục trước.<button onClick={retryLayout}>Thử dựng lại bản đồ</button></div>}
    <div className={`vn-heatmap__plot${table ? ' is-table' : ''}`} ref={plotRef} style={{ '--map-height': `${height}px` }}>
      {loading && !data ? <div className="vn-heatmap__empty" role="status">Đang tải bản đồ thị trường…</div>
        : !data && error ? <div className="vn-heatmap__empty"><h3>Chưa tải được dữ liệu thị trường</h3><p>Bấm Thử lại để kết nối lại nguồn dữ liệu.</p></div>
        : !model.eligible ? <div className="vn-heatmap__empty"><h3>Chưa có mã đủ dữ liệu trong phạm vi này</h3><p>Thử một ngành, sàn hoặc cách tính diện tích khác.</p><button onClick={() => { setSector(''); setExchange(''); setQuery(''); setMetric('value') }}>Xóa bộ lọc</button></div>
          : table ? <div className="vn-heatmap__table-wrap"><table><thead><tr><th>Mã</th><th>Ngành</th><th>Giá (đ)</th><th>Biến động</th><th>{METRICS[metric].label}</th></tr></thead><tbody>{model.rows.map(item => <tr key={item.symbol}><td><button onClick={() => onSelectSymbol(item.symbol)}>{item.symbol}</button></td><td>{item.sector}</td><td>{formatNumber(item.price, 0)}</td><td>{formatChange(item.change_pct)}</td><td>{formatMetric(item[metric], metric)}</td></tr>)}</tbody></table></div>
            : !model.mapRows.length ? <div className="vn-heatmap__empty"><h3>Chưa có mã đủ giá và % biến động</h3><p>Các mã thiếu thông tin vẫn có trong dạng bảng.</p><button onClick={() => setTable(true)}>Xem dạng bảng</button></div>
            : layoutError && !layout ? <div className="vn-heatmap__empty" role="alert"><p>{layoutError}</p><button onClick={retryLayout}>Thử dựng lại bản đồ</button><button onClick={() => setTable(true)}>Xem dạng bảng</button></div>
              : <>
                {computing && !layout && <div className="vn-heatmap__computing" role="status">Đang sắp xếp bản đồ…</div>}
                <svg ref={svgRef} {...camera.events} data-animate-layout={motion.animate}
                  onPointerMove={event => { camera.events.onPointerMove(event); const cell = eventCell(event); if (cell && !hover?.pinned && !event.buttons) showTip(cell, event) }}
                  onClick={event => { const cell = eventCell(event); if (cell) activate(cell, event) }}
                  onDoubleClick={event => { const cell = eventCell(event); if (cell) focusCell(cell.id) }}
                  onFocus={event => { const cell = eventCell(event); if (cell && event.target.matches(':focus-visible')) activate(cell) }}
                  onKeyDown={event => { const cell = eventCell(event); if (cell) navigate(event, cell) }} data-total-cells={layout?.cells.length || 0} data-scale={camera.view.scale} data-pan-x={camera.view.x} data-pan-y={camera.view.y} width="100%" height={height} viewBox={`0 0 ${width || 1} ${height}`} role="group" aria-label="Bản đồ nhiệt cổ phiếu Việt Nam" onPointerLeave={() => setHover(h => h?.pinned ? h : null)}>
                  {visibleCells.map((cell, index) => { const item = displayById.get(cell.id); return <HeatmapCell key={cell.id}
                    id={cell.id} sector={item.sector} label={item.changeLabel} color={tileColor(item)}
                    x={cell.x} y={cell.y} width={cell.width} height={cell.height} font={cell.font}
                    index={index} active={hover?.id === cell.id} tabIndex={activeId === cell.id ? 0 : -1} /> })}
                  {visibleSectors.map(region => <foreignObject key={region.id} x={region.x} y={region.y} width={region.width} height={region.height}>
                    <button className="vn-heatmap__sector-label" style={{ height: region.height, lineHeight: `${region.height}px`, paddingBlock: 0, fontSize: Math.min(11, region.height * .65) }} onClick={() => camera.focus(layout.sectors.find(s => s.id === region.id))} title={`Phóng vào ngành ${region.name}`}>{region.name}</button>
                  </foreignObject>)}
                </svg>
                {tip && <aside className={`vn-heatmap__tooltip${inlineTip ? ' is-inline' : ''}`} data-pinned={hover.pinned} inert={!hover.pinned} role={hover.pinned ? 'dialog' : 'tooltip'} aria-label={`Thông tin ${tip.symbol}`} style={inlineTip ? undefined : { left: hover.pinned ? pinnedLeft : Math.max(8, Math.min(width - tipWidth - 8, hover.x + 16)), top: Math.max(8, Math.min(height - 250, hover.y + 18)) }}>
                  <button className="vn-heatmap__tip-close" aria-label="Đóng thông tin mã" onClick={() => setHover(null)}><X size={14} /></button>
                  <strong>{tip.symbol}<span>{formatChange(tip.change_pct)}</span></strong>
                  <p>{tip.name}</p>
                  <dl><div><dt>{METRICS[metric].label}</dt><dd>{formatMetric(tip.weight, metric)}</dd></div>
                    <><div><dt>Giá / Tham chiếu</dt><dd>{formatNumber(tip.price, 0)} / {formatNumber(tip.ref_price, 0)} đ</dd></div><div><dt>Sàn / Ngành</dt><dd>{tip.exchange} · {tip.industry || tip.sector}</dd></div><div><dt>Trạng thái</dt><dd>{STATE_LABEL[priceState(tip)]}</dd></div></>
                  </dl>
                  <button onClick={() => onSelectSymbol(tip.symbol)}>Mở chi tiết {tip.symbol} <ArrowUpRight size={14} /></button>
                </aside>}
              </>}
    </div>
    <footer className="vn-heatmap__footer">
      <div className="vn-heatmap__legend" aria-label="Chú giải màu">{HEATMAP_COLOR_LEGEND.map(({ label, color }) => <span key={label}><i style={{ background: color }} />{label}</span>)}</div>
      <details className="vn-heatmap__info"><summary>Dữ liệu & cách xem</summary>
        <div><p>Diện tích theo {METRICS[metric].label.toLowerCase()}; màu theo % so với tham chiếu. Nhóm ngành ICB.</p>
          <p>Kéo để di chuyển. Ctrl + cuộn hoặc chụm hai ngón để zoom. Chọn ô để xem chi tiết.</p>
          <p>Cập nhật {timeLabel(data?.last_success_at || data?.as_of)}{data?.source ? ` · ${data.source.toUpperCase()}` : ''}.</p>
          <p>{model.missing > 0 ? `${formatNumber(model.missing, 0)} mã thiếu dữ liệu diện tích. ` : ''}{model.zero > 0 ? `${formatNumber(model.zero, 0)} mã có giá trị bằng 0. ` : ''}{model.missingChange > 0 ? `${model.missingChange} mã chưa có % hợp lệ, xem ở dạng bảng.` : ''}</p>
        </div>
      </details>
    </footer>
  </section>
}
