import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

export default function TodayBriefSection({
  todayBrief,
  activeArticleId,
  savedIds,
  onSelectBrief,
  onSaveBrief,
}) {
  const restBriefs = todayBrief.slice(1)

  if (restBriefs.length === 0) return null

  return (
    <section className="flex flex-col gap-4 mb-6">
      {/* Title head */}
      <div className="flex items-center gap-2">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Tóm lược thị trường (Today Brief)
        </h2>
        <span className="text-[10px] text-slate-500 font-mono">
          ({restBriefs.length} phân tích nhanh)
        </span>
      </div>

      {/* Brief Card Grid */}
      <div className="flex flex-wrap gap-4 w-full">
        {restBriefs.map((item) => {
          const isActive = item.article_id === activeArticleId
          const isSaved = savedIds.has(item.article_id)

          return (
            <div
              key={item.article_id}
              className={`bg-[#161b26] border rounded-md p-4 flex flex-col justify-between gap-3 transition-all cursor-pointer flex-1 min-w-[280px] max-w-[480px] ${
                isActive
                  ? 'border-teal-500/40 shadow-sm bg-teal-950/5'
                  : 'border-[#1f293d] hover:border-slate-700'
              }`}
              onClick={() => onSelectBrief(item.article_id)}
            >
              <div>
                {/* Badge and Metadata */}
                <div className="flex items-center justify-between text-[9px] text-slate-500 font-mono mb-2">
                  {item.importance_label && item.importance_label !== 'noise' && (
                    <span className="px-1 py-0.2 bg-amber-500/10 text-amber-400 font-bold uppercase rounded-[2px]">
                      {item.importance_label}
                    </span>
                  )}
                  <span>
                    {item.source} · {item.time || formatNewsDate(item.published_at)}
                  </span>
                </div>

                {/* Headline */}
                <h3 className={`text-xs font-bold leading-snug line-clamp-2 ${isActive ? 'text-white' : 'text-slate-200'}`}>
                  {item.headline}
                </h3>

                {/* Why it matters */}
                <p className="text-[11px] text-slate-450 leading-relaxed mt-2 line-clamp-3 italic">
                  {item.why_it_matters}
                </p>
              </div>

              {/* Tags and actions */}
              <div className="flex items-center justify-between gap-2 border-t border-[#1f293d]/50 pt-2 mt-1">
                <div className="flex flex-wrap gap-1 min-w-0">
                  {item.affected_markets?.slice(0, 2).map((m) => (
                    <span
                      key={m}
                      className="px-1.5 py-0.5 bg-[#0f1420] border border-[#1f293d]/50 rounded-[3px] text-[8.5px] font-mono text-teal-400 truncate"
                    >
                      {m}
                    </span>
                  ))}
                </div>

                <button
                  type="button"
                  className={`text-[9px] font-bold tracking-wide uppercase transition-colors shrink-0 cursor-pointer ${
                    isSaved ? 'text-teal-400' : 'text-slate-500 hover:text-slate-350'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation()
                    onSaveBrief(item.article_id)
                  }}
                >
                  {isSaved ? '✓ SAVED' : 'SAVE'}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
