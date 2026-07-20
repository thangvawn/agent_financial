import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

export default function NewsHeader({
  topBrief,
  onSelectTopBrief,
  onRefresh,
  loading,
  freshness,
  sourceCount,
  successfulSourceCount,
}) {
  return (
    <header className="flex flex-col gap-4 border-b border-[#1f293d] pb-6 mb-6">
      {/* Title + Metadata Actions Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-[10px] text-teal-400 font-bold uppercase tracking-wider font-mono">
            NORTHSTAR / NEWS INTEL DESK
          </p>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
            News &amp; Intelligence
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-medium leading-relaxed">
            Phân tích tin tức vĩ mô và doanh nghiệp cùng hệ thống kênh truyền dẫn tác động chéo.
          </p>
        </div>

        {/* Desk status & Actions */}
        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="text-[10px] font-mono text-slate-500 bg-[#161b26] border border-[#1f293d] px-2 py-1 rounded flex items-center gap-2">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
            </span>
            <span>
              SOURCES: {successfulSourceCount}/{sourceCount} ({freshness})
            </span>
          </div>

          <button
            type="button"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0d9488] hover:bg-[#0f766e] text-white font-bold text-xs rounded transition-all cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={onRefresh}
            disabled={loading}
          >
            {loading ? (
              <>
                <svg className="animate-spin h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Đang tải</span>
              </>
            ) : (
              <span>Cập nhật tin</span>
            )}
          </button>
        </div>
      </div>

      {/* Highlights / Rolling ticker */}
      {topBrief && (
        <div className="bg-[#10b981]/5 border border-[#10b981]/20 rounded-md p-3 flex items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="px-2 py-0.5 bg-[#10b981]/15 text-[#10b981] font-bold rounded-[3px] text-[10px] tracking-wide shrink-0">
              NỔI BẬT
            </span>
            <strong className="text-slate-200 font-bold truncate block">
              {topBrief.headline}
            </strong>
          </div>
          <button
            type="button"
            className="text-[#10b981] hover:text-[#059669] font-bold text-[11px] shrink-0 font-mono transition-colors cursor-pointer border-none bg-transparent shadow-none min-h-0 h-auto p-0"
            onClick={onSelectTopBrief}
          >
            ĐỌC PHÂN TÍCH ↗
          </button>
        </div>
      )}
    </header>
  )
}
