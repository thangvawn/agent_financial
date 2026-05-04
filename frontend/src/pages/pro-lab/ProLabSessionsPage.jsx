const sectionClass = 'rounded-2xl border border-slate-200 bg-slate-50/80 p-4'
const primaryButtonClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800'
const secondaryButtonClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50'

export default function ProLabSessionsPage({ sessionsPayload, onRefresh, onRevoke }) {
  if (!sessionsPayload) {
    return <p className="text-sm text-slate-600">Cấp token và mở workspace để xem active sessions.</p>
  }

  return (
    <section className="grid gap-4">
      <section className={`${sectionClass} flex flex-wrap items-center justify-between gap-3`}>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">Access Control</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Active Sessions</h2>
          <p className="mt-1 text-sm text-slate-600">Quản lý token đang dùng cho Pro Lab local/private testing.</p>
        </div>
        <button type="button" className={primaryButtonClass} onClick={onRefresh}>Refresh</button>
      </section>
      {sessionsPayload.sessions.length ? (
        <div className="grid gap-3 md:grid-cols-2">
          {sessionsPayload.sessions.map((item) => (
            <article key={item.token_id} className={sectionClass}>
              <div className="flex items-center justify-between gap-2">
                <strong className="text-slate-900">{item.role}</strong>
                <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs font-semibold text-slate-600">{item.status}</span>
              </div>
              <p className="mt-2 break-all rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-600">{item.token_id}</p>
              <dl className="mt-2 space-y-1 text-sm text-slate-700">
                <div><dt className="inline font-semibold text-slate-900">Created:</dt> <dd className="inline">{item.created_at}</dd></div>
                <div><dt className="inline font-semibold text-slate-900">Expires:</dt> <dd className="inline">{item.expires_at || 'n/a'}</dd></div>
                <div><dt className="inline font-semibold text-slate-900">Scopes:</dt> <dd className="inline">{item.scopes.join(', ')}</dd></div>
              </dl>
              {item.is_current ? <span className="mt-2 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">Current session</span> : null}
              <button type="button" className={`mt-3 ${secondaryButtonClass}`} onClick={() => onRevoke(item.token_id)} disabled={item.status !== 'active'}>
                Revoke session
              </button>
            </article>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-600">Chưa có session nào.</p>
      )}
    </section>
  )
}
