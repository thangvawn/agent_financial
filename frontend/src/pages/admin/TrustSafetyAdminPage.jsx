import { useEffect, useState } from 'react'

import {
  actOnTrustSafetyIncident,
  fetchTrustSafetyAudit,
  fetchTrustSafetyIncidents,
  fetchTrustSafetyStatus,
  openTrustSafetyIncident,
} from '../../modules/trust-safety-admin'

const DEFAULT_INCIDENT = {
  source_audit_id: '',
  surface: 'guided_investing',
  topic: '',
  severity: 'high',
  summary: '',
  owner_id: '',
  notes: '',
}

const DEFAULT_ACTION = {
  action: 'investigate',
  owner_id: '',
  notes: '',
}

const shellClass = 'mx-auto flex w-full max-w-7xl flex-col gap-5 rounded-[28px] border border-slate-200/70 bg-white/90 p-6 text-slate-800 shadow-[0_18px_45px_rgba(15,23,42,0.08)]'
const sectionClass = 'rounded-2xl border border-slate-200 bg-slate-50/80 p-4'
const sectionTitleClass = 'text-lg font-semibold text-slate-900'
const inputClass = 'mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100'
const primaryButtonClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800'
const secondaryButtonClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100'

export default function TrustSafetyAdminPage({ onBack }) {
  const [adminKeyInput, setAdminKeyInput] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [status, setStatus] = useState(null)
  const [audit, setAudit] = useState([])
  const [incidents, setIncidents] = useState([])
  const [incidentForm, setIncidentForm] = useState(DEFAULT_INCIDENT)
  const [incidentAction, setIncidentAction] = useState(DEFAULT_ACTION)
  const [selectedIncidentId, setSelectedIncidentId] = useState('')
  const [filters, setFilters] = useState({
    surface: '',
    severity: '',
    status: '',
    riskClass: '',
    search: '',
  })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const saved = window.localStorage.getItem('trust_safety.admin_key') || ''
    setAdminKeyInput(saved)
    setAdminKey(saved)
  }, [])

  useEffect(() => {
    if (!adminKey) return
    void load(adminKey)
  }, [adminKey])

  async function load(key = adminKey) {
    setError('')
    try {
      const [statusPayload, auditPayload, incidentsPayload] = await Promise.all([
        fetchTrustSafetyStatus(key),
        fetchTrustSafetyAudit(key, filters),
        fetchTrustSafetyIncidents(key, filters),
      ])
      setStatus(statusPayload)
      setAudit(auditPayload)
      setIncidents(incidentsPayload)
      if (!selectedIncidentId && incidentsPayload.length) {
        setSelectedIncidentId(incidentsPayload[0].incident_id)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleConnect() {
    const key = adminKeyInput.trim()
    if (!key) {
      setError('Nhập ADMIN_TRUST_SAFETY_KEY trước.')
      return
    }
    window.localStorage.setItem('trust_safety.admin_key', key)
    setAdminKey(key)
    await load(key)
  }

  async function handleApplyFilters() {
    if (!adminKey) return
    await load(adminKey)
  }

  async function handleOpenIncident() {
    setError('')
    setMessage('')
    try {
      const payload = await openTrustSafetyIncident(adminKey, incidentForm)
      setMessage(`Đã mở incident ${payload.incident_id}.`)
      setIncidentForm(DEFAULT_INCIDENT)
      await load()
      setSelectedIncidentId(payload.incident_id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleIncidentAction() {
    if (!selectedIncidentId) return
    setError('')
    setMessage('')
    try {
      const payload = await actOnTrustSafetyIncident(adminKey, selectedIncidentId, incidentAction)
      setMessage(`Incident ${payload.incident_id} -> ${payload.status}.`)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  function handleOpenIncidentFromAudit(item) {
    setIncidentForm({
      source_audit_id: item.audit_id,
      surface: item.surface || 'guided_investing',
      topic: item.topic || item.channel || '',
      severity: item.severity || 'high',
      summary: item.output_summary || item.input_summary || `${item.surface} · ${item.route_decision}`,
      owner_id: '',
      notes: `Khởi tạo từ audit ${item.audit_id}. Route: ${item.route_decision}. Risks: ${item.risk_classes.join(', ') || 'none'}.`,
    })
    setMessage(`Đã nạp audit ${item.audit_id} vào incident form.`)
  }

  const selectedIncident = incidents.find((item) => item.incident_id === selectedIncidentId) || null

  return (
    <section className={shellClass}>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Trust Safety Admin</h1>
          <p className="mt-1 text-sm text-slate-600">
            Quản lý audit trust/safety, mở incident và điều phối xử lý thay vì chỉ đọc log thụ động.
          </p>
        </div>
        {onBack ? (
          <button type="button" onClick={onBack} className={secondaryButtonClass}>
            Quay lại Pro Lab Admin
          </button>
        ) : null}
      </header>

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Admin Access</h2>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="min-w-[260px] flex-1 text-sm font-medium text-slate-700">
            Admin key
            <input
              className={inputClass}
              type="password"
              placeholder="ADMIN_TRUST_SAFETY_KEY"
              value={adminKeyInput}
              onChange={(event) => setAdminKeyInput(event.target.value)}
            />
          </label>
          <button type="button" onClick={handleConnect} className={primaryButtonClass}>Kết nối</button>
        </div>
      </section>

      {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
      {message ? <p className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}

      {status ? (
        <section className={sectionClass}>
          <h2 className={sectionTitleClass}>Overview</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <StatusTile label="Total events" value={status.total_events} />
            <StatusTile label="Critical events" value={status.critical_events} />
            <StatusTile label="Blocked events" value={status.blocked_events} />
            <StatusTile label="Default disclaimer injections" value={status.default_disclaimer_injections} />
            <StatusTile label="Frozen surfaces" value={status.frozen_surfaces} />
            <StatusTile label="Degraded surfaces" value={status.degraded_surfaces} />
          </div>
        </section>
      ) : null}

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Filters</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label className="text-sm font-medium text-slate-700">
            Surface
            <input className={inputClass} value={filters.surface} onChange={(e) => setFilters((c) => ({ ...c, surface: e.target.value }))} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Severity
            <select className={inputClass} value={filters.severity} onChange={(e) => setFilters((c) => ({ ...c, severity: e.target.value }))}>
              <option value="">all</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Status
            <select className={inputClass} value={filters.status} onChange={(e) => setFilters((c) => ({ ...c, status: e.target.value }))}>
              <option value="">all</option>
              <option value="open">open</option>
              <option value="investigating">investigating</option>
              <option value="mitigated">mitigated</option>
              <option value="resolved">resolved</option>
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">
            Risk class
            <input className={inputClass} value={filters.riskClass} onChange={(e) => setFilters((c) => ({ ...c, riskClass: e.target.value }))} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Search
            <input className={inputClass} value={filters.search} onChange={(e) => setFilters((c) => ({ ...c, search: e.target.value }))} />
          </label>
        </div>
        <button type="button" onClick={handleApplyFilters} className={`mt-3 ${secondaryButtonClass}`}>Áp dụng filter</button>
      </section>

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Mở Incident</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Source audit id
            <input className={inputClass} value={incidentForm.source_audit_id} onChange={(e) => setIncidentForm((c) => ({ ...c, source_audit_id: e.target.value }))} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Surface
            <input className={inputClass} value={incidentForm.surface} onChange={(e) => setIncidentForm((c) => ({ ...c, surface: e.target.value }))} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Topic
            <input className={inputClass} value={incidentForm.topic} onChange={(e) => setIncidentForm((c) => ({ ...c, topic: e.target.value }))} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Severity
            <select className={inputClass} value={incidentForm.severity} onChange={(e) => setIncidentForm((c) => ({ ...c, severity: e.target.value }))}>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
          </label>
          <label className="md:col-span-2 text-sm font-medium text-slate-700">
            Summary
            <textarea className={inputClass} value={incidentForm.summary} onChange={(e) => setIncidentForm((c) => ({ ...c, summary: e.target.value }))} rows={3} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Owner
            <input className={inputClass} value={incidentForm.owner_id} onChange={(e) => setIncidentForm((c) => ({ ...c, owner_id: e.target.value }))} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Notes
            <textarea className={inputClass} value={incidentForm.notes} onChange={(e) => setIncidentForm((c) => ({ ...c, notes: e.target.value }))} rows={2} />
          </label>
        </div>
        <button type="button" onClick={handleOpenIncident} className={`mt-3 ${primaryButtonClass}`}>Mở incident</button>
      </section>

      <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
        <aside className={sectionClass}>
          <h2 className={sectionTitleClass}>Incidents</h2>
          <ul className="mt-3 space-y-2">
            {incidents.map((item) => (
              <li key={item.incident_id} className="rounded-xl border border-slate-200 bg-white p-3">
                <button
                  type="button"
                  onClick={() => setSelectedIncidentId(item.incident_id)}
                  className={selectedIncidentId === item.incident_id ? 'font-semibold text-teal-700' : 'font-semibold text-slate-900'}
                >
                  {item.surface} · {item.status} · {item.severity}
                </button>
                <p className="mt-1 text-sm text-slate-600">{item.summary}</p>
              </li>
            ))}
          </ul>
        </aside>

        <article className="space-y-4">
          <section className={sectionClass}>
            {selectedIncident ? (
              <section>
                <h2 className={sectionTitleClass}>Incident Action</h2>
                <div className="mt-2 space-y-1 text-sm text-slate-700">
                  <p>ID: {selectedIncident.incident_id}</p>
                  <p>Severity: {selectedIncident.severity}</p>
                  <p>Status: {selectedIncident.status}</p>
                  <p>Owner: {selectedIncident.owner_id || 'unassigned'}</p>
                  <p>Summary: {selectedIncident.summary}</p>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <label className="text-sm font-medium text-slate-700">
                    Action
                    <select className={inputClass} value={incidentAction.action} onChange={(e) => setIncidentAction((c) => ({ ...c, action: e.target.value }))}>
                      <option value="investigate">investigate</option>
                      <option value="mitigate">mitigate</option>
                      <option value="resolve">resolve</option>
                      <option value="reopen">reopen</option>
                      <option value="reassign">reassign</option>
                    </select>
                  </label>
                  <label className="text-sm font-medium text-slate-700">
                    Owner
                    <input className={inputClass} value={incidentAction.owner_id} onChange={(e) => setIncidentAction((c) => ({ ...c, owner_id: e.target.value }))} />
                  </label>
                  <label className="md:col-span-2 text-sm font-medium text-slate-700">
                    Notes
                    <textarea className={inputClass} value={incidentAction.notes} onChange={(e) => setIncidentAction((c) => ({ ...c, notes: e.target.value }))} rows={3} />
                  </label>
                </div>
                <button type="button" className={`mt-3 ${primaryButtonClass}`} onClick={handleIncidentAction}>Lưu incident action</button>
              </section>
            ) : (
              <p className="text-sm text-slate-600">Chọn incident để thao tác.</p>
            )}
          </section>

          <section className={sectionClass}>
            <h2 className={sectionTitleClass}>Audit Logs</h2>
            <ul className="mt-3 space-y-2">
              {audit.slice(0, 25).map((item) => (
                <li key={item.audit_id} className="rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-700">
                  <strong className="text-slate-900">{item.surface}</strong> · {item.channel} · {item.route_decision}
                  <p className="mt-1">Severity: {item.severity}</p>
                  <p>Risks: {item.risk_classes.join(', ') || 'none'}</p>
                  {item.output_summary ? <p>{item.output_summary}</p> : null}
                  <button type="button" className={`mt-2 ${secondaryButtonClass}`} onClick={() => handleOpenIncidentFromAudit(item)}>
                    Mở incident từ log này
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </article>
      </div>
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
