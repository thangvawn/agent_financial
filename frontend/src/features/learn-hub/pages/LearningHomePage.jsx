import { useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useLearningAssets, useLearningCatalog } from '..'
import { SearchIcon } from '../../../shared/Icons'
import { COURSE_CATEGORIES, DEMO_COURSES, filterCourses } from '../content/courseCatalogData'
import { BookReaderWorkspace } from './BookReaderWorkspace'
import { toReadableBook } from './bookSource'
import CourseCard from './CourseCard'
import BookGrid from './BookGrid'
import CoursePlayerPage from './CoursePlayerPage'
import {
  LocalBookGrid,
  LocalVideoGrid,
  VideoPreview,
  filterAssetsByType,
  filterLocal,
} from './LibraryMedia'
import './learn-hub.css'
import './learn-hub-catalog.css'

const PROGRESS_KEY = 'northstar.learn-hub.progress'

function readAllProgress() {
  try { return JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}') } catch { return {} }
}

function getCourseProgress(courseId, totalLessons) {
  const saved = readAllProgress()
  const done = (saved[courseId] || []).length
  if (!done) return null
  return { pct: totalLessons > 0 ? (done / totalLessons) * 100 : 0 }
}

export default function LearningHomePage({ sessionId, onBack }) {
  const queryClient = useQueryClient()
  const [category, setCategory] = useState('all')
  const [search, setSearch] = useState('')
  const [activeCourseId, setActiveCourseId] = useState(null)
  const [activeBook, setActiveBook] = useState(null)
  const [activeVideo, setActiveVideo] = useState(null)
  const [mediaTab, setMediaTab] = useState('video')

  const {
    videoItems: rawVideos,
    bookItems,
    isLoading: assetLoading,
    error: assetError,
  } = useLearningAssets(sessionId)

  const videoAssets = useMemo(() => filterAssetsByType(rawVideos, 'video'), [rawVideos])
  const bookAssets = bookItems || []

  const filteredCourses = useMemo(
    () => filterCourses(DEMO_COURSES, { category, search }),
    [category, search],
  )

  if (!sessionId) {
    return (
      <section className="lh-shell lh-shell--center">
        <div className="lh-empty-card">
          <h1>Cần đăng nhập</h1>
          <p>Learn Hub cần session để mở thư viện khóa học.</p>
          {onBack ? <button type="button" className="lhc-btn lhc-btn--primary" onClick={onBack}>Về trang chủ</button> : null}
        </div>
      </section>
    )
  }

  if (activeBook) {
    return (
      <BookReaderWorkspace
        book={toReadableBook(activeBook)}
        sessionId={sessionId}
        onClose={() => setActiveBook(null)}
      />
    )
  }

  if (activeCourseId) {
    return (
      <CoursePlayerPage
        courseId={activeCourseId}
        onBack={() => setActiveCourseId(null)}
      />
    )
  }

  return (
    <section className="lh-shell" data-domain="learn_hub">
      {/* Hero */}
      <header className="lh-hero">
        <div className="lh-hero__inner">
          <div className="lh-hero__text">
            <p className="lh-hero__kicker">Learn Hub</p>
            <h1 className="lh-hero__title">Thư viện khóa học</h1>
            <p className="lh-hero__subtitle">Học tài chính và đầu tư qua video — từ cơ bản đến nâng cao</p>
          </div>
          <div className="lh-hero__search">
            <SearchIcon className="lh-hero__search-icon" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm khóa học, chủ đề…"
              className="lh-hero__search-input"
            />
          </div>
        </div>
      </header>

      {/* Category chips */}
      <div className="lh-chips-bar">
        <div className="lh-chips" role="tablist" aria-label="Danh mục khóa học">
          {COURSE_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              role="tab"
              aria-selected={category === cat.id}
              className={`lh-chip ${category === cat.id ? 'lh-chip--active' : ''}`}
              onClick={() => setCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
          <button
            type="button"
            className="lh-chip lh-chip--refresh"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}
            title="Làm mới dữ liệu"
          >
            ↻ Làm mới
          </button>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="lh-body">
        {/* Course grid */}
        <section className="lh-section" aria-labelledby="lh-courses-title">
          <h2 id="lh-courses-title" className="lh-section__title">
            Khóa học{category !== 'all' ? ` — ${COURSE_CATEGORIES.find((c) => c.id === category)?.label}` : ''}
            <span className="lh-section__count">{filteredCourses.length}</span>
          </h2>
          {filteredCourses.length === 0 ? (
            <p className="lh-empty">Không tìm thấy khóa học phù hợp.</p>
          ) : (
            <div className="lhc-grid">
              {filteredCourses.map((course) => (
                <CourseCard
                  key={course.course_id}
                  course={course}
                  progress={getCourseProgress(course.course_id, course.lesson_count)}
                  onClick={setActiveCourseId}
                />
              ))}
            </div>
          )}
        </section>

        {/* Financial Books & Reading Shelf */}
        <BookGrid onOpenBook={setActiveBook} />

        {/* Uploaded media section */}
        <section className="lh-section lh-section--media" aria-labelledby="lh-media-title">
          <h2 id="lh-media-title" className="lh-section__title">Thư viện media đã tải lên</h2>

          <div className="lh-media-tabs" role="tablist">
            {[['video', 'Video'], ['book', 'Sách & Tài liệu']].map(([id, label]) => (
              <button key={id} type="button" role="tab" aria-selected={mediaTab === id} className={`lh-media-tab ${mediaTab === id ? 'lh-media-tab--active' : ''}`} onClick={() => { setMediaTab(id); setActiveVideo(null) }}>
                {label}
              </button>
            ))}
          </div>

          {mediaTab === 'video' && activeVideo ? (
            <VideoPreview video={activeVideo} onClose={() => setActiveVideo(null)} />
          ) : null}

          {mediaTab === 'video' ? (
            <LocalVideoGrid
              items={filterLocal(videoAssets, search)}
              loading={assetLoading}
              error={assetError}
              onPlay={setActiveVideo}
            />
          ) : null}

          {mediaTab === 'book' ? (
            <LocalBookGrid
              items={filterLocal(bookAssets, search)}
              loading={assetLoading}
              error={assetError}
              onRead={setActiveBook}
            />
          ) : null}
        </section>
      </div>

      <p className="lh-footer-note">Học liệu phục vụ giáo dục — không phải khuyến nghị đầu tư.</p>
    </section>
  )
}
