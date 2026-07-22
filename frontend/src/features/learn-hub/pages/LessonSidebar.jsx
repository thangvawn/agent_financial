import { useState } from 'react'

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function ChevronIcon({ open }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ transition: 'transform 180ms ease', transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }}>
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}

export default function LessonSidebar({ course, activeLessonId, completedSet, onSelectLesson, onClose }) {
  const [collapsedSections, setCollapsedSections] = useState(new Set())

  if (!course) return null

  function toggleSection(sectionId) {
    setCollapsedSections((prev) => {
      const next = new Set(prev)
      if (next.has(sectionId)) next.delete(sectionId)
      else next.add(sectionId)
      return next
    })
  }

  let globalIndex = 0

  return (
    <aside className="lhs-sidebar" aria-label="Danh sách bài học">
      <div className="lhs-sidebar__header">
        <h2 className="lhs-sidebar__course-title">{course.title}</h2>
        {onClose ? (
          <button type="button" className="lhs-sidebar__close" onClick={onClose} aria-label="Đóng sidebar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        ) : null}
      </div>
      <div className="lhs-sidebar__sections">
        {course.sections.map((section) => {
          const isCollapsed = collapsedSections.has(section.section_id)
          const sectionCompleted = section.lessons.every((l) => completedSet.has(l.lesson_id))
          const sectionStartIndex = globalIndex

          return (
            <div key={section.section_id} className="lhs-section">
              <button
                type="button"
                className={`lhs-section__head ${sectionCompleted ? 'lhs-section__head--done' : ''}`}
                onClick={() => toggleSection(section.section_id)}
                aria-expanded={!isCollapsed}
              >
                <ChevronIcon open={!isCollapsed} />
                <span className="lhs-section__title">{section.title}</span>
                <span className="lhs-section__count">{section.lessons.length} bài</span>
              </button>
              {!isCollapsed ? (
                <ul className="lhs-section__lessons">
                  {section.lessons.map((lesson) => {
                    globalIndex += 1
                    const idx = globalIndex
                    const isActive = lesson.lesson_id === activeLessonId
                    const isDone = completedSet.has(lesson.lesson_id)

                    return (
                      <li key={lesson.lesson_id}>
                        <button
                          type="button"
                          className={`lhs-lesson ${isActive ? 'lhs-lesson--active' : ''} ${isDone ? 'lhs-lesson--done' : ''}`}
                          onClick={() => onSelectLesson(lesson.lesson_id)}
                        >
                          <span className="lhs-lesson__index">
                            {isDone ? <CheckIcon /> : <span>{sectionStartIndex + (idx - sectionStartIndex)}</span>}
                          </span>
                          <span className="lhs-lesson__info">
                            <span className="lhs-lesson__title">{lesson.title}</span>
                            <span className="lhs-lesson__dur">{lesson.duration}</span>
                          </span>
                          {isActive ? <span className="lhs-lesson__playing" aria-label="Đang phát">▶</span> : null}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              ) : null}
            </div>
          )
        })}
      </div>
    </aside>
  )
}
