import { useEffect, useRef, useState } from 'react'

import {
  findCourseById,
  findLessonIndex,
  getAllLessons,
  isYouTubeUrl,
  toYouTubeEmbed,
} from '../content/courseCatalogData'
import CoursePlayerTabContent from './CoursePlayerTabContent'
import CourseVideoPlayer from './CourseVideoPlayer'
import LessonSidebar from './LessonSidebar'

function progressKey(sessionId) {
  return `northstar.learn-hub.progress:${sessionId || 'anonymous'}`
}
function readProgress(sessionId) {
  try { return JSON.parse(localStorage.getItem(progressKey(sessionId)) || '{}') } catch { return {} }
}
function writeProgress(sessionId, data) {
  try { localStorage.setItem(progressKey(sessionId), JSON.stringify(data)) } catch { /* noop */ }
}

const PLAYER_TABS = [
  ['overview', 'Tổng quan'],
  ['video-agent', '🤖 Video Agent'],
  ['checkpoint', '🎯 Mốc kiểm tra'],
  ['tutor', '🎓 AI Gia Sư'],
  ['notes', 'Ghi chú'],
  ['resources', 'Tài liệu'],
]

export default function CoursePlayerPage({ courseId, course: initialCourse, sessionId, onBack }) {
  const course = initialCourse || findCourseById(courseId)
  const allLessons = course ? getAllLessons(course) : []
  const [activeLessonId, setActiveLessonId] = useState(() => allLessons[0]?.lesson_id || '')
  const [completedSet, setCompletedSet] = useState(() => new Set(readProgress(sessionId)[courseId] || []))
  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [videoErrorLesson, setVideoErrorLesson] = useState(null)
  const [currentTimeSeconds, setCurrentTimeSeconds] = useState(0)

  const selectLesson = (lessonId) => {
    setCurrentTimeSeconds(0)
    setActiveLessonId(lessonId)
  }
  const videoRef = useRef(null)

  const handleTabKeyDown = (e, currentId) => {
    const tabIds = PLAYER_TABS.map(([id]) => id)
    const idx = tabIds.indexOf(currentId)
    const delta = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    if (delta !== 0) {
      e.preventDefault()
      const nextId = tabIds[(idx + delta + tabIds.length) % tabIds.length]
      setActiveTab(nextId)
      document.getElementById(`lhp-tab-${nextId}`)?.focus()
    }
  }

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
      const saved = readProgress(sessionId)
      saved[courseId] = [...next]
      writeProgress(sessionId, saved)
      return next
    })
  }

  const handleVideoEnded = () => {
    markComplete(activeLessonId)
    if (activeIndex + 1 < allLessons.length) {
      selectLesson(allLessons[activeIndex + 1].lesson_id)
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
        <button type="button" className="lhp-sidebar-toggle" onClick={() => setSidebarOpen((v) => !v)}>Mục lục</button>
      </header>

      <div className={`lhp-workspace ${sidebarOpen ? '' : 'lhp-workspace--no-sidebar'}`}>
        <div className="lhp-main">
          <CourseVideoPlayer
            activeLessonId={activeLessonId}
            activeLesson={activeLesson}
            courseTitle={course.title}
            isYouTube={isYouTube}
            youtubeEmbed={youtubeEmbed}
            videoError={videoErrorLesson === activeLessonId}
            videoRef={videoRef}
            onVideoEnded={handleVideoEnded}
            onVideoError={() => setVideoErrorLesson(activeLessonId)}
            onTimeUpdate={(event) => setCurrentTimeSeconds(event.currentTarget.currentTime)}
          />

          <div className="lhp-lesson-info">
            <span className="lhp-lesson-info__num">Bài {activeIndex + 1}/{allLessons.length}</span>
            <h2 className="lhp-lesson-info__title">{activeLesson?.title}</h2>
            <div className="lhp-lesson-info__actions">
              {isYouTube && activeLesson?.video_url ? (
                <a className="lhc-btn lhc-btn--outline" href={activeLesson.video_url} target="_blank" rel="noreferrer">Mở YouTube</a>
              ) : null}
              {!completedSet.has(activeLessonId) ? (
                <button type="button" className="lhc-btn lhc-btn--outline" onClick={() => markComplete(activeLessonId)}>Đánh dấu hoàn thành</button>
              ) : (
                <span className="lhp-lesson-done-badge">✓ Đã hoàn thành</span>
              )}
              {activeIndex + 1 < allLessons.length ? (
                <button type="button" className="lhc-btn lhc-btn--primary" onClick={() => selectLesson(allLessons[activeIndex + 1].lesson_id)}>
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

          <CoursePlayerTabContent
            activeTab={activeTab}
            course={course}
            courseId={courseId}
            activeLesson={activeLesson}
            activeLessonId={activeLessonId}
            sessionId={sessionId}
            completedSet={completedSet}
            allLessons={allLessons}
            onCompleteCheckpoint={(id) => markComplete(id)}
            currentTimeSeconds={currentTimeSeconds}
          />
        </div>

        {sidebarOpen ? (
          <LessonSidebar
            course={course}
            activeLessonId={activeLessonId}
            completedSet={completedSet}
            onSelectLesson={selectLesson}
            onClose={() => setSidebarOpen(false)}
          />
        ) : null}
      </div>
    </section>
  )
}
