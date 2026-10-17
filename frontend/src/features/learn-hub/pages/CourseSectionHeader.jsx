import { useState, useRef, useEffect } from 'react'
import { ArrowRight, ChevronDown } from 'lucide-react'

const SORT_OPTIONS = [
  { id: 'latest', label: 'Mới nhất' },
  { id: 'duration', label: 'Thời lượng' },
  { id: 'lessons', label: 'Số bài học' },
  { id: 'bookmarked', label: 'Đã lưu' },
]

export default function CourseSectionHeader({
  count = 0,
  sortBy = 'latest',
  onSortChange,
}) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  const activeLabel = SORT_OPTIONS.find((s) => s.id === sortBy)?.label || 'Mới nhất'

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  return (
    <div className="lh-courses-header">
      <div className="lh-courses-header__left">
        <h2 id="lh-courses-title" className="lh-courses-header__title">
          Khóa học
        </h2>
        <span className="lh-courses-header__badge">{count}</span>
      </div>

      <div className="lh-courses-header__right" ref={menuRef}>
        <button
          type="button"
          className="lh-sort-trigger"
          aria-expanded={open}
          aria-haspopup="listbox"
          onClick={() => setOpen((prev) => !prev)}
        >
          <span>Xem: <strong>{activeLabel}</strong></span>
          <ArrowRight size={14} className="lh-sort-arrow" />
        </button>

        {open ? (
          <ul className="lh-sort-dropdown" role="listbox">
            {SORT_OPTIONS.map((opt) => (
              <li
                key={opt.id}
                role="option"
                aria-selected={sortBy === opt.id}
                className={`lh-sort-item ${sortBy === opt.id ? 'is-active' : ''}`}
                onClick={() => {
                  onSortChange(opt.id)
                  setOpen(false)
                }}
              >
                {opt.label}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  )
}
