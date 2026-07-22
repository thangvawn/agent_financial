import { useCallback, useEffect, useRef, useState } from 'react'

import { findCourseById, getAllLessons, findLessonIndex } from '../content/courseCatalogData'
import LessonSidebar from './LessonSidebar'

const STORAGE_KEY = 'northstar.learn-hub.progress'

function readProgress() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') } catch { return {} }
}

function writeProgress(data) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)) } catch { /* noop */ }
}

export default function CoursePlayerPage({ courseId, onBack }) {
  const course = findCourseById(courseId)
  const allLessons = course ? getAllLessons(course) : []
  const [activeLessonId, setActiveLessonId] = useState(() => allLessons[0]?.lesson_id || '')
  const [completedSet, setCompletedSet] = useState(() => {
    const saved = readProgress()
    return new Set(saved[courseId] || [])
  })
  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const videoRef = useRef(null)

  const activeLesson = allLessons.find((l) => l.lesson_id === activeLessonId) || allLessons[0]
  const activeIndex = findLessonIndex(course, activeLessonId)

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load()
      videoRef.current.play().catch(() => { /* autoplay blocked */ })
    }
  }, [activeLessonId])

  const markComplete = useCallback((lessonId) => {
    setCompletedSet((prev) => {
      const next = new Set(prev)
      next.add(lessonId)
      const saved = readProgress()
      saved[courseId] = [...next]
      writeProgress(saved)
      return next
    })
  }, [courseId])

  const handleVideoEnded = useCallback(() => {
    markComplete(activeLessonId)
    const nextIndex = activeIndex + 1
    if (nextIndex < allLessons.length) {
      setActiveLessonId(allLessons[nextIndex].lesson_id)
    }
  }, [activeLessonId, activeIndex, allLessons, markComplete])

  if (!course) {
    return (
      <section className="lh-shell lh-shell--center">
        <div className="lh-empty-card">
          <h1>Không tìm thấy khóa học</h1>
          <button type="button" className="lhc-btn lhc-btn--primary" onClick={onBack}>Quay lại</button>
        </div>
      </section>
    )
  }

  return (
    <section className="lhp-shell" data-domain="learn_hub">
      <header className="lhp-header">
        <button type="button" className="lhp-back" onClick={onBack}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
          Quay lại
        </button>
        <h1 className="lhp-header__title">{course.title}</h1>
        <button type="button" className="lhp-sidebar-toggle" onClick={() => setSidebarOpen((v) => !v)} aria-label={sidebarOpen ? 'Ẩn sidebar' : 'Hiện sidebar'}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" /><line x1="9" y1="3" x2="9" y2="21" /></svg>
        </button>
      </header>

      <div className={`lhp-workspace ${sidebarOpen ? '' : 'lhp-workspace--no-sidebar'}`}>
        <div className="lhp-main">
          <div className="lhp-player-wrap">
            <video
              ref={videoRef}
              className="lhp-player"
              controls
              src={activeLesson?.video_url || ''}
              onEnded={handleVideoEnded}
            >
              Trình duyệt không hỗ trợ video.
            </video>
          </div>

          <div className="lhp-lesson-info">
            <span className="lhp-lesson-info__num">Bài {activeIndex + 1}/{allLessons.length}</span>
            <h2 className="lhp-lesson-info__title">{activeLesson?.title}</h2>
            <div className="lhp-lesson-info__actions">
              {!completedSet.has(activeLessonId) ? (
                <button type="button" className="lhc-btn lhc-btn--outline" onClick={() => markComplete(activeLessonId)}>
                  Đánh dấu hoàn thành
                </button>
              ) : (
                <span className="lhp-lesson-done-badge">✓ Đã hoàn thành</span>
              )}
              {activeIndex + 1 < allLessons.length ? (
                <button type="button" className="lhc-btn lhc-btn--primary" onClick={() => setActiveLessonId(allLessons[activeIndex + 1].lesson_id)}>
                  Bài tiếp theo →
                </button>
              ) : null}
            </div>
          </div>

          <div className="lhp-tabs" role="tablist">
            {[['overview', 'Tổng quan'], ['notes', 'Ghi chú'], ['resources', 'Tài liệu']].map(([id, label]) => (
              <button key={id} type="button" role="tab" aria-selected={activeTab === id} className={activeTab === id ? 'is-active' : ''} onClick={() => setActiveTab(id)}>
                {label}
              </button>
            ))}
          </div>

          <div className="lhp-tab-content">
            {activeTab === 'overview' ? (
              <div className="lhp-overview">
                <h3>Về khóa học</h3>
                <p>{course.description}</p>
                <div className="lhp-overview__meta">
                  <span>Giảng viên: <strong>{course.instructor}</strong></span>
                  <span>Độ khó: <strong>{course.difficulty}</strong></span>
                  <span>Tổng thời lượng: <strong>{course.total_duration}</strong></span>
                  <span>Số bài: <strong>{course.lesson_count}</strong></span>
                </div>
                <h3>Tiến độ</h3>
                <div className="lhp-overview__progress">
                  <div className="lhc-card__progress-bar lhp-overview__bar">
                    <div className="lhc-card__progress-fill" style={{ width: `${allLessons.length ? (completedSet.size / allLessons.length * 100) : 0}%` }} />
                  </div>
                  <span>{completedSet.size}/{allLessons.length} bài đã hoàn thành</span>
                </div>
              </div>
            ) : null}
            {activeTab === 'notes' ? (
              <div className="lhp-notes">
                <p className="lhp-notes__placeholder">Ghi chú cho bài học sẽ xuất hiện ở đây. Tính năng đang phát triển.</p>
              </div>
            ) : null}
            {activeTab === 'resources' ? (
              <div className="lhp-resources">
                <p className="lhp-notes__placeholder">Tài liệu đính kèm cho khóa học sẽ hiển thị ở đây. Tính năng đang phát triển.</p>
              </div>
            ) : null}
          </div>
        </div>

        {sidebarOpen ? (
          <LessonSidebar
            course={course}
            activeLessonId={activeLessonId}
            completedSet={completedSet}
            onSelectLesson={setActiveLessonId}
            onClose={() => setSidebarOpen(false)}
          />
        ) : null}
      </div>
    </section>
  )
}
