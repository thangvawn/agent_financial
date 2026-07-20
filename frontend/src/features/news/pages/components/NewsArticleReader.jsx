import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

export default function NewsArticleReader({
  activeArticle,
  detail,
  detailLoading,
  savedIds,
  onSave,
  onSelectRelated,
}) {
  if (!activeArticle) {
    return (
      <div className="bg-[#161b26] border border-[#1f293d] rounded-md p-8 flex flex-col items-center justify-center text-center h-full min-h-[500px]">
        <div className="w-10 h-10 border-2 border-teal-500/20 border-t-teal-500 rounded-full animate-spin mb-4" />
        <p className="text-xs text-slate-500">Đang tải cấu trúc dữ liệu...</p>
      </div>
    )
  }

  const isSaved = savedIds.has(activeArticle.article_id)
  const sourceUrl = detail?.original_source || activeArticle.url

  return (
    <article className="bg-[#161b26] border border-[#1f293d] rounded-md p-5 flex flex-col gap-6 h-full min-h-[500px] relative">
      {/* Detail Loader Overlay */}
      {detailLoading && (
        <div className="absolute inset-0 bg-[#161b26]/75 backdrop-blur-[2px] flex items-center justify-center z-10 rounded-md">
          <div className="flex items-center gap-2 text-xs font-bold text-teal-400 font-mono">
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>ĐANG PHÂN TÍCH...</span>
          </div>
        </div>
      )}

      {/* Main Metadata Row */}
      <div className="flex items-center justify-between flex-wrap gap-3 border-b border-[#1f293d]/50 pb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2 py-0.5 bg-[#0f1420] border border-[#1f293d] rounded text-[10px] font-mono text-slate-400">
            {activeArticle.source}
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {formatNewsDate(activeArticle.published_at)}
          </span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider font-mono ${
            activeArticle.sentiment === 'positive'
              ? 'bg-emerald-500/10 text-emerald-450'
              : activeArticle.sentiment === 'negative'
              ? 'bg-red-500/10 text-red-405'
              : 'bg-slate-700/20 text-slate-400'
          }`}>
            SẮC THÁI: {activeArticle.sentiment || 'neutral'}
          </span>
        </div>

        {/* Save/Bookmark button */}
        <button
          type="button"
          onClick={() => onSave(activeArticle.article_id)}
          className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded border cursor-pointer transition-all ${
            isSaved
              ? 'bg-teal-950/20 border-teal-500/40 text-teal-400'
              : 'bg-[#0f1420] border-[#1f293d] text-slate-400 hover:border-[#0d9488] hover:text-white'
          }`}
        >
          {isSaved ? '✓ ĐÃ LƯU' : 'LƯU TIN'}
        </button>
      </div>

      {/* Headline */}
      <h2 className="text-lg font-bold leading-normal text-white tracking-tight">
        {activeArticle.headline}
      </h2>

      {/* Summary Box */}
      <section className="bg-[#0f1420] border border-[#1f293d]/70 rounded p-4 flex flex-col gap-3">
        <h3 className="text-[10px] text-teal-450 uppercase font-black tracking-wider">
          Tóm tắt &amp; Luận điểm
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed font-medium">
          {activeArticle.summary?.trim()
            ? activeArticle.summary
            : 'Nguồn chỉ cung cấp tiêu đề ngắn. Vui lòng mở bài viết gốc ở nút bên dưới để xem nội dung đầy đủ.'}
        </p>

        {sourceUrl && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="w-fit text-teal-400 hover:text-teal-300 font-bold text-xs flex items-center gap-1.5 transition-colors cursor-pointer mt-1"
          >
            Xem bài viết gốc ↗
          </a>
        )}
      </section>

      {/* Affected markets */}
      {(detail?.affected_markets || activeArticle.affected_markets)?.length > 0 && (
        <section className="flex flex-col gap-2">
          <h3 className="text-[10px] text-slate-500 uppercase font-black tracking-wider">
            Thị trường &amp; Ngành ảnh hưởng
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {(detail?.affected_markets || activeArticle.affected_markets).map((market) => (
              <span
                key={market}
                className="px-2 py-0.5 bg-[#0f1420] border border-[#1f293d] rounded text-xs font-mono text-teal-400"
              >
                {market}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Related articles */}
      {detail?.related_articles?.length > 0 && (
        <section className="flex flex-col gap-3 border-t border-[#1f293d]/45 pt-4">
          <h3 className="text-[10px] text-slate-500 uppercase font-black tracking-wider">
            Tin tức liên quan khác
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {detail.related_articles.map((ra) => (
              <div
                key={ra.article_id}
                role="button"
                tabIndex={0}
                className="w-full text-xs gap-1 news-feed-item-btn"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'stretch',
                  justifyContent: 'flex-start',
                  textAlign: 'left',
                  height: 'auto',
                  minHeight: '0',
                  padding: '12px',
                  borderRadius: '8px',
                  background: 'rgba(15, 20, 32, 0.6)',
                  border: '1px solid rgba(31, 41, 61, 0.6)',
                  color: 'inherit',
                  cursor: 'pointer',
                  boxSizing: 'border-box',
                  position: 'relative',
                }}
                onClick={() => onSelectRelated(ra.article_id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onSelectRelated(ra.article_id)
                  }
                }}
              >
                <strong className="text-xs font-bold text-slate-200 line-clamp-2 leading-snug">
                  {ra.headline || ra.title || 'Không có tiêu đề'}
                </strong>
                <span className="text-[9px] text-slate-500 font-mono mt-1">
                  {ra.source} · {formatNewsDate(ra.published_at)}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </article>
  )
}
