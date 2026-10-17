import { BookOpen, Bookmark, Play } from 'lucide-react'

export default function CourseCard({
  course,
  progress,
  onClick,
  isBookmarked = false,
  onToggleBookmark,
}) {
  const pct = progress?.pct ?? 0
  const started = pct > 0

  const getDifficultyClass = (diff) => {
    if (diff === 'Cơ bản') return 'lhc-card__difficulty-badge--basic'
    if (diff === 'Trung bình') return 'lhc-card__difficulty-badge--intermediate'
    if (diff === 'Nâng cao') return 'lhc-card__difficulty-badge--advanced'
    return ''
  }

  const categoryGradient =
    course.thumbnail_gradient ||
    {
      finance: 'linear-gradient(135deg, #064e3b 0%, #022c22 100%)',
      investing: 'linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%)',
      analysis: 'linear-gradient(135deg, #4c1d95 0%, #1e1b4b 100%)',
      tools: 'linear-gradient(135deg, #831843 0%, #18181b 100%)',
    }[course.category] ||
    'linear-gradient(135deg, #18181b 0%, #09090b 100%)'

  return (
    <article
      className="lhc-card"
      onClick={() => onClick(course.course_id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onClick(course.course_id)
      }}
    >
      <div
        className="lhc-card__thumb"
        style={{ background: categoryGradient }}
      >
        {course.thumbnail_image ? (
          <img
            src={course.thumbnail_image}
            alt={course.title}
            className="lhc-card__img"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        ) : null}

        {/* Hover play button center reveal */}
        <div className="lhc-card__hover-play" aria-hidden="true">
          <div className="lhc-card__hover-play-circle">
            <Play size={18} fill="currentColor" />
          </div>
        </div>

        {/* Bottom-left duration badge */}
        <div className="lhc-card__duration-badge">
          <span className="lhc-card__duration-icon" aria-hidden="true">▶</span>
          <span>{course.total_duration}</span>
        </div>

        {/* Top-right difficulty badge */}
        <span className={`lhc-card__difficulty-badge ${getDifficultyClass(course.difficulty)}`}>
          {course.difficulty}
        </span>
      </div>

      <div className="lhc-card__body">
        <p className="lhc-card__instructor" title={course.instructor}>
          {course.instructor}
        </p>
        <h3 className="lhc-card__title" title={course.title}>
          {course.title}
        </h3>
        <p className="lhc-card__desc">{course.description}</p>

        {started ? (
          <div className="lhc-card__progress">
            <div className="lhc-card__progress-bar">
              <div className="lhc-card__progress-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="lhc-card__progress-label">{Math.round(pct)}% hoàn thành</span>
          </div>
        ) : null}
      </div>

      <div className="lhc-card__footer">
        <div className="lhc-card__footer-left">
          <BookOpen size={14} className="lhc-card__footer-icon" aria-hidden="true" />
          <span>{course.lesson_count} bài học</span>
        </div>

        <button
          type="button"
          className={`lhc-card__bookmark-btn ${isBookmarked ? 'is-bookmarked' : ''}`}
          aria-label={isBookmarked ? 'Bỏ lưu khóa học' : 'Lưu khóa học'}
          title={isBookmarked ? 'Đã lưu' : 'Lưu vào danh sách'}
          onClick={(e) => {
            e.stopPropagation()
            onToggleBookmark?.(course.course_id)
          }}
        >
          <Bookmark size={16} fill={isBookmarked ? 'currentColor' : 'none'} />
        </button>
      </div>
    </article>
  )
}
