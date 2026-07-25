import { useCallback, useEffect, useRef, useState } from 'react'

import {
  findCourseById,
  findLessonIndex,
  getAllLessons,
  isYouTubeUrl,
  toYouTubeEmbed,
} from '../content/courseCatalogData'
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
  const [completedSet, setCompletedSet] = useState(() => new Set(readProgress()[courseId] || []))
  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [videoError, setVideoError] = useState(false)
  const videoRef = useRef(null)

  const activeLesson = allLessons.find((l) => l.lesson_id === activeLessonId) || allLessons[0]
  const activeIndex = findLessonIndex(course, activeLessonId)
  const isYouTube = isYouTubeUrl(activeLesson?.video_url)
  const youtubeEmbed = toYouTubeEmbed(activeLesson?.video_url)

  useEffect(() => {
    setVideoError(false)
    if (!isYouTube && videoRef.current) {
      videoRef.current.load()
      videoRef.current.play().catch(() => {})
    }
  }, [activeLessonId, isYouTube])

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
    if (activeIndex + 1 < allLessons.length) {
      setActiveLessonId(allLessons[activeIndex + 1].lesson_id)
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
        <button type="button" className="lhp-back" onClick={onBack}>← Quay lại</button>
        <h1 className="lhp-header__title">{course.title}</h1>
        <button type="button" className="lhp-sidebar-toggle" onClick={() => setSidebarOpen((v) => !v)}>
          Mục lục
        </button>
      </header>

      <div className={`lhp-workspace ${sidebarOpen ? '' : 'lhp-workspace--no-sidebar'}`}>
        <div className="lhp-main">
          <div className="lhp-player-wrap">
            {isYouTube && youtubeEmbed ? (
              <iframe
                key={activeLessonId}
                className="lhp-player lhp-player--youtube"
                src={youtubeEmbed}
                title={activeLesson?.title || course.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerPolicy="strict-origin-when-cross-origin"
                allowFullScreen
              />
            ) : videoError ? (
              <div className="lhp-player lhp-player--placeholder">
                <p>Không phát được video trong app</p>
                {activeLesson?.video_url ? (
                  <a className="lhc-btn lhc-btn--primary" href={activeLesson.video_url} target="_blank" rel="noreferrer">
                    Mở trên YouTube
                  </a>
                ) : null}
              </div>
            ) : (
              <video
                ref={videoRef}
                className="lhp-player"
                controls
                src={activeLesson?.video_url || ''}
                onEnded={handleVideoEnded}
                onError={() => setVideoError(true)}
              />
            )}
          </div>

          <div className="lhp-lesson-info">
            <span className="lhp-lesson-info__num">Bài {activeIndex + 1}/{allLessons.length}</span>
            <h2 className="lhp-lesson-info__title">{activeLesson?.title}</h2>
            <div className="lhp-lesson-info__actions">
              {isYouTube && activeLesson?.video_url ? (
                <a className="lhc-btn lhc-btn--outline" href={activeLesson.video_url} target="_blank" rel="noreferrer">
                  Mở YouTube
                </a>
              ) : null}
              {!completedSet.has(activeLessonId) ? (
                <button type="button" className="lhc-btn lhc-btn--outline" onClick={() => markComplete(activeLessonId)}>
                  Đánh dấu hoàn thành
                </button>
              ) : (
                <span className="lhp-lesson-done-badge">✓ Đã hoàn thành</span>
              )}
              {activeIndex + 1 < allLessons.length ? (
                <button
                  type="button"
                  className="lhc-btn lhc-btn--primary"
                  onClick={() => setActiveLessonId(allLessons[activeIndex + 1].lesson_id)}
                >
                  Bài tiếp theo →
                </button>
              ) : null}
            </div>
          </div>

          <div className="lhp-tabs" role="tablist">
            {[['overview', 'Tổng quan'], ['notes', 'Ghi chú'], ['resources', 'Tài liệu']].map(([id, label]) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={activeTab === id}
                className={activeTab === id ? 'is-active' : ''}
                onClick={() => setActiveTab(id)}
              >
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
                  <span>Thời lượng: <strong>{course.total_duration}</strong></span>
                </div>
                <h3>Tiến độ</h3>
                <div className="lhp-overview__progress">
                  <div className="lhc-card__progress-bar lhp-overview__bar">
                    <div
                      className="lhc-card__progress-fill"
                      style={{ width: `${allLessons.length ? (completedSet.size / allLessons.length * 100) : 0}%` }}
                    />
                  </div>
                  <span>{completedSet.size}/{allLessons.length} bài đã hoàn thành</span>
                </div>
              </div>
            ) : null}
            {activeTab === 'notes' ? (
              <p className="lhp-notes__placeholder">Ghi chú bài học đang phát triển.</p>
            ) : null}
            {activeTab === 'resources' ? (
              activeLesson?.video_url ? (
                <p>Nguồn: <a href={activeLesson.video_url} target="_blank" rel="noreferrer">{activeLesson.video_url}</a></p>
              ) : (
                <p className="lhp-notes__placeholder">Chưa có tài liệu đính kèm.</p>
              )
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
