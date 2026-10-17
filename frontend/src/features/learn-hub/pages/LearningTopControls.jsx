import { useEffect, useState } from 'react'
import {
  BookOpen,
  CheckSquare,
  ChevronDown,
  FileText,
  Maximize2,
  Minimize2,
  Pin,
  Search,
  Sparkles,
  X,
} from 'lucide-react'

const LEARN_SUBTABS = [
  { id: 'courses', label: 'Khóa học', icon: BookOpen },
  { id: 'docs', label: 'Sách & Tài liệu', icon: FileText },
  { id: 'quanta_docs', label: 'Quanta Docs', icon: Sparkles },
  { id: 'ai_tutor', label: 'Hỏi AI Tutor', icon: Pin },
  { id: 'mock_exam', label: 'CFA Mock', icon: CheckSquare },
]

const LEVEL_OPTIONS = [
  { id: 'all', label: 'Tất cả trình độ' },
  { id: 'Cơ bản', label: 'Cơ bản' },
  { id: 'Trung bình', label: 'Trung bình' },
  { id: 'Nâng cao', label: 'Nâng cao' },
]

export default function LearningTopControls({
  activeSubTab,
  onSubTabChange,
  search,
  onSearchChange,
  difficulty,
  onDifficultyChange,
}) {
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    function handleFsChange() {
      setIsFullscreen(Boolean(document.fullscreenElement))
    }
    document.addEventListener('fullscreenchange', handleFsChange)
    return () => document.removeEventListener('fullscreenchange', handleFsChange)
  }, [])

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }

  return (
    <div className="lh-top-bar" role="toolbar" aria-label="Learn Hub toolbar">
      {/* Navigation Sub-Tab Pills */}
      <div className="lh-subtabs" role="tablist" aria-label="Learn Hub Sub Tabs">
        {LEARN_SUBTABS.map((tab) => {
          const Icon = tab.icon
          const isActive = activeSubTab === tab.id
          return (
            <button
              key={tab.id}
              id={`lh-tab-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`lh-panel-${tab.id}`}
              className={`lh-subtab-pill ${isActive ? 'is-active' : ''}`}
              onClick={() => onSubTabChange(tab.id)}
            >
              <Icon size={16} className="lh-subtab-icon" />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Right Controls: Search & Level Filter & Fullscreen Toggle */}
      <div className="lh-top-actions">
        <div className="lh-search-box">
          <Search size={15} className="lh-search-icon" aria-hidden="true" />
          <input
            type="text"
            id="lh-search-input"
            aria-label="Tìm khóa học, chủ đề, giảng viên"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Tìm khóa học, chủ đề, giảng viên..."
            className="lh-search-input"
          />
          {search ? (
            <button
              type="button"
              className="lh-search-clear"
              aria-label="Xóa tìm kiếm"
              onClick={() => onSearchChange('')}
            >
              <X size={13} />
            </button>
          ) : null}
        </div>

        <div className="lh-filter-dropdown-wrap">
          <select
            id="lh-level-select"
            aria-label="Lọc theo trình độ"
            value={difficulty}
            onChange={(e) => onDifficultyChange(e.target.value)}
            className="lh-filter-select"
          >
            {LEVEL_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown size={14} className="lh-select-chevron" aria-hidden="true" />
        </div>

        <button
          type="button"
          className={`lh-fullscreen-btn ${isFullscreen ? 'is-active' : ''}`}
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Thu nhỏ cửa sổ' : 'Toàn màn hình (Full Screen)'}
          aria-label={isFullscreen ? 'Thu nhỏ cửa sổ' : 'Toàn màn hình (Full Screen)'}
        >
          {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          <span className="lh-fullscreen-btn__text">
            {isFullscreen ? 'Thu nhỏ' : 'Toàn màn hình'}
          </span>
        </button>
      </div>
    </div>
  )
}
