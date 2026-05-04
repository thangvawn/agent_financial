import { useEffect, useState } from 'react'

import {
  evaluateAnalyticsAlerts,
  fetchAnalyticsAlerts,
  fetchAnalyticsDashboard,
  fetchAnalyticsEvents,
  fetchAnalyticsKpis,
  fetchAnalyticsOps,
  fetchAnalyticsStatus,
  runAnalyticsKpiRollup,
  runAnalyticsOpsSnapshot,
} from '../../modules/analytics-admin'

const DEFAULT_QUERY = {
  event_category: '',
  module: '',
  surface: '',
  event_name: '',
  search: '',
  limit: 50,
}

const shellClass = 'mx-auto flex w-full max-w-7xl flex-col gap-5 rounded-[28px] border border-slate-200/70 bg-white/90 p-6 text-slate-800 shadow-[0_18px_45px_rgba(15,23,42,0.08)]'
const sectionClass = 'rounded-2xl border border-slate-200 bg-slate-50/80 p-4'
const sectionTitleClass = 'text-lg font-semibold text-slate-900'
const inputClass = 'mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100'
const primaryButtonClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800'
const secondaryButtonClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100'

export default function AnalyticsAdminPage({ onBack }) {
  const [adminKeyInput, setAdminKeyInput] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [windowGrain, setWindowGrain] = useState('day')
  const [activeView, setActiveView] = useState('product')
  const [queryFilters, setQueryFilters] = useState(DEFAULT_QUERY)
  const [status, setStatus] = useState(null)
  const [kpis, setKpis] = useState([])
  const [productDashboard, setProductDashboard] = useState(null)
  const [trustDashboard, setTrustDashboard] = useState(null)
  const [apiHealth, setApiHealth] = useState([])
  const [freshness, setFreshness] = useState([])
  const [moderation, setModeration] = useState([])
  const [alerts, setAlerts] = useState([])
  const [events, setEvents] = useState([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const saved = window.localStorage.getItem('analytics.admin_key') || ''
    setAdminKeyInput(saved)
    setAdminKey(saved)
  }, [])

  useEffect(() => {
    if (!adminKey) return
    void load(adminKey)
  }, [adminKey, windowGrain])

  async function load(key = adminKey) {
    setLoading(true)
    setError('')
    try {
      const [
        statusPayload,
        kpiPayload,
        productPayload,
        trustPayload,
        apiPayload,
        freshnessPayload,
        moderationPayload,
        alertPayload,
        eventPayload,
      ] = await Promise.all([
        fetchAnalyticsStatus(key),
        fetchAnalyticsKpis(key, windowGrain),
        fetchAnalyticsDashboard(key, 'product', windowGrain),
        fetchAnalyticsDashboard(key, 'trust'),
        fetchAnalyticsOps(key, 'api-health'),
        fetchAnalyticsOps(key, 'freshness'),
        fetchAnalyticsOps(key, 'moderation'),
        fetchAnalyticsAlerts(key, 'open'),
        fetchAnalyticsEvents(key, queryFilters),
      ])
      setStatus(statusPayload)
      setKpis(kpiPayload)
      setProductDashboard(productPayload)
      setTrustDashboard(trustPayload)
      setApiHealth(apiPayload)
      setFreshness(freshnessPayload)
      setModeration(moderationPayload)
      setAlerts(alertPayload)
      setEvents(eventPayload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleConnect() {
    if (!adminKeyInput.trim()) {
      setError('Nhập ADMIN_ANALYTICS_KEY trước.')
      return
    }
    window.localStorage.setItem('analytics.admin_key', adminKeyInput.trim())
    setAdminKey(adminKeyInput.trim())
    await load(adminKeyInput.trim())
  }

  async function handleRunKpiRollup() {
    try {
      await runAnalyticsKpiRollup(adminKey, windowGrain)
      setMessage('Đã chạy KPI rollup.')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRunOpsSnapshot() {
    try {
      await runAnalyticsOpsSnapshot(adminKey, 24)
      setMessage('Đã chạy ops snapshot.')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleEvaluateAlerts() {
    try {
      await evaluateAnalyticsAlerts(adminKey, false)
      setMessage('Đã evaluate alerts.')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRunQuery() {
    try {
      const payload = await fetchAnalyticsEvents(adminKey, queryFilters)
      setEvents(payload)
      setMessage('Đã làm mới event query.')
    } catch (err) {
      setError(err.message)
    }
  }

  function renderMetricGrid(metrics) {
    return (
      <div className="grid gap-3 md:grid-cols-2">
        {metrics.map((item) => (
          <article key={item.key || item.metric_name} className="rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-700">
            <strong className="text-slate-900">{item.label || item.metric_name}</strong>
            <p className="mt-1">{item.value} {item.unit}</p>
            <p>Status: {item.status}</p>
            {item.context ? <p>Context: {item.context}</p> : null}
          </article>
        ))}
      </div>
    )
  }

  return (
    <section className={shellClass}>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Analytics / Ops Admin</h1>
          <p className="mt-1 text-sm text-slate-600">Product, ops và trust dashboards dùng chung một admin surface.</p>
        </div>
        {onBack ? <button type="button" onClick={onBack} className={secondaryButtonClass}>Quay lại Pro Lab Admin</button> : null}
      </header>

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Admin Access</h2>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="min-w-[260px] flex-1 text-sm font-medium text-slate-700">
            Admin key
            <input
              className={inputClass}
              type="password"
              placeholder="ADMIN_ANALYTICS_KEY"
              value={adminKeyInput}
              onChange={(event) => setAdminKeyInput(event.target.value)}
            />
          </label>
          <button type="button" onClick={handleConnect} className={primaryButtonClass}>Kết nối</button>
        </div>
      </section>

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Controls</h2>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="w-40 text-sm font-medium text-slate-700">
            Window
            <select className={inputClass} value={windowGrain} onChange={(event) => setWindowGrain(event.target.value)}>
              <option value="hour">hour</option>
              <option value="day">day</option>
              <option value="week">week</option>
            </select>
          </label>
          <button type="button" onClick={handleRunKpiRollup} className={secondaryButtonClass}>Run KPI Rollup</button>
          <button type="button" onClick={handleRunOpsSnapshot} className={secondaryButtonClass}>Run Ops Snapshot</button>
          <button type="button" onClick={handleEvaluateAlerts} className={secondaryButtonClass}>Evaluate Alerts</button>
        </div>
      </section>

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Views</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {['product', 'ops', 'trust', 'query'].map((view) => (
            <button
              key={view}
              type="button"
              onClick={() => setActiveView(view)}
              className={activeView === view ? primaryButtonClass : secondaryButtonClass}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
      </section>

      {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      {message ? <p className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
      {loading ? <p className="text-sm text-slate-600">Đang tải analytics dashboard...</p> : null}

      {status ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Status</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatusTile label="Total events" value={status.total_events} />
            <StatusTile label="KPI snapshots" value={status.total_kpi_snapshots} />
            <StatusTile label="Ops snapshots" value={status.total_ops_snapshots} />
            <StatusTile label="Open alerts" value={status.open_alerts} />
          </div>
        </section>
      ) : null}

      {activeView === 'product' && productDashboard ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Product Dashboard</h2>
          <div className="mt-3">{renderMetricGrid(productDashboard.summary_metrics)}</div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Module Activity</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {productDashboard.module_activity.map((item) => (
              <li key={item.module}>
                {item.module}: {item.event_count} events · {item.unique_sessions} sessions
              </li>
            ))}
          </ul>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Recent Product Events</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-700">
            {productDashboard.recent_events.map((item) => (
              <li key={item.event_id} className="rounded-xl border border-slate-200 bg-white p-3">
                <strong className="text-slate-900">{item.event_name}</strong> · {item.module} · {item.surface}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {activeView === 'ops' ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Ops Dashboard</h2>
          <h3 className="mt-3 text-base font-semibold text-slate-900">API Health</h3>
          <div className="mt-2">{renderMetricGrid(apiHealth)}</div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Data Freshness</h3>
          <div className="mt-2">{renderMetricGrid(freshness)}</div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Moderation / Trust Ops</h3>
          <div className="mt-2">{renderMetricGrid(moderation)}</div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Latest KPI Snapshots</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {kpis.map((item) => (
              <li key={item.snapshot_id}>
                {item.kpi_name}: {item.value}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {activeView === 'trust' && trustDashboard ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Trust Dashboard</h2>
          <div className="mt-3">{renderMetricGrid(trustDashboard.summary_metrics)}</div>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Open Alerts</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-700">
            {trustDashboard.open_alerts.map((item) => (
              <li key={item.alert_id} className="rounded-xl border border-slate-200 bg-white p-3">
                <strong className="text-slate-900">{item.rule_name}</strong> · {item.severity_tier} · {item.status}
                <p className="mt-1">{item.summary}</p>
              </li>
            ))}
          </ul>
          <h3 className="mt-4 text-base font-semibold text-slate-900">Recent Trust Events</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-700">
            {trustDashboard.recent_events.map((item) => (
              <li key={item.event_id} className="rounded-xl border border-slate-200 bg-white p-3">
                <strong className="text-slate-900">{item.event_name}</strong> · {item.module} · {item.surface}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {activeView === 'query' ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Event Query</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              Category
              <select
                className={inputClass}
                value={queryFilters.event_category}
                onChange={(event) => setQueryFilters((current) => ({ ...current, event_category: event.target.value }))}
              >
                <option value="">all</option>
                <option value="product">product</option>
                <option value="ops">ops</option>
                <option value="trust_safety">trust_safety</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              Module
              <input
                className={inputClass}
                value={queryFilters.module}
                onChange={(event) => setQueryFilters((current) => ({ ...current, module: event.target.value }))}
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Surface
              <input
                className={inputClass}
                value={queryFilters.surface}
                onChange={(event) => setQueryFilters((current) => ({ ...current, surface: event.target.value }))}
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Event name
              <input
                className={inputClass}
                value={queryFilters.event_name}
                onChange={(event) => setQueryFilters((current) => ({ ...current, event_name: event.target.value }))}
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Search
              <input
                className={inputClass}
                value={queryFilters.search}
                onChange={(event) => setQueryFilters((current) => ({ ...current, search: event.target.value }))}
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Limit
              <input
                className={inputClass}
                type="number"
                min="1"
                max="500"
                value={queryFilters.limit}
                onChange={(event) => setQueryFilters((current) => ({ ...current, limit: Number(event.target.value) || 50 }))}
              />
            </label>
          </div>
          <button type="button" className={`mt-3 ${primaryButtonClass}`} onClick={handleRunQuery}>Run query</button>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {events.map((item) => (
              <li key={item.event_id} className="rounded-xl border border-slate-200 bg-white p-3">
                <strong className="text-slate-900">{item.event_name}</strong> · {item.event_category} · {item.module} · {item.surface}
                <p className="mt-1 text-xs text-slate-500">{item.timestamp}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {activeView !== 'trust' ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Open Alerts</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {alerts.map((item) => (
              <li key={item.alert_id} className="rounded-xl border border-slate-200 bg-white p-3">
                <strong className="text-slate-900">{item.rule_name}</strong> · {item.severity_tier} · {item.status}
                <p className="mt-1">{item.summary}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  )
}

function StatusTile({ label, value }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </article>
  )
}
