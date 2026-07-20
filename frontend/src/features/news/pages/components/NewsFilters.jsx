import { useState } from 'react'

const TIME_RANGES = [
  { value: 24, label: '24 giờ qua' },
  { value: 72, label: '3 ngày qua' },
  { value: 168, label: '7 ngày qua' },
]

const SENTIMENTS = [
  { value: '', label: 'Tất cả sắc thái' },
  { value: 'positive', label: 'Tích cực' },
  { value: 'negative', label: 'Tiêu cực' },
  { value: 'neutral', label: 'Trung tính' },
]

const IMPACT_LEVELS = [
  { value: '', label: 'Mọi mức tác động' },
  { value: 'high', label: 'Tác động cao' },
  { value: 'medium', label: 'Trung bình' },
  { value: 'low', label: 'Tác động thấp' },
]

const IMPORTANCE_LABELS = [
  { value: '', label: 'Mọi độ quan trọng' },
  { value: 'critical', label: 'Khẩn cấp' },
  { value: 'high', label: 'Quan trọng' },
  { value: 'medium', label: 'Trung bình' },
  { value: 'low', label: 'Ít quan trọng' },
]

export default function NewsFilters({
  marketLens,
  onLensChange,
  query,
  onQueryChange,
  timeRangeHours,
  onTimeRangeHoursChange,
  sentiment,
  onSentimentChange,
  impactLevel,
  onImpactLevelChange,
  importance,
  onImportanceChange,
  onResetFilters,
}) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const hasActiveSubFilters = timeRangeHours !== 168 || sentiment || impactLevel || importance

  return (
    <section className="bg-[#161b26] border border-[#1f293d] rounded-md p-4 mb-6 flex flex-col gap-4">
      {/* Top Filter Row: Lens tab selectors + search + advanced toggle */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Market Lens tabs */}
        <div className="flex bg-[#0f1420] p-1 rounded border border-[#1f293d] w-fit" role="tablist">
          {[
            { id: 'vietnam', label: 'Thị trường VN' },
            { id: 'global', label: 'Vĩ mô toàn cầu' },
            { id: 'cross_impact', label: 'Tác động chéo' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={marketLens === tab.id}
              className={`px-3 py-1.5 text-xs font-bold rounded transition-all cursor-pointer ${
                marketLens === tab.id
                  ? 'bg-[#0d9488] text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              onClick={() => onLensChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search input + Advanced Button */}
        <div className="flex items-center gap-2 flex-1 lg:max-w-md">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="Tìm kiếm tin tức (ví dụ: Fed, tỉ giá, doanh thu)..."
              className="w-full bg-[#0f1420] border border-[#1f293d] focus:border-[#0d9488] text-xs text-white rounded px-3 py-2 outline-none font-medium placeholder-slate-500 transition-colors"
            />
            {query && (
              <button
                type="button"
                className="absolute right-2 top-2.5 text-slate-500 hover:text-slate-350 cursor-pointer"
                onClick={() => onQueryChange('')}
              >
                ×
              </button>
            )}
          </div>

          <button
            type="button"
            className={`px-3 py-2 text-xs font-bold rounded border cursor-pointer transition-all shrink-0 ${
              showAdvanced || hasActiveSubFilters
                ? 'bg-[#1f293d]/50 border-[#0d9488] text-[#2dd4bf]'
                : 'bg-transparent border-[#1f293d] text-slate-450 hover:bg-[#1f293d]/25'
            }`}
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            Bộ lọc {hasActiveSubFilters ? '•' : ''}
          </button>
        </div>
      </div>

      {/* Advanced Filters Expandable Panel */}
      {(showAdvanced || hasActiveSubFilters) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-[#1f293d]/45 animate-fadeIn">
          {/* Time range selection */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Thời gian</span>
            <select
              value={timeRangeHours}
              onChange={(e) => onTimeRangeHoursChange(Number(e.target.value))}
              className="bg-[#0f1420] border border-[#1f293d] text-xs text-slate-300 rounded px-2.5 py-1.5 cursor-pointer outline-none"
            >
              {TIME_RANGES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* Sentiment selection */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Sắc thái (AI)</span>
            <select
              value={sentiment}
              onChange={(e) => onSentimentChange(e.target.value)}
              className="bg-[#0f1420] border border-[#1f293d] text-xs text-slate-300 rounded px-2.5 py-1.5 cursor-pointer outline-none"
            >
              {SENTIMENTS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          {/* Impact level selection */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Mức tác động</span>
            <select
              value={impactLevel}
              onChange={(e) => onImpactLevelChange(e.target.value)}
              className="bg-[#0f1420] border border-[#1f293d] text-xs text-slate-300 rounded px-2.5 py-1.5 cursor-pointer outline-none"
            >
              {IMPACT_LEVELS.map((i) => (
                <option key={i.value} value={i.value}>{i.label}</option>
              ))}
            </select>
          </div>

          {/* Importance level selection */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Độ quan trọng</span>
            <select
              value={importance}
              onChange={(e) => onImportanceChange(e.target.value)}
              className="bg-[#0f1420] border border-[#1f293d] text-xs text-slate-300 rounded px-2.5 py-1.5 cursor-pointer outline-none"
            >
              {IMPORTANCE_LABELS.map((imp) => (
                <option key={imp.value} value={imp.value}>{imp.label}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Clear Filters Prompt */}
      {hasActiveSubFilters && (
        <div className="flex items-center justify-between text-xs bg-[#0f1420] px-3 py-2 rounded border border-[#1f293d]/50">
          <span className="text-slate-400">
            Đang áp dụng bộ lọc nâng cao.
          </span>
          <button
            type="button"
            className="text-teal-400 hover:text-teal-300 font-bold cursor-pointer"
            onClick={onResetFilters}
          >
            Đặt lại bộ lọc
          </button>
        </div>
      )}
    </section>
  )
}
