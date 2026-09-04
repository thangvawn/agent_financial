import { useEffect, useRef, useState } from 'react'

import {
  findCourseById,
  findLessonIndex,
  getAllLessons,
  isYouTubeUrl,
  toYouTubeEmbed,
} from '../content/courseCatalogData'
import LessonSidebar from './LessonSidebar'
import LearnTutorPanel from './LearnTutorPanel'

const STORAGE_KEY = 'northstar.learn-hub.progress'

function readProgress() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') } catch { return {} }
}

function writeProgress(data) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)) } catch { /* noop */ }
}

const PLAYER_TABS = [
  ['overview', 'Tổng quan'],
  ['tutor', '🎓 AI Gia Sư'],
  ['notes', 'Ghi chú'],
  ['resources', 'Tài liệu'],
]

export default function CoursePlayerPage({ courseId, sessionId, onBack }) {
  const course = findCourseById(courseId)
  const allLessons = course ? getAllLessons(course) : []
  const [activeLessonId, setActiveLessonId] = useState(() => allLessons[0]?.lesson_id || '')
  const [completedSet, setCompletedSet] = useState(() => new Set(readProgress()[courseId] || []))
  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [videoErrorLesson, setVideoErrorLesson] = useState(null)
  const videoRef = useRef(null)

  const handleTabKeyDown = (e, currentId) => {
    const tabIds = PLAYER_TABS.map(([id]) => id)
    const idx = tabIds.indexOf(currentId)
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      const nextId = tabIds[(idx + 1) % tabIds.length]
      setActiveTab(nextId)
      document.getElementById(`lhp-tab-${nextId}`)?.focus()
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      const prevId = tabIds[(idx - 1 + tabIds.length) % tabIds.length]
      setActiveTab(prevId)
      document.getElementById(`lhp-tab-${prevId}`)?.focus()
    } else if (e.key === 'Home') {
      e.preventDefault()
      setActiveTab(tabIds[0])
      document.getElementById(`lhp-tab-${tabIds[0]}`)?.focus()
    } else if (e.key === 'End') {
      e.preventDefault()
      setActiveTab(tabIds[tabIds.length - 1])
      document.getElementById(`lhp-tab-${tabIds[tabIds.length - 1]}`)?.focus()
    }
  }

  const videoError = videoErrorLesson === activeLessonId
  const activeLesson = allLessons.find((l) => l.lesson_id === activeLessonId) || allLessons[0]
  const activeIndex = findLessonIndex(course, activeLessonId)
  const isYouTube = isYouTubeUrl(activeLesson?.video_url)
  const youtubeEmbed = toYouTubeEmbed(activeLesson?.video_url)

  useEffect(() => {
    if (!isYouTube && videoRef.current) {
      videoRef.current.load()
      videoRef.current.play().catch(() => {})
    }
  }, [activeLessonId, isYouTube])

  const markComplete = (lessonId) => {
    setCompletedSet((prev) => {
      const next = new Set(prev)
      next.add(lessonId)
      const saved = readProgress()
      saved[courseId] = [...next]
      writeProgress(saved)
      return next
    })
  }

  const handleVideoEnded = () => {
    markComplete(activeLessonId)
    if (activeIndex + 1 < allLessons.length) {
      setActiveLessonId(allLessons[activeIndex + 1].lesson_id)
    }
  }

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
                onError={() => setVideoErrorLesson(activeLessonId)}
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

          <div className="lhp-tabs" role="tablist" aria-label="Nội dung bài học">
            {PLAYER_TABS.map(([id, label]) => (
              <button
                key={id}
                id={`lhp-tab-${id}`}
                type="button"
                role="tab"
                aria-selected={activeTab === id}
                aria-controls={`lhp-panel-${id}`}
                tabIndex={activeTab === id ? 0 : -1}
                className={activeTab === id ? 'is-active' : ''}
                onClick={() => setActiveTab(id)}
                onKeyDown={(e) => handleTabKeyDown(e, id)}
              >
                {label}
              </button>
            ))}
          </div>

          <div
            id={`lhp-panel-${activeTab}`}
            className="lhp-tab-content"
            role="tabpanel"
            aria-labelledby={`lhp-tab-${activeTab}`}
          >
            {activeTab === 'tutor' ? (
              <LearnTutorPanel courseId={courseId} lessonId={activeLessonId} sessionId={sessionId} />
            ) : null}
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
