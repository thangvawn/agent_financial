import { useEffect, useMemo, useState } from 'react'

import {
  approveContentOpsItem,
  archiveContentOpsItem,
  fetchContentOpsAnalytics,
  fetchContentOpsItem,
  fetchContentOpsReviewQueue,
  fetchContentOpsStatus,
  generateContentOpsAiDraft,
  listContentOpsItems,
  listContentOpsVersions,
  publishContentOpsItem,
  rollbackContentOpsItem,
  submitContentOpsReview,
  upsertContentOpsItem,
} from '../../modules/content-ops-admin'

const CONTENT_TYPES = [
  'lesson',
  'course',
  'path',
  'quiz',
  'glossary_term',
  'contextual_explainer',
  'nudge_template',
  'disclaimer_block',
  'community_policy_snippet',
]

const DEFAULT_FORM = {
  content_id: 'new',
  slug: '',
  title: '',
  locale: 'vi-VN',
  owner_team: 'education',
  risk_category: 'education',
  payload_text: '{\n  "title": "",\n  "body": []\n}',
  change_summary: '',
}

const DEFAULT_PAYLOAD_BY_TYPE = {
  lesson: '{\n  "title": "",\n  "summary": "",\n  "tier": "financial_basics",\n  "content_type": "micro_lesson",\n  "estimated_minutes": 3,\n  "body": [],\n  "glossary_refs": [],\n  "quiz_questions": []\n}',
  course: '{\n  "course_id": "",\n  "title": "",\n  "description": "",\n  "tier": "financial_basics",\n  "lesson_ids": []\n}',
  path: '{\n  "path_id": "",\n  "title": "",\n  "persona_segment": "starter",\n  "lesson_ids": [],\n  "description": ""\n}',
  quiz: '{\n  "title": "",\n  "questions_json": []\n}',
  glossary_term: '{\n  "term": "",\n  "short_definition": "",\n  "long_definition": ""\n}',
  contextual_explainer: '{\n  "surface": "learning",\n  "trigger_key": "",\n  "title": "",\n  "body": [],\n  "linked_lesson_ids": [],\n  "guardrail_note": ""\n}',
  nudge_template: '{\n  "surface": "home",\n  "trigger_type": "",\n  "persona_tags": [],\n  "title_template": "",\n  "message_template": "",\n  "cta_label": "",\n  "cta_path_template": ""\n}',
  disclaimer_block: '{\n  "surface": "",\n  "topic": "",\n  "short_text": "",\n  "full_text": "",\n  "severity": "medium"\n}',
  community_policy_snippet: '{\n  "surface": "community",\n  "policy_type": "posting_rule",\n  "body": "",\n  "risk_tags": []\n}',
}

const shellClass = 'mx-auto flex w-full max-w-[1720px] flex-col gap-5 rounded-[28px] border border-slate-200/70 bg-white/90 px-6 md:px-10 py-6 text-slate-800 shadow-[0_18px_45px_rgba(15,23,42,0.08)]'
const sectionClass = 'rounded-2xl border border-slate-200 bg-slate-50/80 p-4'
const sectionTitleClass = 'text-lg font-semibold text-slate-900'
const inputClass = 'mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100'
const primaryButtonClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50'
const secondaryButtonClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50'

export default function ContentOpsAdminPage({ onBack }) {
  const [adminKeyInput, setAdminKeyInput] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [role, setRole] = useState('admin')
  const [status, setStatus] = useState(null)
  const [contentType, setContentType] = useState('lesson')
  const [items, setItems] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [versions, setVersions] = useState([])
  const [reviewQueue, setReviewQueue] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [form, setForm] = useState(DEFAULT_FORM)
  const [aiPrompt, setAiPrompt] = useState('Tao draft ngan gon, trust-first, education-first.')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const savedKey = window.localStorage.getItem('content-ops.admin_key') || ''
    const savedRole = window.localStorage.getItem('content-ops.role') || 'admin'
    setAdminKeyInput(savedKey)
    setAdminKey(savedKey)
    setRole(savedRole)
  }, [])

  useEffect(() => {
    if (!adminKey) return
    let cancelled = false
    async function run() {
      setLoading(true)
      setError('')
      try {
        const [statusPayload, itemsPayload, queuePayload] = await Promise.all([
          fetchContentOpsStatus(adminKey, role),
          listContentOpsItems(adminKey, role, contentType),
          fetchContentOpsReviewQueue(adminKey, role),
        ])
        if (cancelled) return
        setStatus(statusPayload)
        setItems(itemsPayload)
        setReviewQueue(queuePayload)
        if (!selectedId && itemsPayload.length) {
          setSelectedId(itemsPayload[0].content_id)
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
  }, [adminKey, role, contentType])

  useEffect(() => {
    if (!adminKey || !selectedId || selectedId === 'new') return
    let cancelled = false
    async function run() {
      setLoading(true)
      setError('')
      try {
        const [itemPayload, versionPayload, analyticsPayload] = await Promise.all([
          fetchContentOpsItem(adminKey, role, selectedId),
          listContentOpsVersions(adminKey, role, selectedId),
          fetchContentOpsAnalytics(adminKey, role, selectedId),
        ])
        if (cancelled) return
        setVersions(versionPayload)
        setAnalytics(analyticsPayload)
        setForm({
          content_id: itemPayload.content_id,
          slug: itemPayload.slug,
          title: itemPayload.title,
          locale: itemPayload.locale,
          owner_team: itemPayload.owner_team,
          risk_category: itemPayload.risk_category,
          payload_text: JSON.stringify(itemPayload.latest_payload || {}, null, 2),
          change_summary: '',
        })
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
  }, [adminKey, role, selectedId])

  const permissions = useMemo(() => status?.permissions || [], [status])

  function handleConnect() {
    setError('')
    setMessage('')
    if (!adminKeyInput.trim()) {
      setError('Nhap ADMIN_CONTENT_OPS_KEY de mo Content Ops CMS.')
      return
    }
    window.localStorage.setItem('content-ops.admin_key', adminKeyInput.trim())
    window.localStorage.setItem('content-ops.role', role)
    setAdminKey(adminKeyInput.trim())
  }

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function resetDraft() {
    setSelectedId('new')
    setVersions([])
    setAnalytics(null)
    setForm({
      ...DEFAULT_FORM,
      title: `${contentType} draft`,
      slug: `${contentType}-draft`,
      payload_text: DEFAULT_PAYLOAD_BY_TYPE[contentType] || DEFAULT_FORM.payload_text,
    })
  }

  function parsePayload() {
    try {
      return JSON.parse(form.payload_text || '{}')
    } catch (err) {
      throw new Error('Payload JSON khong hop le.')
    }
  }

  async function reloadList(nextSelectedId = selectedId) {
    const [itemsPayload, queuePayload] = await Promise.all([
      listContentOpsItems(adminKey, role, contentType),
      fetchContentOpsReviewQueue(adminKey, role),
    ])
    setItems(itemsPayload)
    setReviewQueue(queuePayload)
    if (nextSelectedId) setSelectedId(nextSelectedId)
  }

  async function handleSaveDraft() {
    setError('')
    setMessage('')
    try {
      const saved = await upsertContentOpsItem(adminKey, role, contentType, form.content_id || 'new', {
        slug: form.slug,
        title: form.title,
        locale: form.locale,
        owner_team: form.owner_team,
        risk_category: form.risk_category,
        payload: parsePayload(),
        change_summary: form.change_summary,
      })
      setMessage(`Da luu draft ${saved.content_id} o version ${saved.current_version}.`)
      await reloadList(saved.content_id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleWorkflow(action) {
    if (!selectedId || selectedId === 'new') return
    setError('')
    setMessage('')
    try {
      let payload
      if (action === 'submit') {
        payload = await submitContentOpsReview(adminKey, role, selectedId, { comments: form.change_summary })
      } else if (action === 'approve') {
        payload = await approveContentOpsItem(adminKey, role, selectedId, { comments: form.change_summary })
      } else if (action === 'publish') {
        payload = await publishContentOpsItem(adminKey, role, selectedId, { comments: form.change_summary })
      } else {
        payload = await archiveContentOpsItem(adminKey, role, selectedId, { comments: form.change_summary })
      }
      setMessage(`Da cap nhat workflow sang ${payload.workflow_state}.`)
      await reloadList(payload.content_id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRollback(versionNumber) {
    if (!selectedId || selectedId === 'new') return
    setError('')
    setMessage('')
    try {
      const payload = await rollbackContentOpsItem(adminKey, role, selectedId, {
        version_number: versionNumber,
        comments: `Rollback to version ${versionNumber}`,
      })
      setMessage(`Da rollback ${payload.content_id} ve version ${versionNumber} va republish.`)
      await reloadList(payload.content_id)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleAiDraft() {
    setError('')
    setMessage('')
    try {
      const payload = await generateContentOpsAiDraft(adminKey, role, {
        content_type: contentType,
        title: form.title || `${contentType} AI draft`,
        prompt: aiPrompt,
        locale: form.locale,
        owner_team: form.owner_team,
        risk_category: form.risk_category,
      })
      setMessage(`Da tao AI-assisted draft ${payload.content_id}.`)
      await reloadList(payload.content_id)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className={shellClass}>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Admin CMS / Content Ops</h1>
          <p className="mt-1 text-sm text-slate-600">
            Quản lý content objects, workflow review/publish, analytics và AI-assisted drafts trong một surface.
          </p>
        </div>
        {onBack ? <button type="button" onClick={onBack} className={secondaryButtonClass}>Quay lai admin truoc</button> : null}
      </header>

      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Ket noi</h2>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="min-w-[260px] flex-1 text-sm font-medium text-slate-700">
            Content Ops key
            <input
              className={inputClass}
              type="password"
              placeholder="ADMIN_CONTENT_OPS_KEY"
              value={adminKeyInput}
              onChange={(event) => setAdminKeyInput(event.target.value)}
            />
          </label>
          <label className="w-56 text-sm font-medium text-slate-700">
            Role
            <select className={inputClass} value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="admin">admin</option>
              <option value="editor">editor</option>
              <option value="reviewer">reviewer</option>
              <option value="compliance_reviewer">compliance_reviewer</option>
              <option value="moderator">moderator</option>
            </select>
          </label>
          <button type="button" onClick={handleConnect} className={primaryButtonClass}>Mo Content Ops</button>
        </div>
        {status ? (
          <p className="mt-2 text-xs text-slate-600">
            Permissions: {permissions.join(', ') || 'n/a'} · Pending review: {status.analytics_overview.pending_review_count}
          </p>
        ) : null}
      </section>

      {!adminKey ? null : (
        <section className={sectionClass}>
          <div className="mb-4 flex flex-wrap gap-2">
            {CONTENT_TYPES.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  setContentType(item)
                  resetDraft()
                }}
                className={contentType === item ? primaryButtonClass : secondaryButtonClass}
              >
                {item}
              </button>
            ))}
            <button type="button" onClick={resetDraft} className={secondaryButtonClass}>Tao draft moi</button>
          </div>

          {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
          {message ? <p className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
          {loading ? <p className="text-sm text-slate-600">Dang tai Content Ops...</p> : null}

          <div className="mt-4 grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
            <aside className="rounded-xl border border-slate-200 bg-white p-3">
              <h3 className="font-semibold text-slate-900">Items</h3>
              <ul className="mt-2 space-y-2">
                {items.map((item) => (
                  <li key={item.content_id} className="rounded-lg border border-slate-200 bg-slate-50 p-2">
                    <button type="button" className="text-left text-sm font-semibold text-slate-900 hover:text-teal-700" onClick={() => setSelectedId(item.content_id)}>
                      {item.title}
                    </button>
                    <p className="mt-1 text-xs text-slate-500">{item.workflow_state} · v{item.current_version}</p>
                  </li>
                ))}
              </ul>
            </aside>

            <article className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4">
              <label className="text-sm font-medium text-slate-700">
                Content ID
                <input className={inputClass} value={form.content_id} onChange={(event) => updateField('content_id', event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Slug
                <input className={inputClass} value={form.slug} onChange={(event) => updateField('slug', event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Title
                <input className={inputClass} value={form.title} onChange={(event) => updateField('title', event.target.value)} />
              </label>
              <div className="grid gap-3 md:grid-cols-3">
                <label className="text-sm font-medium text-slate-700">
                  Locale
                  <input className={inputClass} value={form.locale} onChange={(event) => updateField('locale', event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Owner team
                  <input className={inputClass} value={form.owner_team} onChange={(event) => updateField('owner_team', event.target.value)} />
                </label>
                <label className="text-sm font-medium text-slate-700">
                  Risk category
                  <input className={inputClass} value={form.risk_category} onChange={(event) => updateField('risk_category', event.target.value)} />
                </label>
              </div>
              <label className="text-sm font-medium text-slate-700">
                Change summary
                <input className={inputClass} value={form.change_summary} onChange={(event) => updateField('change_summary', event.target.value)} />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Payload JSON
                <textarea className={inputClass} value={form.payload_text} rows={14} onChange={(event) => updateField('payload_text', event.target.value)} />
              </label>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={handleSaveDraft} className={primaryButtonClass}>Luu draft</button>
                <button type="button" onClick={() => handleWorkflow('submit')} disabled={selectedId === 'new'} className={secondaryButtonClass}>Submit review</button>
                <button type="button" onClick={() => handleWorkflow('approve')} disabled={selectedId === 'new'} className={secondaryButtonClass}>Approve</button>
                <button type="button" onClick={() => handleWorkflow('publish')} disabled={selectedId === 'new'} className={secondaryButtonClass}>Publish</button>
                <button type="button" onClick={() => handleWorkflow('archive')} disabled={selectedId === 'new'} className={secondaryButtonClass}>Archive</button>
              </div>
              <label className="text-sm font-medium text-slate-700">
                AI draft prompt
                <textarea className={inputClass} value={aiPrompt} rows={4} onChange={(event) => setAiPrompt(event.target.value)} />
              </label>
              <button type="button" onClick={handleAiDraft} className={secondaryButtonClass}>Tao AI-assisted draft</button>
            </article>

            <aside className="grid gap-3">
              <section className="rounded-xl border border-slate-200 bg-white p-3">
                <h3 className="font-semibold text-slate-900">Versions</h3>
                {versions.length ? (
                  <ul className="mt-2 space-y-2 text-sm text-slate-700">
                    {versions.map((item) => (
                      <li key={item.version_id} className="rounded-lg border border-slate-200 bg-slate-50 p-2">
                        v{item.version_number} · {item.status} · {item.origin}
                        <div className="mt-2">
                          <button type="button" onClick={() => handleRollback(item.version_number)} className={secondaryButtonClass}>
                            Rollback
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-600">Chua co version.</p>
                )}
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-3">
                <h3 className="font-semibold text-slate-900">Review queue</h3>
                {reviewQueue.length ? (
                  <ul className="mt-2 space-y-1 text-sm text-slate-700">
                    {reviewQueue.slice(0, 10).map((item) => (
                      <li key={item.task_id}>
                        {item.content_id} · {item.review_type} · {item.assignee_role}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-600">Khong co pending review.</p>
                )}
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-3">
                <h3 className="font-semibold text-slate-900">Analytics</h3>
                {analytics ? (
                  <ul className="mt-2 space-y-1 text-sm text-slate-700">
                    <li>Impressions: {analytics.impression_count}</li>
                    <li>Opens: {analytics.open_count}</li>
                    <li>Completions: {analytics.completion_count}</li>
                    <li>CTR: {analytics.clickthrough_count}</li>
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-600">Chua co analytics.</p>
                )}
              </section>
            </aside>
          </div>
        </section>
      )}
    </section>
  )
}
