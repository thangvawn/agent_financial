import { useEffect, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ChartNoAxesCombined, ChevronRight, RefreshCw, RotateCcw, Search, X } from 'lucide-react'
import { fetchMpCommoditiesSnapshot } from '../services'
import { InstrumentSparkline } from '../components/PriceSparkline'
import { useCommodityHistory } from '../hooks/useCommodityHistory'
import { COMMODITY_GROUPS, COMMODITY_RANGES, RANGE_LABELS, commodityNumber, commodityPrice, groupLabel, historySummary, quoteTime, selectCommodities, sourceLabel, tone } from '../services/commodityModel'
import LightweightChartPanel from './LightweightChartPanel'
import './commodities.css'

function quoteStatusLabel(row) {
  return row.quote_status === 'unavailable' ? 'Chưa có giá' : row.quote_status === 'stale' ? 'Giá lưu trước đó' : 'Giá có độ trễ'
}

function Change({ value }) {
  const state = tone(value)
  return <span className={`commodity-change is-${state}`}>{state === 'up' ? '+' : ''}{commodityNumber(value)}{state !== 'unknown' ? '%' : ''}</span>
}

function CommodityDetail({ row, refreshToken }) {
  const [period, setPeriod] = useState('3mo')
  const [mode, setMode] = useState('candle')
  const [revision, setRevision] = useState(0)
  const [reset, setReset] = useState(0)
  const history = useCommodityHistory(row.symbol, period, refreshToken + revision)
  const summary = useMemo(() => historySummary(history.points), [history.points])
  const hasChart = history.status === 'ready'
  const chartMode = summary.candles ? mode : 'area'
  return <section className="commodity-detail" aria-label={`Chi tiết ${row.symbol}`}>
    <header className="commodity-detail-head">
      <div><div className="commodity-identity"><h3>{row.name}</h3><span>{row.symbol}</span></div><p>{groupLabel(row.category)} · {row.yahoo_symbol || row.symbol} · Hợp đồng tương lai</p></div>
      <div className="commodity-quote"><div><strong>{commodityPrice(row.price)}</strong><span>{row.unit || 'Chưa rõ đơn vị'}</span></div><div><Change value={row.change_pct}/><span>so với đóng cửa trước</span></div></div>
    </header>
    <div className="commodity-quote-meta"><span>Giá cập nhật {quoteTime(row.updated_at || row.as_of)} · GMT+7</span><span>{quoteStatusLabel(row)} · {sourceLabel(row.source)}</span></div>
    <div className="commodity-chart-toolbar">
      <div className="commodity-segment" role="group" aria-label="Khoảng thời gian">{COMMODITY_RANGES.map(range => <button key={range} aria-pressed={range === period} onClick={() => setPeriod(range)}>{RANGE_LABELS[range]}</button>)}</div>
      <div className="commodity-chart-actions"><div className="commodity-segment" role="group" aria-label="Kiểu biểu đồ"><button aria-pressed={chartMode === 'area'} onClick={() => setMode('area')}>Đường</button><button aria-pressed={chartMode === 'candle'} disabled={!summary.candles} title={!summary.candles ? 'Cần đủ giá mở, cao, thấp và đóng cửa' : 'Biểu đồ nến'} onClick={() => setMode('candle')}>Nến</button></div><button className="commodity-icon-button" aria-label="Đặt lại khung biểu đồ" disabled={!hasChart} onClick={() => setReset(value => value + 1)}><RotateCcw size={15}/></button><button className="commodity-icon-button" aria-label="Tải lại lịch sử giá" disabled={history.loading} onClick={() => setRevision(value => value + 1)}><RefreshCw size={15}/></button></div>
    </div>
    <div className="commodity-chart" aria-busy={history.loading}>
      {hasChart ? <LightweightChartPanel key={`${row.symbol}:${period}`} points={history.points} preserveRange mode={chartMode} height={370} showVolume={summary.volume} interval="1d" resetTrigger={reset} pricePrecision={Math.abs(row.price) < 10 ? 4 : 2} ariaLabel={`Lịch sử ${row.name}, ${RANGE_LABELS[period]}, ${row.unit}`}/> : <div className={`commodity-chart-empty ${history.status === 'loading' ? 'is-loading' : ''}`} role="status"><ChartNoAxesCombined size={28}/><strong>{history.status === 'loading' ? 'Đang tải lịch sử giá…' : history.status === 'error' ? 'Chưa tải được biểu đồ' : 'Chưa đủ lịch sử để vẽ biểu đồ'}</strong><span>{history.status === 'loading' ? `${row.symbol} · ${RANGE_LABELS[period]}` : 'Bảng giá vẫn dùng được. Bạn có thể tải lại hoặc chọn khoảng thời gian khác.'}</span>{history.status !== 'loading' && <button onClick={() => setRevision(value => value + 1)}>Thử lại lịch sử</button>}</div>}
    </div>
    {hasChart && history.error && <div className="commodity-alert" role="status">{history.error}</div>}
    {hasChart && history.notice && <div className="commodity-chart-caption" role="status">{history.notice}</div>}
    <div className="commodity-chart-caption"><span>{history.freshness === 'stale' ? 'Lịch sử lưu trước đó' : 'Lịch sử giá'} · Nến ngày · {sourceLabel(history.source || row.source)}{history.loading ? ' · Đang cập nhật…' : ''}</span><span>Kéo để di chuyển · Cuộn / chụm để zoom</span></div>
    <dl className="commodity-detail-stats"><div><dt>Thay đổi {RANGE_LABELS[period]}</dt><dd><Change value={summary.change}/></dd></div><div><dt>Cao nhất trong kỳ</dt><dd>{commodityPrice(summary.high)}</dd></div><div><dt>Thấp nhất trong kỳ</dt><dd>{commodityPrice(summary.low)}</dd></div><div><dt>KL ngày giao dịch gần nhất</dt><dd>{commodityNumber(row.volume_24h, 0)}</dd></div></dl>
    <p className="commodity-disclosure">Đơn vị giá: {row.unit || 'chưa xác định'}. % trong bảng so với giá đóng cửa ngày trước của nguồn; % theo kỳ tính từ giá đóng cửa đầu và cuối khoảng xem. Giá hợp đồng có thể trễ, không phải giá giao ngay.</p>
  </section>
}

export default function CommoditiesPanel() {
  const [data, setData] = useState(null)
  const [query, setQuery] = useState('')
  const [group, setGroup] = useState('all')
  const [sort, setSort] = useState('volume')
  const [selected, setSelected] = useState('XAU')
  const [mobileView, setMobileView] = useState('chart')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    let busy = false
    async function load(refresh = false) {
      if (busy || document.visibilityState === 'hidden') return
      busy = true
      setLoading(true)
      try {
        const payload = await fetchMpCommoditiesSnapshot({ signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]), refresh })
        if (!controller.signal.aborted) { setData(payload); setError('') }
      } catch (err) { if (!controller.signal.aborted) setError(err.message || 'Nguồn dữ liệu chưa phản hồi.') }
      finally { busy = false; if (!controller.signal.aborted) setLoading(false) }
    }
    load(revision > 0)
    const resume = () => load()
    const timer = setInterval(resume, 60000)
    window.addEventListener('focus', resume)
    window.addEventListener('online', resume)
    document.addEventListener('visibilitychange', resume)
    return () => {
      controller.abort(); clearInterval(timer)
      window.removeEventListener('focus', resume)
      window.removeEventListener('online', resume)
      document.removeEventListener('visibilitychange', resume)
    }
  }, [revision])
  const items = useMemo(() => Array.isArray(data?.items) ? data.items : [], [data])
  const filtered = useMemo(() => selectCommodities(items, { group, query, sort }), [items, group, query, sort])
  // Selection always belongs to the visible group/search result.
  const selectedRow = filtered.find(row => row.symbol === selected) || filtered[0]
  const advancing = items.filter(row => tone(row.change_pct) === 'up').length
  const declining = items.filter(row => tone(row.change_pct) === 'down').length
  const unchanged = items.filter(row => tone(row.change_pct) === 'flat').length
  const missing = items.length - advancing - declining - unchanged
  const resetFilters = () => { setQuery(''); setGroup('all') }

  return <section className="mp-panel commodity-page">
    <header className="commodity-head"><div><h2>Hàng hoá</h2><p>Theo dõi hợp đồng quốc tế theo nhóm thị trường.</p></div><div className="commodity-feed"><span>{data?.freshness === 'fresh' ? 'Giá có độ trễ' : 'Dữ liệu lưu trước đó'} · {quoteTime(data?.as_of)} (GMT+7)</span><button className="commodity-icon-button" onClick={() => setRevision(value => value + 1)} disabled={loading} aria-label="Làm mới bảng giá"><RefreshCw size={16} className={loading ? 'is-spinning' : ''}/></button></div></header>
    <div className="commodity-overview" aria-label="Độ rộng danh sách theo dõi"><strong>{items.length} hợp đồng</strong><span className="is-up"><ArrowUp size={13}/>{advancing} tăng</span><span className="is-down"><ArrowDown size={13}/>{declining} giảm</span><span>{unchanged} không đổi</span>{missing > 0 && <span>{missing} thiếu biến động</span>}<small>Chọn một hợp đồng để xem lịch sử giá</small></div>
    {!!data?.coverage && (data.coverage.stale > 0 || data.coverage.unavailable > 0) && <p className="commodity-coverage" role="status">{data.coverage.quoted}/{items.length} hợp đồng có giá · {data.coverage.stale} giá lưu trước đó · {data.coverage.unavailable} chưa có giá. Thời điểm từng hợp đồng được hiển thị khi chọn.</p>}
    {error && <div className="commodity-alert" role="alert"><span>{data ? 'Chưa làm mới được, đang giữ bảng giá trước đó.' : 'Không tải được bảng giá hàng hoá.'} {error}</span><button disabled={loading} onClick={() => setRevision(value => value + 1)}>Thử lại</button></div>}
    <div className="commodity-groups" role="group" aria-label="Nhóm hàng hoá">{COMMODITY_GROUPS.map(([key, label]) => <button key={key} aria-pressed={group === key} onClick={() => setGroup(key)}>{label}<span>{key === 'all' ? items.length : items.filter(row => row.category === key).length}</span></button>)}</div>
    <div className="commodity-mobile-view" role="group" aria-label="Vùng xem hàng hoá"><button aria-pressed={mobileView === 'chart'} onClick={() => setMobileView('chart')}>Biểu đồ{selectedRow ? ` · ${selectedRow.symbol}` : ''}</button><button aria-pressed={mobileView === 'list'} onClick={() => setMobileView('list')}>Bảng giá · Chọn hợp đồng</button></div>
    <div className="commodity-workbench" data-mobile-view={mobileView}>
      <section className="commodity-watch" aria-label="Danh sách hợp đồng">
        <div className="commodity-tools"><label className="commodity-search"><Search size={15}/><input aria-label="Tìm hàng hoá" value={query} onChange={event => setQuery(event.target.value)} placeholder="Tìm mã hoặc tên…"/>{query && <button aria-label="Xoá tìm kiếm" onClick={() => setQuery('')}><X size={14}/></button>}</label><select aria-label="Sắp xếp hàng hoá" value={sort} onChange={event => setSort(event.target.value)}><option value="volume">Khối lượng</option><option value="gainers">Tăng mạnh</option><option value="losers">Giảm mạnh</option><option value="name">Mã A–Z</option></select></div>
        <div className="commodity-list-meta"><span>{filtered.length} / {items.length} hợp đồng</span><span>Biểu đồ nhỏ: đóng cửa 1 tháng</span></div>
        <div className="commodity-table-wrap"><table className="commodity-table"><thead><tr><th scope="col">Hợp đồng</th><th scope="col">Giá / Thay đổi</th><th scope="col">1 tháng</th></tr></thead><tbody>
          {filtered.map(row => <tr key={row.symbol} className={selectedRow?.symbol === row.symbol ? 'is-selected' : ''} onClick={() => { setSelected(row.symbol); setMobileView('chart') }}><td><button className="commodity-select" aria-label={`Xem ${row.name} (${row.symbol})`} aria-pressed={selectedRow?.symbol === row.symbol} onClick={() => { setSelected(row.symbol); setMobileView('chart') }}><strong>{row.symbol}<ChevronRight size={13}/></strong><span>{row.name}</span></button></td><td className="commodity-row-price"><strong>{commodityPrice(row.price)}</strong><Change value={row.change_pct}/><small>{row.unit || '—'}{row.quote_status && row.quote_status !== 'available' ? ` · ${quoteStatusLabel(row)}` : ''}</small></td><td><InstrumentSparkline symbol={row.symbol} refreshToken={revision} pollMs={300000} label={row.symbol} height={34} width={112} unit={row.unit} interactive={false}/></td></tr>)}
        </tbody></table>
        {!filtered.length && <div className={`commodity-list-empty ${loading ? 'is-loading' : ''}`} role="status"><strong>{loading && !data ? 'Đang tải bảng giá…' : query || group !== 'all' ? 'Không tìm thấy hợp đồng' : 'Chưa có dữ liệu hàng hoá'}</strong><span>{query || group !== 'all' ? 'Thử tên khác hoặc mở lại tất cả nhóm.' : 'Bảng giá sẽ xuất hiện khi nguồn phản hồi.'}</span>{(query || group !== 'all') && <button onClick={resetFilters}>Xoá bộ lọc</button>}</div>}
        </div>
      </section>
      {selectedRow ? <CommodityDetail row={selectedRow} refreshToken={revision}/> : <div className="commodity-detail commodity-detail-placeholder"><ChartNoAxesCombined size={28}/><p>Chọn hợp đồng trong danh sách để xem biểu đồ.</p></div>}
    </div>
  </section>
}
