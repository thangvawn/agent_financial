import { useEffect, useState } from 'react'

import { fetchCommunityModerationQueue, reviewCommunityModeration } from '../../modules/community'

const shellClass = 'mx-auto flex w-full max-w-6xl flex-col gap-5 rounded-[28px] border border-slate-200/70 bg-white/90 p-6 text-slate-800 shadow-[0_18px_45px_rgba(15,23,42,0.08)]'
const sectionClass = 'rounded-2xl border border-slate-200 bg-slate-50/80 p-4'
const inputClass = 'mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100'
const primaryButtonClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800'
const secondaryButtonClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100'

export default function CommunityModerationPage({ onBack }) {
  const [moderatorKey, setModeratorKey] = useState(() => window.localStorage.getItem('community.moderator_key') || 'community-dev')
  const [queueItems, setQueueItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    space_id: '',
    risk_label: '',
    search: '',
  })

  useEffect(() => {
    window.localStorage.setItem('community.moderator_key', moderatorKey)
  }, [moderatorKey])

  async function loadQueue() {
    setLoading(true)
    setError('')
    try {
      const payload = await fetchCommunityModerationQueue(moderatorKey, filters)
      setQueueItems(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleReview(item, action) {
    setError('')
    try {
      await reviewCommunityModeration(
        {
          content_type: item.content_type,
          content_id: item.content_id,
          action,
          reviewer_id: 'community-moderator',
          notes: `Dashboard action: ${action}`,
        },
        moderatorKey,
      )
      await loadQueue()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className={shellClass}>
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Community Moderation Dashboard</h1>
          <p className="mt-1 text-sm text-slate-600">Surface moderation tách riêng khỏi community để review tập trung hơn.</p>
        </div>
        <button type="button" onClick={onBack} className={secondaryButtonClass}>Quay lại Community</button>
      </header>

      <section className={sectionClass}>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-sm font-medium text-slate-700">
            Moderator key
            <input className={inputClass} value={moderatorKey} onChange={(event) => setModeratorKey(event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Filter theo space
            <input
              className={inputClass}
              value={filters.space_id}
              onChange={(event) => setFilters((current) => ({ ...current, space_id: event.target.value }))}
              placeholder="goal-planning-circle"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Filter theo risk label
            <input
              className={inputClass}
              value={filters.risk_label}
              onChange={(event) => setFilters((current) => ({ ...current, risk_label: event.target.value }))}
              placeholder="pump_and_dump"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Search preview
            <input
              className={inputClass}
              value={filters.search}
              onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
              placeholder="telegram / gia muc tieu / FPT"
            />
          </label>
        </div>
        <button type="button" onClick={loadQueue} className={`mt-3 ${primaryButtonClass}`}>Tải moderation queue</button>
      </section>

      {loading ? <p className="text-sm text-slate-600">Đang tải queue...</p> : null}
      {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {queueItems.length ? (
        <ul className="space-y-3">
          {queueItems.map((item) => (
            <li key={item.event_id} className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
              <p className="text-sm font-semibold text-slate-900">{item.content_type} · {item.space_id || 'unknown space'}</p>
              <p className="mt-1 text-sm text-slate-700">{item.content_preview}</p>
              {item.ai_risk_labels.length ? <p className="mt-1 text-xs uppercase tracking-wide text-amber-700">{item.ai_risk_labels.join(', ')}</p> : null}
              {item.notes ? <p className="mt-1 text-xs text-slate-500">{item.notes}</p> : null}
              <div className="mt-3 flex flex-wrap gap-2">
                <button type="button" className={primaryButtonClass} onClick={() => handleReview(item, 'publish')}>
                  Publish
                </button>
                <button type="button" className={secondaryButtonClass} onClick={() => handleReview(item, 'reject')}>
                  Reject
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-600">Chưa có item nào trong queue hoặc bạn chưa tải queue.</p>
      )}
    </section>
  )
}
