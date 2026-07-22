import { PlayIcon } from '../../../shared/Icons'

const DIFFICULTY_COLORS = {
  'Cơ bản': 'var(--pos)',
  'Trung bình': 'var(--warn)',
  'Nâng cao': 'var(--neg)',
}

export default function CourseCard({ course, progress, onClick }) {
  const pct = progress?.pct ?? 0
  const started = pct > 0

  return (
    <article className="lhc-card" onClick={() => onClick(course.course_id)} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') onClick(course.course_id) }}>
      <div className="lhc-card__thumb" style={!course.thumbnail_image ? { background: course.thumbnail_gradient } : undefined}>
        {course.thumbnail_image ? (
          <img src={course.thumbnail_image} alt={course.title} className="lhc-card__img" loading="lazy" />
        ) : null}
        <span className="lhc-card__play-overlay" aria-hidden="true"><PlayIcon size={28} /></span>
        <span className="lhc-card__difficulty" style={{ '--diff-color': DIFFICULTY_COLORS[course.difficulty] || 'var(--accent)' }}>
          {course.difficulty}
        </span>
      </div>
      <div className="lhc-card__body">
        <p className="lhc-card__instructor">{course.instructor}</p>
        <h3 className="lhc-card__title">{course.title}</h3>
        <p className="lhc-card__meta">
          {course.lesson_count} bài · {course.total_duration}
        </p>
        {started ? (
          <div className="lhc-card__progress">
            <div className="lhc-card__progress-bar">
              <div className="lhc-card__progress-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="lhc-card__progress-label">{Math.round(pct)}% hoàn thành</span>
          </div>
        ) : (
          <p className="lhc-card__desc">{course.description}</p>
        )}
      </div>
    </article>
  )
}
