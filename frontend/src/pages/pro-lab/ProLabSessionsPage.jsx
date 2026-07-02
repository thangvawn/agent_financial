const sectionClass = 'p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4'
const primaryButtonClass = 'px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016]'
const secondaryButtonClass = 'px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 text-rose-400 bg-transparent border border-rose-500/20 hover:bg-rose-500/10 disabled:opacity-50 disabled:pointer-events-none'

export default function ProLabSessionsPage({ sessionsPayload, onRefresh, onRevoke }) {
  if (!sessionsPayload) {
    return <p className="text-xs text-[#88aab8]">Cấp token và mở workspace để xem active sessions.</p>
  }

  return (
    <div className="grid gap-4 text-[#c8d6d2]">
      <section className={`${sectionClass} flex flex-wrap items-center justify-between gap-3`}>
        <div>
          <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Access Control</p>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mt-1">Active Sessions</h2>
          <p className="text-xs text-[#88aab8] mt-1">Quản lý token đang dùng cho Pro Lab local/private testing.</p>
        </div>
        <button type="button" className={primaryButtonClass} onClick={onRefresh}>Refresh</button>
      </section>
      {sessionsPayload.sessions.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {sessionsPayload.sessions.map((item) => (
            <article key={item.token_id} className={sectionClass}>
              <div className="flex items-center justify-between gap-2">
                <strong className="text-white font-bold text-xs">{item.role}</strong>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">{item.status}</span>
              </div>
              <p className="mt-2 break-all rounded-lg border border-[#88aab8]/10 bg-[#0c1720]/40 p-2.5 text-xs text-[#88aab8] font-mono">{item.token_id}</p>
              <dl className="mt-2 space-y-1.5 text-xs text-[#88aab8]">
                <div><dt className="inline font-bold text-white">Created:</dt> <dd className="inline">{item.created_at}</dd></div>
                <div><dt className="inline font-bold text-white">Expires:</dt> <dd className="inline">{item.expires_at || 'n/a'}</dd></div>
                <div><dt className="inline font-bold text-white">Scopes:</dt> <dd className="inline">{item.scopes.join(', ')}</dd></div>
              </dl>
              {item.is_current ? <span className="mt-2 inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/20 text-emerald-400 border border-emerald-900/30 self-start">Current session</span> : null}
              <button type="button" className={`mt-3 ${secondaryButtonClass} self-start`} onClick={() => onRevoke(item.token_id)} disabled={item.status !== 'active'}>
                Revoke session
              </button>
            </article>
          ))}
        </div>
      ) : (
        <p className="text-xs text-[#88aab8]">Chưa có session nào.</p>
      )}
    </div>
  )
}
