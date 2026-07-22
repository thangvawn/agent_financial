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

  const hasQuery = Boolean(query.trim())
  const hasActiveSubFilters = timeRangeHours !== 168 || sentiment || impactLevel || importance
  const hasActiveFilters = hasQuery || hasActiveSubFilters
  let activeFilterMessage = 'Đang áp dụng bộ lọc nâng cao.'
  if (hasQuery && hasActiveSubFilters) activeFilterMessage = 'Đang áp dụng tìm kiếm và bộ lọc nâng cao.'
  else if (hasQuery) activeFilterMessage = 'Đang áp dụng tìm kiếm.'

  return (
    <section className="news-filters" aria-label="Bộ lọc tin tức">
      <div className="news-filters__top">
        <div className="news-filters__lenses" role="group" aria-label="Góc nhìn thị trường">
          {[
            { id: 'vietnam', label: 'Thị trường VN' },
            { id: 'global', label: 'Vĩ mô toàn cầu' },
            { id: 'cross_impact', label: 'Tác động chéo' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              aria-pressed={marketLens === tab.id}
              className={marketLens === tab.id ? 'is-active' : ''}
              onClick={() => onLensChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="news-filters__search-row">
          <div className="news-filters__search">
            <input
              type="text"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="Tìm kiếm tin tức (ví dụ: Fed, tỉ giá, doanh thu)..."
              aria-label="Tìm kiếm tin tức"
            />
            {query && (
              <button
                type="button"
                className="news-filters__clear"
                aria-label="Xóa tìm kiếm"
                onClick={() => onQueryChange('')}
              >
                ×
              </button>
            )}
          </div>

          <button
            type="button"
            className={showAdvanced || hasActiveFilters ? 'news-filters__toggle is-active' : 'news-filters__toggle'}
            aria-expanded={showAdvanced || Boolean(hasActiveSubFilters)}
            aria-controls="news-advanced-filters"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            Bộ lọc {hasActiveFilters ? '•' : ''}
          </button>
        </div>
      </div>

      {(showAdvanced || hasActiveSubFilters) && (
        <div id="news-advanced-filters" className="news-filters__advanced animate-fadeIn">
          <label>
            <span>Thời gian</span>
            <select
              value={timeRangeHours}
              onChange={(e) => onTimeRangeHoursChange(Number(e.target.value))}
            >
              {TIME_RANGES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </label>

          <label>
            <span>Sắc thái (AI)</span>
            <select
              value={sentiment}
              onChange={(e) => onSentimentChange(e.target.value)}
            >
              {SENTIMENTS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </label>

          <label>
            <span>Mức tác động</span>
            <select
              value={impactLevel}
              onChange={(e) => onImpactLevelChange(e.target.value)}
            >
              {IMPACT_LEVELS.map((i) => (
                <option key={i.value} value={i.value}>{i.label}</option>
              ))}
            </select>
          </label>

          <label>
            <span>Độ quan trọng</span>
            <select
              value={importance}
              onChange={(e) => onImportanceChange(e.target.value)}
            >
              {IMPORTANCE_LABELS.map((imp) => (
                <option key={imp.value} value={imp.value}>{imp.label}</option>
              ))}
            </select>
          </label>
        </div>
      )}

      {hasActiveFilters && (
        <div className="news-filters__active-note">
          <span>{activeFilterMessage}</span>
          <button
            type="button"
            onClick={onResetFilters}
          >
            Đặt lại bộ lọc
          </button>
        </div>
      )}
    </section>
  )
}
