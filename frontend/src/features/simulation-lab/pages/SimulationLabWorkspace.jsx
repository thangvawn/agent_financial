import { createElement, useEffect, useMemo, useRef, useState } from 'react'
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  LineSeries,
  createChart,
  createSeriesMarkers,
} from 'lightweight-charts'
import {
  Activity, AlertTriangle, ArrowLeft, BarChart3, Beaker, BookOpen,
  Check, ChevronRight, CircleDot, Clock3, Database, FlaskConical,
  GitCompareArrows, History, Layers3, Play, Plus, RefreshCw, Save,
  Settings2, ShieldCheck, SlidersHorizontal, Trash2,
} from 'lucide-react'

import {
  fetchSimulationStudio,
  issueProLabAccessToken,
  runSimulationStudio,
} from '../services/proLabApi'
import './simulation-lab-workspace.css'

const NAV = [
  ['builder', 'Strategy builder', SlidersHorizontal],
  ['results', 'Kết quả', BarChart3],
  ['compare', 'So sánh runs', GitCompareArrows],
  ['history', 'Lịch sử', History],
]

const DEFAULT_STRATEGY = {
  name: 'VN Trend 20/50',
  hypothesis: 'Mua cổ phiếu Việt Nam khi giá xác nhận xu hướng và thoát khi xu hướng suy yếu.',
  universe: ['FPT', 'VCB', 'HPG', 'MWG'],
  benchmark: 'VNINDEX',
  rebalance_frequency: 'monthly',
  entry_rules: [{ field: 'close', operator: 'above', value: 'sma_20' }],
  exit_rules: [{ field: 'close', operator: 'below', value: 'sma_20' }],
}

const DEFAULT_EXECUTION = {
  initial_capital: 100000000,
  timeframe: '1d',
  commission_pct: 0.15,
  slippage_pct: 0.05,
  lot_size: 100,
  settlement: 'T+2',
}

export default function SimulationLabWorkspace({ sessionId, onBack }) {
  const [token, setToken] = useState(() => localStorage.getItem('pro_lab.access_token') || '')
  const [studio, setStudio] = useState(null)
  const [strategy, setStrategy] = useState(DEFAULT_STRATEGY)
  const [execution, setExecution] = useState(DEFAULT_EXECUTION)
  const [period, setPeriod] = useState({ start_date: '2023-01-01', end_date: '2025-12-31' })
  const [active, setActive] = useState('builder')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [mobileNav, setMobileNav] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function boot() {
      if (!sessionId) return
      setError('')
      try {
        let accessToken = token
        if (!accessToken) {
          const issued = await issueProLabAccessToken(sessionId)
          accessToken = issued.access_token
          localStorage.setItem('pro_lab.access_token', accessToken)
          if (!cancelled) setToken(accessToken)
        }
        const payload = await fetchSimulationStudio(sessionId, accessToken)
        if (!cancelled) setStudio(payload)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Không thể mở Simulation Lab.')
      }
    }
    void boot()
    return () => { cancelled = true }
  }, [sessionId, token])

  const runs = useMemo(() => studio?.workspace?.experiments?.filter((item) => item.experiment_type === 'backtest_lab') || [], [studio])

  async function runBacktest() {
    if (!token || running) return
    setRunning(true)
    setError('')
    setActive('results')
    try {
      const payload = await runSimulationStudio({
        user_id: sessionId,
        ...period,
        strategy,
        execution,
      }, token)
      setResult(payload)
      setActive('results')
      setStudio(await fetchSimulationStudio(sessionId, token))
    } catch (err) {
      setError(err.message || 'Backtest không chạy được.')
    } finally {
      setRunning(false)
    }
  }

  function applyTemplate(template) {
    setStrategy((current) => ({
      ...current,
      name: template.name,
      hypothesis: template.description,
      universe: template.universe,
      entry_rules: template.entry_rules,
      exit_rules: template.exit_rules,
    }))
  }

  return (
    <main className="simlab">
      <aside className={`simlab__rail ${mobileNav ? 'is-open' : ''}`}>
        <div className="simlab__brand"><FlaskConical size={18} /><span>Simulation Lab</span></div>
        <button className="simlab__back" type="button" onClick={onBack}><ArrowLeft size={15} /> Terminal</button>
        <nav>
          <p className="simlab__nav-label">WORKSPACE</p>
          {NAV.map(([id, label, Icon]) => (
            <button key={id} type="button" className={active === id ? 'is-active' : ''} onClick={() => { setActive(id); setMobileNav(false) }}>
              {createElement(Icon, { size: 16 })}<span>{label}</span>{id === 'history' && runs.length ? <b>{runs.length}</b> : null}
            </button>
          ))}
        </nav>
        <div className="simlab__rail-section">
          <p className="simlab__nav-label">MẪU CHIẾN LƯỢC</p>
          {(studio?.templates || []).map((item) => (
            <button className="simlab__template" key={item.id} type="button" onClick={() => applyTemplate(item)}>
              <span>{item.name}</span><ChevronRight size={14} />
            </button>
          ))}
        </div>
        <div className="simlab__data-pill">
          <span><Database size={14} /> Historical feed</span>
          <strong><i /> {studio?.data_status?.provider || 'checking'}</strong>
        </div>
      </aside>

      <section className="simlab__main">
        <header className="simlab__topbar">
          <button className="simlab__mobile-menu" type="button" onClick={() => setMobileNav(!mobileNav)}><Layers3 size={18} /></button>
          <div className="simlab__title-block">
            <input aria-label="Tên chiến lược" value={strategy.name} onChange={(e) => setStrategy({ ...strategy, name: e.target.value })} />
            <span><CircleDot size={10} /> Bản nháp · tự động lưu cục bộ</span>
          </div>
          <div className="simlab__actions">
            <button type="button" className="simlab__icon-btn" title="Lưu"><Save size={16} /></button>
            <button type="button" className="simlab__run" onClick={runBacktest} disabled={running || !studio}>
              {running ? <RefreshCw className="is-spinning" size={16} /> : <Play size={16} fill="currentColor" />}
              {running ? 'Đang chạy…' : 'Chạy backtest'}
            </button>
          </div>
        </header>

        {error ? <div className="simlab__error"><AlertTriangle size={16} />{error}</div> : null}
        {active === 'builder' ? (
          <Builder strategy={strategy} setStrategy={setStrategy} execution={execution} setExecution={setExecution} period={period} setPeriod={setPeriod} studio={studio} />
        ) : null}
        {active === 'results' ? (running ? <RunProgress strategy={strategy} /> : <Results result={result} runs={runs} />) : null}
        {active === 'compare' ? <Compare runs={runs} /> : null}
        {active === 'history' ? <RunHistory runs={runs} onSelect={(run) => { setResult({ experiment: run, fidelity: inferFidelity(run) }); setActive('results') }} /> : null}
      </section>
    </main>
  )
}

function Builder({ strategy, setStrategy, execution, setExecution, period, setPeriod, studio }) {
  return (
    <div className="simlab__workspace">
      <section className="simlab__canvas">
        <div className="simlab__section-head">
          <div><span className="simlab__kicker">LOGIC CANVAS</span><h1>Thiết kế giả thuyết có thể kiểm chứng</h1></div>
          <span className="simlab__status"><Check size={13} /> Hợp lệ</span>
        </div>
        <div className="simlab__hypothesis">
          <BookOpen size={17} />
          <textarea value={strategy.hypothesis} onChange={(e) => setStrategy({ ...strategy, hypothesis: e.target.value })} />
        </div>
        <StrategyBlock number="01" tone="blue" title="Phạm vi đầu tư" subtitle="Chọn nhóm chứng khoán được phép tham gia">
          <label className="simlab__field simlab__field--wide"><span>Mã chứng khoán</span><input value={strategy.universe.join(', ')} onChange={(e) => setStrategy({ ...strategy, universe: e.target.value.split(',').map((v) => v.trim().toUpperCase()).filter(Boolean) })} /></label>
          <label className="simlab__field"><span>Benchmark</span><select value={strategy.benchmark} onChange={(e) => setStrategy({ ...strategy, benchmark: e.target.value })}><option>VNINDEX</option><option>VN30</option><option>HNXINDEX</option></select></label>
        </StrategyBlock>
        <StrategyBlock number="02" tone="green" title="Điều kiện vào lệnh" subtitle="Tất cả điều kiện phải đồng thời đúng">
          <RuleEditor rules={strategy.entry_rules} onChange={(entry_rules) => setStrategy({ ...strategy, entry_rules })} fields={studio?.supported_fields} />
        </StrategyBlock>
        <StrategyBlock number="03" tone="red" title="Điều kiện thoát" subtitle="Đóng vị thế khi một điều kiện được kích hoạt">
          <RuleEditor rules={strategy.exit_rules} onChange={(exit_rules) => setStrategy({ ...strategy, exit_rules })} fields={studio?.supported_fields} />
        </StrategyBlock>
      </section>
      <aside className="simlab__config">
        <div className="simlab__config-head"><Settings2 size={16} /><strong>Data & execution</strong></div>
        <ConfigGroup label="Khoảng kiểm thử">
          <div className="simlab__date-grid"><label><span>Từ ngày</span><input type="date" value={period.start_date} onChange={(e) => setPeriod({ ...period, start_date: e.target.value })} /></label><label><span>Đến ngày</span><input type="date" value={period.end_date} onChange={(e) => setPeriod({ ...period, end_date: e.target.value })} /></label></div>
        </ConfigGroup>
        <ConfigGroup label="Dữ liệu">
          <label className="simlab__field"><span>Khung thời gian</span><select value={execution.timeframe} onChange={(e) => setExecution({ ...execution, timeframe: e.target.value })}><option value="1d">Ngày (1D)</option><option value="1h">Giờ (1H)</option><option value="1wk">Tuần (1W)</option><option value="1mo">Tháng (1M)</option></select></label>
          <div className="simlab__source"><Database size={15} /><div><strong>{studio?.data_status?.provider || 'Đang kiểm tra'}</strong><span>Historical · on demand</span></div><i /></div>
        </ConfigGroup>
        <ConfigGroup label="Mô phỏng lệnh">
          <MoneyInput label="Vốn ban đầu" value={execution.initial_capital} onChange={(value) => setExecution({ ...execution, initial_capital: value })} suffix="₫" />
          <div className="simlab__split"><NumberInput label="Phí" value={execution.commission_pct} onChange={(value) => setExecution({ ...execution, commission_pct: value })} /><NumberInput label="Trượt giá" value={execution.slippage_pct} onChange={(value) => setExecution({ ...execution, slippage_pct: value })} /></div>
          <div className="simlab__vn-rules"><ShieldCheck size={16} /><div><strong>Vietnam execution profile</strong><span>Lot 100 · T+2 · equal weight</span></div></div>
        </ConfigGroup>
        <div className="simlab__fidelity"><AlertTriangle size={15} /><p><strong>Research fidelity</strong> Phí, trượt giá, lot và T+2 được lưu để audit, hiện chưa khấu trừ trực tiếp.</p></div>
      </aside>
    </div>
  )
}

function StrategyBlock({ number, tone, title, subtitle, children }) {
  return <article className={`simlab__block simlab__block--${tone}`}><div className="simlab__block-index">{number}</div><div className="simlab__block-body"><header><div><h2>{title}</h2><p>{subtitle}</p></div></header><div className="simlab__block-content">{children}</div></div></article>
}

function RuleEditor({ rules, onChange, fields = [] }) {
  const setRule = (index, patch) => onChange(rules.map((item, i) => i === index ? { ...item, ...patch } : item))
  return <div className="simlab__rules">{rules.map((rule, index) => <div className="simlab__rule" key={`${index}-${rule.field}`}><span className="simlab__logic">{index ? 'VÀ' : 'NẾU'}</span><select value={rule.field} onChange={(e) => setRule(index, { field: e.target.value })}>{(fields.length ? fields : [{ id: 'close', label: 'Giá đóng cửa' }, { id: 'volume', label: 'Khối lượng' }]).map((field) => <option key={field.id} value={field.id}>{field.label}</option>)}</select><select value={rule.operator} onChange={(e) => setRule(index, { operator: e.target.value })}><option value="above">lớn hơn</option><option value="below">nhỏ hơn</option><option value="crosses_above">cắt lên</option><option value="crosses_below">cắt xuống</option></select><input value={rule.value} onChange={(e) => setRule(index, { value: e.target.value })} /><button type="button" title="Xóa điều kiện" onClick={() => onChange(rules.filter((_, i) => i !== index))}><Trash2 size={14} /></button></div>)}<button className="simlab__add-rule" type="button" onClick={() => onChange([...rules, { field: 'close', operator: 'above', value: 'sma_20' }])}><Plus size={14} /> Thêm điều kiện</button></div>
}

function Results({ result, runs }) {
  const [selectedTicker, setSelectedTicker] = useState('')
  const experiment = result?.experiment || runs[0]
  if (!experiment) return <Empty icon={Beaker} title="Chưa có kết quả" text="Chạy chiến lược đầu tiên để mở equity curve, benchmark và risk report." />
  const engine = experiment.engine_result || {}
  const metrics = engine.metrics || {}
  const portfolio = normalizeSeries(engine.series?.portfolio || engine.series || [])
  const benchmark = normalizeSeries(engine.series?.benchmark || engine.series?.vnindex || [])
  const warnings = engine.warnings || []
  const trades = engine.strategy?.trades || []
  const openPositions = engine.strategy?.open_positions || []
  const strategyMetrics = engine.strategy?.metrics || {}
  const instruments = engine.series?.instruments || {}
  const tickers = Object.keys(instruments)
  const activeTicker = tickers.includes(selectedTicker) ? selectedTicker : tickers[0]
  const snapshot = engine.portfolio_snapshot || null
  const finalValue = metrics.final_value ?? metrics.ending_value ?? portfolio.at(-1)?.value
  return <div className="simlab__results">
    <div className="simlab__results-head"><div><span className="simlab__kicker">RUN REPORT</span><h1>{experiment.experiment_id}</h1><p>{engine.start_date} → {engine.end_date} · {engine.interval || '1d'} · {engine.source || 'unknown source'}</p></div><span className={`simlab__fidelity-badge ${result?.fidelity?.level === 'offline' ? 'is-offline' : ''}`}><Activity size={13} />{result?.fidelity?.level === 'offline' ? 'Offline fallback' : 'Research result'}</span></div>
    <div className="simlab__metrics"><Metric label="Tổng lợi nhuận" value={pct(metrics.total_return_pct)} /><Metric label="Sharpe" value={num(metrics.sharpe ?? metrics.sharpe_ratio)} /><Metric label="Max drawdown" value={pct(metrics.max_drawdown_pct)} negative /><Metric label="Số giao dịch" value={Number.isFinite(Number(strategyMetrics.trade_count)) ? String(strategyMetrics.trade_count) : '—'} /></div>
    {activeTicker ? <InstrumentAnalysis ticker={activeTicker} tickers={tickers} onSelect={setSelectedTicker} points={instruments[activeTicker]} trades={trades.filter((trade) => trade.ticker === activeTicker)} openPosition={openPositions.find((item) => item.ticker === activeTicker)} /> : null}
    <PortfolioSnapshot snapshot={snapshot} fallbackValue={finalValue} />
    <section className="simlab__chart-panel simlab__portfolio-chart"><div className="simlab__panel-title"><div><h2>Dòng vốn danh mục</h2><p>Giá trị mark-to-market của toàn bộ danh mục theo từng phiên</p></div><div className="simlab__legend"><span><i className="portfolio" />Portfolio</span><span><i className="benchmark" />VN-Index</span></div></div><EquityChart primary={portfolio} secondary={benchmark} /></section>
    {trades.length ? <TradeLedger trades={trades} /> : <div className="simlab__no-trades"><AlertTriangle size={15} /><span>Rule không tạo giao dịch trong giai đoạn này. Hãy kiểm tra điều kiện và timeframe.</span></div>}
    <div className="simlab__result-grid"><section className="simlab__report-card"><h3><ShieldCheck size={16} /> Data & execution audit</h3><dl><div><dt>Nguồn</dt><dd>{engine.source || 'Không xác định'}</dd></div><div><dt>Universe</dt><dd>{(engine.tickers || []).join(', ') || '—'}</dd></div><div><dt>Phí / trượt giá</dt><dd>Ghi nhận, chưa khấu trừ</dd></div><div><dt>Benchmark</dt><dd>{engine.benchmark_label || 'Không có'}</dd></div></dl></section><section className="simlab__report-card"><h3><AlertTriangle size={16} /> Cảnh báo engine</h3>{warnings.length ? <ul>{warnings.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="simlab__quiet">Không có cảnh báo do engine trả về.</p>}</section></div>
  </div>
}

function InstrumentAnalysis({ ticker, tickers, onSelect, points, trades, openPosition }) {
  return <section className="simlab__instrument"><div className="simlab__instrument-tabs">{tickers.map((item) => <button className={item === ticker ? 'is-active' : ''} key={item} type="button" onClick={() => onSelect(item)}>{item}</button>)}</div><div className="simlab__panel-title"><div><h2>{ticker} · Giá và điểm vào/thoát</h2><p>Đường cyan: giá đóng cửa · vàng: SMA · BUY xanh · SELL đỏ</p></div>{openPosition ? <span className={`simlab__position-chip ${Number(openPosition.unrealized_return_pct) >= 0 ? 'positive' : 'negative'}`}>Đang giữ · {pct(openPosition.unrealized_return_pct)}</span> : <span className="simlab__position-chip">Không có vị thế mở</span>}</div><PriceChart points={points} trades={trades} openPosition={openPosition} /></section>
}

function PriceChart({ points = [], trades = [], openPosition }) {
  const containerRef = useRef(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return undefined
    const candles = normalizeCandles(points)
    if (candles.length < 2) return undefined
    const tokens = getComputedStyle(container)
    const color = (name) => tokens.getPropertyValue(name).trim()
    const chart = createChart(container, {
      width: container.clientWidth,
      height: 390,
      layout: { background: { type: ColorType.Solid, color: color('--sl-panel') }, textColor: color('--sl-muted') },
      grid: { vertLines: { color: color('--sl-line-soft') }, horzLines: { color: color('--sl-line-soft') } },
      crosshair: { mode: CrosshairMode.Normal, vertLine: { color: color('--sl-dim') }, horzLine: { color: color('--sl-dim') } },
      rightPriceScale: { borderColor: color('--sl-line'), scaleMargins: { top: 0.08, bottom: 0.12 } },
      timeScale: { borderColor: color('--sl-line'), timeVisible: true, rightOffset: 8, barSpacing: 7, minBarSpacing: 2 },
      handleScroll: true,
      handleScale: true,
    })
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: color('--sl-green'), downColor: color('--sl-red'),
      borderUpColor: color('--sl-green'), borderDownColor: color('--sl-red'),
      wickUpColor: color('--sl-green'), wickDownColor: color('--sl-red'),
      priceLineVisible: false,
    })
    candleSeries.setData(candles)
    const smaSeries = chart.addSeries(LineSeries, { color: color('--sl-amber'), lineWidth: 1, priceLineVisible: false, lastValueVisible: false })
    smaSeries.setData(points.filter((item) => Number.isFinite(Number(item.sma))).map((item) => ({ time: Number(item.time), value: Number(item.sma) })).sort((a, b) => a.time - b.time))
    const markerData = trades.flatMap((trade, index) => [
      { time: toMarkerTime(trade.entry_date), position: 'belowBar', color: color('--sl-green'), shape: 'arrowUp', id: `buy-${index}`, size: 1.25 },
      { time: toMarkerTime(trade.exit_date), position: 'aboveBar', color: color('--sl-red'), shape: 'arrowDown', id: `sell-${index}`, size: 1.25 },
    ])
    if (openPosition && !trades.some((trade) => trade.entry_date === openPosition.entry_date)) markerData.push({ time: toMarkerTime(openPosition.entry_date), position: 'belowBar', color: color('--sl-green'), shape: 'arrowUp', id: 'open-position', size: 1.6 })
    createSeriesMarkers(candleSeries, markerData.filter((item) => candles.some((candle) => candle.time === item.time)).sort((a, b) => a.time - b.time), { autoScale: true })
    chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, candles.length - 180), to: candles.length + 8 })
    const observer = new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth }))
    observer.observe(container)
    return () => { observer.disconnect(); chart.remove() }
  }, [points, trades, openPosition])

  return <div className="simlab__price-chart" ref={containerRef} />
}

function PortfolioSnapshot({ snapshot, fallbackValue }) {
  if (!snapshot) return null
  return <section className="simlab__portfolio"><div className="simlab__panel-title"><div><h2>Danh mục tại ngày {snapshot.as_of}</h2><p>Giá trị mark-to-market, gồm tiền mặt và vị thế đang mở</p></div><strong className={Number(snapshot.total_pnl) >= 0 ? 'positive' : 'negative'}>{money(snapshot.total_value)} · {pct(snapshot.total_return_pct)}</strong></div><div className="simlab__capital-split"><div><span>Tổng giá trị</span><strong>{money(snapshot.total_value ?? fallbackValue)}</strong></div><div><span>Tiền mặt</span><strong>{money(snapshot.cash)}</strong></div><div><span>Giá trị vị thế</span><strong>{money(snapshot.market_value)}</strong></div><div><span>Lãi/lỗ</span><strong className={Number(snapshot.total_pnl) >= 0 ? 'positive' : 'negative'}>{signedMoney(snapshot.total_pnl)}</strong></div></div><div className="simlab__sleeves"><div className="head">Mã</div><div className="head">Trạng thái</div><div className="head">Giá trị hiện tại</div><div className="head">Lãi/lỗ</div>{(snapshot.sleeves || []).flatMap((item) => [<div key={`${item.ticker}-ticker`}><strong>{item.ticker}</strong><small>{item.weight_pct}% vốn đầu</small></div>, <div key={`${item.ticker}-status`}><span className={item.status === 'open' ? 'open' : 'cash'}>{item.status === 'open' ? 'Đang giữ' : 'Tiền mặt'}</span></div>, <div key={`${item.ticker}-value`}>{money(item.current_value)}</div>, <div className={Number(item.total_pnl) >= 0 ? 'positive' : 'negative'} key={`${item.ticker}-pnl`}>{signedMoney(item.total_pnl)}<small>{pct(item.total_return_pct)}</small></div>])}</div></section>
}

function RunProgress({ strategy }) {
  return <div className="simlab__run-progress"><span className="simlab__pulse"><Activity size={20} /></span><span className="simlab__kicker">BACKTEST ENGINE</span><h1>Đang xử lý {strategy.universe.length} mã…</h1><p>Tải dữ liệu lịch sử, căn chỉnh phiên giao dịch và tính equity curve. Thường mất 2–15 giây.</p><div><i /></div></div>
}

function Compare({ runs }) {
  if (runs.length < 2) return <Empty icon={GitCompareArrows} title="Cần ít nhất 2 runs" text="Các lần chạy được giữ nguyên trong database để bạn so sánh cùng một giả thuyết qua nhiều cấu hình." />
  return <div className="simlab__table-page"><div className="simlab__section-head"><div><span className="simlab__kicker">COMPARE</span><h1>So sánh độ bền chiến lược</h1></div></div><div className="simlab__compare-table"><div className="head">Run</div><div className="head">Return</div><div className="head">Sharpe</div><div className="head">Drawdown</div>{runs.slice(0, 6).flatMap((run) => { const m = run.engine_result?.metrics || {}; return [<div key={`${run.experiment_id}-id`}><strong>{run.experiment_id}</strong><span>{run.created_at?.slice(0, 10)}</span></div>, <div key={`${run.experiment_id}-ret`}>{pct(m.total_return_pct)}</div>, <div key={`${run.experiment_id}-sh`}>{num(m.sharpe ?? m.sharpe_ratio)}</div>, <div key={`${run.experiment_id}-dd`}>{pct(m.max_drawdown_pct)}</div>] })}</div></div>
}

function RunHistory({ runs, onSelect }) {
  return <div className="simlab__table-page"><div className="simlab__section-head"><div><span className="simlab__kicker">AUDIT TRAIL</span><h1>Lịch sử thí nghiệm</h1></div></div>{runs.length ? <div className="simlab__run-list">{runs.map((run) => <button type="button" onClick={() => onSelect(run)} key={run.experiment_id}><span className="simlab__run-icon"><Clock3 size={16} /></span><span><strong>{run.experiment_id}</strong><small>{run.created_at?.replace('T', ' ').slice(0, 19)}</small></span><span>{run.engine_result?.interval || '1d'}</span><span>{pct(run.engine_result?.metrics?.total_return_pct)}</span><ChevronRight size={16} /></button>)}</div> : <Empty icon={History} title="Lịch sử đang trống" text="Mỗi lần chạy sẽ được lưu với input, output, nguồn dữ liệu và caveat." />}</div>
}

function EquityChart({ primary, secondary, trades = [] }) {
  if (primary.length < 2) return <div className="simlab__chart-empty">Không đủ điểm dữ liệu để vẽ equity curve.</div>
  const all = [...primary, ...secondary]
  const min = Math.min(...all.map((p) => p.value)); const max = Math.max(...all.map((p) => p.value)); const spread = max - min || 1
  const path = (series) => series.map((point, i) => `${i ? 'L' : 'M'} ${(i / Math.max(series.length - 1, 1)) * 1000} ${260 - ((point.value - min) / spread) * 220}`).join(' ')
  const markers = buildTradeMarkers(primary, trades, min, spread)
  return <div className="simlab__equity"><svg viewBox="0 0 1000 280" preserveAspectRatio="none"><defs><linearGradient id="simlabArea" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="var(--sl-accent)" stopOpacity=".24"/><stop offset="1" stopColor="var(--sl-accent)" stopOpacity="0"/></linearGradient></defs><path className="grid" d="M0 40H1000M0 95H1000M0 150H1000M0 205H1000M0 260H1000"/><path className="area" d={`${path(primary)} L1000 280 L0 280 Z`} /><path className="primary" d={path(primary)} />{secondary.length > 1 ? <path className="secondary" d={path(secondary)} /> : null}{markers.map((marker, index) => <g className={`trade-marker ${marker.side}`} key={`${marker.side}-${marker.ticker}-${marker.time}-${index}`}><circle cx={marker.x} cy={marker.y} r="4.5" /><title>{marker.side.toUpperCase()} {marker.ticker} · {marker.date}</title></g>)}</svg></div>
}

function TradeLedger({ trades }) {
  return <section className="simlab__trades"><div className="simlab__panel-title"><div><h2>Trade ledger</h2><p>Điểm vào/thoát do backend sinh từ rule, thực thi ở phiên kế tiếp</p></div><span>{trades.length} giao dịch</span></div><div className="simlab__trade-table"><div className="head">Mã</div><div className="head">BUY</div><div className="head">SELL</div><div className="head">Nắm giữ</div><div className="head">P/L</div>{trades.slice().reverse().slice(0, 30).flatMap((trade, index) => [<div key={`${index}-ticker`}><strong>{trade.ticker}</strong></div>, <div key={`${index}-entry`}><b className="buy">{trade.entry_date}</b><small>{num(trade.entry_price)}</small></div>, <div key={`${index}-exit`}><b className="sell">{trade.exit_date}</b><small>{num(trade.exit_price)}</small></div>, <div key={`${index}-hold`}>{trade.holding_days} ngày</div>, <div className={Number(trade.return_pct) >= 0 ? 'positive' : 'negative'} key={`${index}-return`}>{pct(trade.return_pct)}</div>])}</div></section>
}

function ConfigGroup({ label, children }) { return <section className="simlab__config-group"><h3>{label}</h3>{children}</section> }
function MoneyInput({ label, value, onChange, suffix }) { return <label className="simlab__field"><span>{label}</span><div className="simlab__input-suffix"><input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} /><b>{suffix}</b></div></label> }
function NumberInput({ label, value, onChange }) { return <label className="simlab__field"><span>{label}</span><div className="simlab__input-suffix"><input type="number" step="0.01" value={value} onChange={(e) => onChange(Number(e.target.value))} /><b>%</b></div></label> }
function Metric({ label, value, negative }) { return <div className="simlab__metric"><span>{label}</span><strong className={negative ? 'is-negative' : ''}>{value}</strong></div> }
function Empty({ icon, title, text }) { return <div className="simlab__empty">{createElement(icon, { size: 28 })}<h1>{title}</h1><p>{text}</p></div> }
function normalizeSeries(series) { if (!Array.isArray(series)) return []; return series.map((item) => ({ time: Number(item?.time), value: Number(item?.value ?? item?.portfolio_value ?? item?.equity) })).filter((item) => Number.isFinite(item.value)) }
function normalizeCandles(points) { const seen = new Set(); return points.map((item) => ({ time: Number(item.time), open: Number(item.open ?? item.close), high: Number(item.high ?? item.close), low: Number(item.low ?? item.close), close: Number(item.close) })).filter((item) => Number.isFinite(item.time) && Number.isFinite(item.open) && Number.isFinite(item.high) && Number.isFinite(item.low) && Number.isFinite(item.close) && !seen.has(item.time) && seen.add(item.time)).sort((a, b) => a.time - b.time) }
function toMarkerTime(dateValue) { return Math.floor(Date.parse(`${dateValue}T00:00:00Z`) / 1000) }
function buildTradeMarkers(series, trades, min, spread) { if (!series.length || !trades.length) return []; const events = trades.flatMap((trade) => [{ side: 'entry', ticker: trade.ticker, date: trade.entry_date }, { side: 'exit', ticker: trade.ticker, date: trade.exit_date }]); return events.slice(-100).map((event) => { const timestamp = Date.parse(`${event.date}T00:00:00Z`) / 1000; let nearest = 0; let distance = Infinity; series.forEach((point, index) => { const next = Math.abs((point.time || index) - timestamp); if (next < distance) { distance = next; nearest = index } }); const point = series[nearest]; return { ...event, time: timestamp, x: (nearest / Math.max(series.length - 1, 1)) * 1000, y: 260 - ((point.value - min) / spread) * 220 } }) }
function pct(value) { return Number.isFinite(Number(value)) ? `${Number(value).toFixed(2)}%` : '—' }
function num(value) { return Number.isFinite(Number(value)) ? Number(value).toFixed(2) : '—' }
function money(value) { return Number.isFinite(Number(value)) ? new Intl.NumberFormat('vi-VN', { notation: 'compact', maximumFractionDigits: 2 }).format(Number(value)) + ' ₫' : '—' }
function signedMoney(value) { if (!Number.isFinite(Number(value))) return '—'; return `${Number(value) >= 0 ? '+' : '−'}${money(Math.abs(Number(value)))}` }
function inferFidelity(run) { const source = run?.engine_result?.source; return { level: source === 'offline_fallback' ? 'offline' : 'research', source } }
