import { useEffect, useState } from 'react'

import {
  bootstrapProLabAdminToken,
  fetchProLabAdminExperiments,
  fetchProLabAdminRuns,
  fetchProLabAuditLogs,
  reviewProLabExperiment,
} from '../../modules/pro-lab-admin'

const DEFAULT_REVIEW = {
  review_status: 'approved',
  review_notes: '',
}

export default function ProLabAdminPage({ onBack, onOpenTrustSafety, onOpenAnalytics }) {
  const [adminKeyInput, setAdminKeyInput] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [experiments, setExperiments] = useState([])
  const [runs, setRuns] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [selectedExperimentId, setSelectedExperimentId] = useState('')
  const [reviewForm, setReviewForm] = useState(DEFAULT_REVIEW)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const savedKey = window.localStorage.getItem('pro_lab.admin_key') || ''
    const savedToken = window.localStorage.getItem('pro_lab.admin_token') || ''
    setAdminKeyInput(savedKey)
    setAdminKey(savedKey)
    setAccessToken(savedToken)
  }, [])

  useEffect(() => {
    if (accessToken) {
      window.localStorage.setItem('pro_lab.admin_token', accessToken)
    }
  }, [accessToken])

  useEffect(() => {
    if (!accessToken) return
    let cancelled = false
    async function run() {
      setLoading(true)
      setError('')
      try {
        const [experimentsPayload, runsPayload, auditPayload] = await Promise.all([
          fetchProLabAdminExperiments(accessToken),
          fetchProLabAdminRuns(accessToken),
          fetchProLabAuditLogs(accessToken),
        ])
        if (cancelled) return
        setExperiments(experimentsPayload.items || [])
        setRuns(runsPayload.items || [])
        setAuditLogs(auditPayload.items || [])
        if (!selectedExperimentId && experimentsPayload.items?.length) {
          setSelectedExperimentId(experimentsPayload.items[0].experiment_id)
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [accessToken, selectedExperimentId])

  const selectedExperiment = experiments.find((item) => item.experiment_id === selectedExperimentId) || null

  async function handleConnect() {
    setError('')
    setMessage('')
    if (!adminKeyInput.trim()) {
      setError('Nhập admin key để bootstrap admin token.')
      return
    }
    try {
      const payload = await bootstrapProLabAdminToken(adminKeyInput.trim())
      window.localStorage.setItem('pro_lab.admin_key', adminKeyInput.trim())
      setAdminKey(adminKeyInput.trim())
      setAccessToken(payload.access_token)
      setMessage('Đã bootstrap admin token cho Pro Lab.')
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleReview() {
    if (!selectedExperimentId || !accessToken) return
    setError('')
    setMessage('')
    try {
      const reviewed = await reviewProLabExperiment(selectedExperimentId, reviewForm, accessToken)
      setMessage(`Experiment ${reviewed.experiment_id} đã được review: ${reviewed.review_status}.`)
      const experimentsPayload = await fetchProLabAdminExperiments(accessToken)
      setExperiments(experimentsPayload.items || [])
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section>
      <h1>Pro Lab Admin</h1>
      <p>Dashboard tối thiểu cho audit logs và experiment review, tách khỏi retail surface.</p>
      {onBack ? (
        <button type="button" onClick={onBack}>
          Quay lại Pro Lab
        </button>
      ) : null}
      {onOpenTrustSafety ? (
        <button type="button" onClick={onOpenTrustSafety}>
          Mở Trust Safety Admin
        </button>
      ) : null}
      {onOpenAnalytics ? (
        <button type="button" onClick={onOpenAnalytics}>
          Mở Analytics Admin
        </button>
      ) : null}

      <section>
        <h2>Admin Access</h2>
        <input
          type="password"
          value={adminKeyInput}
          placeholder="ADMIN_TRADING_LAB_KEY"
          onChange={(event) => setAdminKeyInput(event.target.value)}
        />
        <button type="button" onClick={handleConnect}>
          Bootstrap admin token
        </button>
        {adminKey ? <p>Admin key loaded.</p> : null}
        {accessToken ? <p>Admin token active: {accessToken.slice(0, 18)}...</p> : null}
      </section>

      {error ? <p>{error}</p> : null}
      {message ? <p>{message}</p> : null}
      {loading ? <p>Đang tải admin review...</p> : null}

      {!accessToken ? null : (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16 }}>
          <aside>
            <h2>Experiments</h2>
            <ul style={{ paddingLeft: 18 }}>
              {experiments.map((item) => (
                <li key={item.experiment_id}>
                  <button type="button" onClick={() => setSelectedExperimentId(item.experiment_id)}>
                    {item.experiment_type} · {item.review_status}
                  </button>
                  <p>{item.user_id}</p>
                </li>
              ))}
            </ul>
          </aside>

          <article>
            {selectedExperiment ? (
              <section>
                <h2>Experiment Review</h2>
                <p>ID: {selectedExperiment.experiment_id}</p>
                <p>User: {selectedExperiment.user_id}</p>
                <p>Type: {selectedExperiment.experiment_type}</p>
                <p>Status: {selectedExperiment.status}</p>
                <p>Current review: {selectedExperiment.review_status}</p>
                {selectedExperiment.review_notes ? <p>Notes: {selectedExperiment.review_notes}</p> : null}
                <label>
                  Review status
                  <select
                    value={reviewForm.review_status}
                    onChange={(event) => setReviewForm((current) => ({ ...current, review_status: event.target.value }))}
                  >
                    <option value="approved">approved</option>
                    <option value="needs_changes">needs_changes</option>
                    <option value="rejected">rejected</option>
                  </select>
                </label>
                <label>
                  Review notes
                  <textarea
                    value={reviewForm.review_notes}
                    onChange={(event) => setReviewForm((current) => ({ ...current, review_notes: event.target.value }))}
                  />
                </label>
                <button type="button" onClick={handleReview}>
                  Lưu review
                </button>
              </section>
            ) : (
              <p>Chọn experiment để review.</p>
            )}

            <section>
              <h2>Experiment Runs</h2>
              {runs.length ? (
                <ul>
                  {runs.slice(0, 20).map((item) => (
                    <li key={item.run_id}>
                      <strong>{item.provider_id}:{item.command_id}</strong> · {item.status} · {item.progress_pct}%
                      <p>Risk flags: {item.safety_flags?.join(', ') || 'n/a'}</p>
                      <p>User: {item.user_id} · Experiment: {item.experiment_id || 'n/a'}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>Chưa có experiment run nào.</p>
              )}
            </section>

            <section>
              <h2>Audit Logs</h2>
              {auditLogs.length ? (
                <ul>
                  {auditLogs.slice(0, 20).map((item) => (
                    <li key={item.audit_id}>
                      <strong>{item.action}</strong> · {item.surface} · {item.created_at}
                      <p>{item.target_type}: {item.target_id || 'n/a'}</p>
                      <p>Actor: {item.actor_id}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>Chưa có audit log nào.</p>
              )}
            </section>
          </article>
        </div>
      )}
    </section>
  )
}
