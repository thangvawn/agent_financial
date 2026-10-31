import { useAccountId } from '../../../shared/auth/accountContext'
import { useEffect, useMemo, useState } from 'react'

import { DEMO_COURSES, filterCourses, normalizeDbCourse } from '../content/courseCatalogData'
import { useCourseBookmarks } from '../hooks/useCourseBookmarks'
import { fetchLearningCatalog } from '../services/learningApi'
import { BookReaderWorkspace } from './BookReaderWorkspace'
import { toReadableBook } from './bookSource'
import DocumentLibrary from './DocumentLibrary'
import PersonalLibrary from './PersonalLibrary'
import UploadDocumentDialog from './UploadDocumentDialog'
import {usePersonalLibrary} from '../hooks/usePersonalLibrary'
import {resolveBookSource} from './bookSource'
import CourseCard from './CourseCard'
import CoursePlayerPage from './CoursePlayerPage'
import CourseSectionHeader from './CourseSectionHeader'
import LearningTopControls from './LearningTopControls'
import LearnTutorPanel from './LearnTutorPanel'
import MockExamRoomPage from './MockExamRoomPage'
import QuantaDocsPage from './QuantaDocsPage'
import { AgentRunPanel } from '../../../shared/agentic/AgentRunPanel'
import './learn-hub.css'
import './learn-hub-catalog.css'

function progressKey(sessionId) {
  return `northstar.learn-hub.progress:${sessionId || 'anonymous'}`
}

function readAllProgress(sessionId) {
  try { return JSON.parse(localStorage.getItem(progressKey(sessionId)) || '{}') } catch { return {} }
}

function getCourseProgress(courseId, totalLessons, sessionId) {
  const saved = readAllProgress(sessionId)
  const done = (saved[courseId] || []).length
  if (!done) return null
  return { pct: totalLessons > 0 ? (done / totalLessons) * 100 : 0 }
}

export default function LearningHomePage({ sessionId, onBack, initialSubTab = 'courses', initialSearch = '' }) {
  const accountId = useAccountId()
  const [activeSubTab, setActiveSubTab] = useState(initialSubTab)
  const [search, setSearch] = useState(initialSearch)
  const [difficulty, setDifficulty] = useState('all')
  const [sortBy, setSortBy] = useState('latest')
  const [activeCourseId, setActiveCourseId] = useState(null)
  const [activeBook, setActiveBook] = useState(null)
  const [activeRunId, setActiveRunId] = useState(null)
  const [activeRunStatus, setActiveRunStatus] = useState(null)
  const [dbCourses, setDbCourses] = useState([])
  const [showUpload,setShowUpload]=useState(false)
  const library=usePersonalLibrary(sessionId)
  function openBook(book) {
    const saved=library.items.find(item=>item.id===book.library_id || item.source_url===resolveBookSource(book).sourceUrl)
    setActiveBook(saved?{...book,library_id:saved.id,libraryItem:saved}:book)
  }

  const { bookmarks, toggleBookmark } = useCourseBookmarks(accountId)

  useEffect(() => {
    let cancelled = false
    fetchLearningCatalog('course', { limit: 100 })
      .then((res) => {
        if (cancelled) return
        if (Array.isArray(res?.items) && res.items.length > 0) {
          const normalized = res.items.map(normalizeDbCourse)
          const dbIds = new Set(
            normalized.flatMap((c) => [c.course_id, c.external_id, c.code].filter(Boolean))
          )
          const extras = DEMO_COURSES.filter((c) => !dbIds.has(c.course_id))
          setDbCourses([...extras, ...normalized])
        } else {
          setDbCourses(DEMO_COURSES)
        }
      })
      .catch(() => { if (!cancelled) setDbCourses(DEMO_COURSES) })
    return () => { cancelled = true }
  }, [])

  const allCourses = dbCourses.length > 0 ? dbCourses : DEMO_COURSES

  const filteredCourses = useMemo(() => {
    let list = filterCourses(allCourses, { search, difficulty })
    if (sortBy === 'bookmarked') {
      list = [...list].sort((a, b) => {
        const aBm = bookmarks.includes(a.course_id) ? 1 : 0
        const bBm = bookmarks.includes(b.course_id) ? 1 : 0
        return bBm - aBm
      })
    } else if (sortBy === 'lessons') {
      list = [...list].sort((a, b) => (b.lesson_count || 0) - (a.lesson_count || 0))
    } else if (sortBy === 'duration') {
      list = [...list].sort((a, b) => {
        const getHours = (str) => parseFloat(String(str || '0').replace(',', '.')) || 0
        return getHours(b.total_duration) - getHours(a.total_duration)
      })
    }
    return list
  }, [allCourses, search, difficulty, sortBy, bookmarks])

  const selectedCourse = useMemo(
    () => (activeCourseId ? allCourses.find((c) => c.course_id === activeCourseId) || null : null),
    [activeCourseId, allCourses]
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
    return <BookReaderWorkspace key={`${accountId}:${activeBook.library_id || activeBook.book_id || activeBook.paper_id}`} book={toReadableBook(activeBook)} sessionId={sessionId} library={library} onClose={() => setActiveBook(null)} />
  }

  if (activeCourseId) {
    return <CoursePlayerPage courseId={activeCourseId} course={selectedCourse} sessionId={sessionId} onBack={() => setActiveCourseId(null)} />
  }

  if (activeSubTab === 'mock_exam') {
    return <MockExamRoomPage accountId={accountId} key={accountId} onBack={() => setActiveSubTab('courses')} />
  }

  if (activeSubTab === 'quanta_docs') {
    return <QuantaDocsPage onBack={() => setActiveSubTab('courses')} />
  }

  return (
    <section className="lh-shell" data-domain="learn_hub">
      <LearningTopControls
        activeSubTab={activeSubTab}
        onSubTabChange={setActiveSubTab}
        search={search}
        onSearchChange={setSearch}
        difficulty={difficulty}
        onDifficultyChange={setDifficulty}
      />

      {activeRunId && (
        <div className="lh-agent-panel-container">
          <AgentRunPanel runId={activeRunId} status={activeRunStatus} onCancel={() => { setActiveRunId(null); setActiveRunStatus(null) }} />
        </div>
      )}

      <div className="lh-body">
        {activeSubTab === 'courses' ? (
          <div className="lh-catalog-container">
            <CourseSectionHeader count={filteredCourses.length} sortBy={sortBy} onSortChange={setSortBy} />
            {filteredCourses.length === 0 ? (
              <div className="lh-empty-state">
                <p>Không tìm thấy khóa học nào phù hợp với bộ lọc hiện tại.</p>
                <button type="button" className="lh-reset-filter-btn" onClick={() => { setSearch(''); setDifficulty('all'); setSortBy('latest') }}>
                  Xóa bộ lọc
                </button>
              </div>
            ) : (
              <div className="lhc-grid">
                {filteredCourses.map((course) => (
                  <CourseCard
                    key={course.course_id}
                    course={course}
                    progress={getCourseProgress(course.course_id, course.lesson_count, sessionId)}
                    onClick={setActiveCourseId}
                    isBookmarked={bookmarks.includes(course.course_id)}
                    onToggleBookmark={toggleBookmark}
                  />
                ))}
              </div>
            )}
          </div>
        ) : null}

        {activeSubTab === 'docs' ? (
          <div className="lh-catalog-container">
            <DocumentLibrary onOpenBook={openBook} onUpload={()=>setShowUpload(true)} library={library} onShowShelf={()=>setActiveSubTab('shelf')} />
          </div>
        ) : null}

        {activeSubTab === 'shelf' && <div className="lh-catalog-container"><PersonalLibrary library={library} onOpenBook={openBook} onUpload={()=>setShowUpload(true)} onBrowse={()=>setActiveSubTab('docs')}/></div>}

        {activeSubTab === 'ai_tutor' ? (
          <div className="lh-catalog-container lh-catalog-container--tutor">
            <LearnTutorPanel sessionId={sessionId} />
          </div>
        ) : null}
      </div>
      {showUpload && <UploadDocumentDialog onClose={()=>setShowUpload(false)} onUpload={library.upload} onAdded={()=>setActiveSubTab('shelf')}/>}
    </section>
  )
}
