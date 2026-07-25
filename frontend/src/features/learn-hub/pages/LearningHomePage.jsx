import { useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useLearningAssets } from '..'
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

import { BookOpen, Compass, Award, TrendingUp, BarChart3, FileText, Sparkles } from 'lucide-react'
import '../../market-portfolio/pages/market-portfolio-panels.css'

const LEARN_SUBTABS = [
  { id: 'all', label: 'Khóa học & Bài giảng', icon: BookOpen },
  { id: 'docs', label: 'Sách & Tài liệu', icon: FileText },
  { id: 'ai_tutor', label: 'Hỏi AI Tutor', icon: Sparkles },
]

export default function LearningHomePage({ sessionId, onBack }) {
  const queryClient = useQueryClient()
  const [category, setCategory] = useState('all')
  const [activeSubTab, setActiveSubTab] = useState('all')
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
      {/* Synchronized Sub-Tab Bar with Integrated Search Input */}
      <div className="mp-desk__tabs justify-between items-center" role="tablist" aria-label="Learn Hub Sub Tabs">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          {LEARN_SUBTABS.map((item) => {
            const Icon = item.icon
            const isActive = activeSubTab === item.id
            return (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={isActive ? 'is-active' : ''}
                onClick={() => {
                  setActiveSubTab(item.id)
                  if (['all', 'basics', 'ta', 'valuation'].includes(item.id)) {
                    setCategory(item.id)
                  }
                }}
              >
                <Icon size={14} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </div>

        {/* Integrated Search Box */}
        <div className="relative flex items-center ml-auto flex-shrink-0">
          <SearchIcon className="absolute left-3 w-3.5 h-3.5 text-zinc-400 pointer-events-none" aria-hidden="true" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm khóa học, chủ đề..."
            className="pl-8 pr-3 py-1 text-xs text-zinc-200 bg-zinc-900/90 border border-zinc-800 focus:border-teal-500/50 rounded-lg outline-none transition-all w-44 focus:w-56"
          />
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
