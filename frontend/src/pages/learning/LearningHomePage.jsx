import { useEffect, useMemo, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import {
  LEARN_QUICK_PROMPTS,
  useAskLearningTutor,
  useCompleteLearningLesson,
  useLearningAssets,
  useLearningCatalog,
  useLearningHome,
  useLearningNextLessonBundle,
  useSubmitLearningQuiz,
} from '../../modules/learning'
import FloatingAssistant from '../../shared/assistant/FloatingAssistant.jsx'
import { PlayIcon, BookIcon, HeadphonesIcon, TargetIcon, LightbulbIcon, PiggyBankIcon, CalculatorIcon, ScaleIcon, ShieldIcon, ShieldPlusIcon, PlantIcon, FlagIcon, LineChartIcon, PieChartIcon, FileTextIcon, FlameIcon, StarIcon, CheckCircleIcon, ClockIcon, ArrowRightIcon, BarChartIcon, TrendingUpIcon, GlobeIcon, PercentIcon } from '../../shared/Icons'
import './learning.css'

const VIDEO_EXTENSIONS = new Set(['mp4', 'webm', 'mov', 'm4v', 'avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'flv', '3gp'])
const AUDIO_EXTENSIONS = new Set(['mp3', 'wav', 'm4a', 'aac', 'ogg', 'oga', 'flac', 'opus'])

export default function LearningHomePage({
  sessionId,
  initialFocusView = 'lesson',
  onBack,
  onOpenAdmin,
  onOpenGuidedInvesting,
  onOpenCommunity,
  onOpenInsights,
}) {
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useLearningHome(sessionId)

  const [activeLearnView, setActiveLearnView] = useState(initialFocusView)
  
  useEffect(() => {
    setActiveLearnView(initialFocusView)
  }, [initialFocusView])
  const [catalogKind, setCatalogKind] = useState('video')
  const [catalogTopic, setCatalogTopic] = useState('')
  const [catalogSearch, setCatalogSearch] = useState('')
  const [activeBook, setActiveBook] = useState(null)

  const [quizResult, setQuizResult] = useState(null)
  const [tutor, setTutor] = useState(null)
  const [question, setQuestion] = useState('Tóm tắt bài này như cho người mới bắt đầu.')
  const [answers, setAnswers] = useState({})
  const [tutorThread, setTutorThread] = useState([])
  const [mutationError, setMutationError] = useState('')

  const {
    lesson,
    coach,
    contextCards,
    isLoading: lessonLoading,
    lessonError: lessonFetchError,
  } = useLearningNextLessonBundle(sessionId, data?.next_lesson_id)

  const {
    videoItems: rawVideoItems,
    audioItems: rawAudioItems,
    bookItems,
    isLoading: assetLoading,
    error: assetError,
    audioFailed,
  } = useLearningAssets(sessionId)

  const videoAssets = useMemo(() => filterAssetsByType(rawVideoItems, 'video'), [rawVideoItems])
  const audioAssets = useMemo(() => {
    if (rawAudioItems) return dedupeAssetsById(filterAssetsByType(rawAudioItems, 'audio'))
    if (audioFailed) return dedupeAssetsById(filterAssetsByType(rawVideoItems, 'audio'))
    return []
  }, [audioFailed, rawAudioItems, rawVideoItems])
  const bookAssets = bookItems

  const {
    items: catalogItems,
    topics: catalogTopics,
    isLoading: catalogLoading,
    error: catalogError,
  } = useLearningCatalog({
    enabled: activeLearnView === 'library' && Boolean(sessionId),
    kind: catalogKind,
    topic: catalogTopic,
  })

  const submitQuizMutation = useSubmitLearningQuiz()
  const completeLessonMutation = useCompleteLearningLesson()
  const askTutorMutation = useAskLearningTutor()
  const submittingQuiz = submitQuizMutation.isPending
  const completingLesson = completeLessonMutation.isPending
  const askingTutor = askTutorMutation.isPending

  const lessonError = lessonFetchError || mutationError

  useEffect(() => {
    if (!lesson?.lesson_id) return
    setQuizResult(null)
    setTutor(null)
    setAnswers({})
  }, [lesson?.lesson_id])

  const filteredCatalogItems = useMemo(() => {
    if (!catalogSearch.trim()) return catalogItems
    const searchLow = catalogSearch.toLowerCase().trim()
    return catalogItems.filter((item) => {
      const title = (item.title || '').toLowerCase()
      const description = (item.description || item.abstract || '').toLowerCase()
      const author = (item.author || '').toLowerCase()
      const provider = (item.provider || '').toLowerCase()
      const instructor = (item.instructor || '').toLowerCase()
      const channel = (item.channel || '').toLowerCase()
      const authors = Array.isArray(item.authors) ? item.authors.join(' ').toLowerCase() : ''

      return (
        title.includes(searchLow) ||
        description.includes(searchLow) ||
        author.includes(searchLow) ||
        authors.includes(searchLow) ||
        provider.includes(searchLow) ||
        instructor.includes(searchLow) ||
        channel.includes(searchLow)
      )
    })
  }, [catalogItems, catalogSearch])

  const resourceBundle = useMemo(
    () => buildRealResourceBundle({ lesson, videoAssets, audioAssets, bookAssets }),
    [audioAssets, bookAssets, lesson, videoAssets],
  )
  const completionText = useMemo(() => `${Math.max(0, data?.completion_pct || 0)}%`, [data?.completion_pct])
  const dashboard = useMemo(
    () => buildLearningDashboard({ data, lesson, contextCards, videoAssets, audioAssets, bookAssets, resourceBundle }),
    [audioAssets, bookAssets, contextCards, data, lesson, resourceBundle, videoAssets],
  )
  useLearnDashboardMotion(!!data && !isLoading && !error, activeLearnView)

  async function handleQuizSubmit() {
    if (!lesson || submittingQuiz) return
    setMutationError('')
    try {
      const payload = await submitQuizMutation.mutateAsync({
        sessionId,
        lessonId: lesson.lesson_id,
        answers,
      })
      setQuizResult(payload)
    } catch (err) {
      setMutationError(err.message)
    }
  }

  async function handleComplete() {
    if (!lesson || completingLesson) return
    setMutationError('')
    try {
      await completeLessonMutation.mutateAsync({
        sessionId,
        lessonId: lesson.lesson_id,
      })
    } catch (err) {
      setMutationError(err.message)
    }
  }

  async function handleTutor() {
    if (!lesson || askingTutor) return
    setMutationError('')
    try {
      const payload = await askTutorMutation.mutateAsync({
        sessionId,
        lessonId: lesson.lesson_id,
        question,
      })
      setTutor(payload)
    } catch (err) {
      setMutationError(err.message)
    }
  }

  function applyPrompt(prompt) {
    setQuestion(prompt)
  }

  function runPracticalCta(ctaType) {
    if (ctaType === 'guided_investing' && onOpenGuidedInvesting) {
      onOpenGuidedInvesting('market_context')
      return
    }
    if (ctaType === 'insights' && onOpenInsights) {
      onOpenInsights()
      return
    }
    if (onOpenGuidedInvesting) onOpenGuidedInvesting('market_context')
  }

  if (!sessionId) {
    return (
      <section className="learn-os-page">
        <div className="learn-os-empty">
          <h1>Learn Hub cần session onboarding để cá nhân hóa.</h1>
          <p>Hoàn tất onboarding trước để mở learning path phù hợp với trạng thái tài chính của bạn.</p>
          {onBack ? (
            <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={onBack}>
              Về Home
            </button>
          ) : null}
        </div>
      </section>
    )
  }

  if (isLoading) {
    return (
      <section className="learn-os-page learn-os-page--loading">
        <p className="learn-os-eyebrow">Learn Hub</p>
        <h1>Đang dựng lộ trình học cho bạn...</h1>
      </section>
    )
  }

  if (error) {
    return (
      <section className="learn-os-page">
        <div className="learn-os-empty">
          <h1>Chưa tải được Learn Hub.</h1>
          <p>{error}</p>
          <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}>
            Thử lại
          </button>
        </div>
      </section>
    )
  }

  if (!data) {
    return (
      <section className="learn-os-page">
        <div className="learn-os-empty">
          <h1>Learn Hub chưa có dữ liệu.</h1>
          <p>Hãy làm mới lại trang hoặc quay về Home để đồng bộ session.</p>
        </div>
      </section>
    )
  }

  if (activeBook) {
    return (
      <section className="learn-os-page learn-os-page--reader">
        <BookReaderWorkspace
          book={activeBook}
          sessionId={sessionId}
          asPage
          onClose={() => setActiveBook(null)}
        />
      </section>
    )
  }

  return (
    <section className={`learn-os-page learn-os-page--${activeLearnView}`}>
      <header className="learn-os-topbar">
        <div>
          <h1>Learn Hub</h1>
          <p>{data.path_label} · {completionText} hoàn thành · dữ liệu runtime từ backend.</p>
        </div>
      </header>

      <section className="learn-os-topic-carousel learn-reveal" aria-label="Explore topics">
        <header className="learn-os-section-title">
          <h2>Chủ đề theo lộ trình</h2>
          <button type="button" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}>Làm mới</button>
        </header>
        <div className="learn-os-topic-strip">
          {dashboard.topics.map((topic, index) => (
            <button
              key={topic.label}
              type="button"
              className={`learn-os-topic-tile ${index === 0 ? 'is-active' : ''}`}
              onClick={() => setQuestion(`Giải thích ${topic.label} cho người mới học tài chính.`)}
            >
              <span>{topic.icon}</span>
              <strong>{topic.label}</strong>
              <small>{topic.count}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="learn-os-progress-panel learn-reveal" aria-label="Learning progress overview">
        <article className="learn-os-progress-card">
          <header className="learn-os-mini-head">
            <span><TrendingUpIcon size={16} /></span>
            <strong>Tiến độ học của bạn</strong>
          </header>
          <div className="learn-os-progress-card__body">
            <div className="learn-os-ring-wrap">
              <svg viewBox="0 0 36 36" className="learn-os-progress-ring">
                <path className="learn-os-progress-ring__bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path className="learn-os-progress-ring__value" strokeDasharray={`${data?.completion_pct || 12}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div>
                <strong>{completionText}</strong>
                <span>Tổng tiến độ</span>
              </div>
            </div>
            <dl className="learn-os-progress-metrics">
              <div>
                <dt>Khoá học</dt>
                <dd>{dashboard.stats[2].value}</dd>
              </div>
              <div>
                <dt>Đã hoàn thành</dt>
                <dd>{dashboard.stats[1].value}</dd>
              </div>
              <div>
                <dt>Bài kế tiếp</dt>
                <dd>{data?.next_lesson_title ? shortTitle(data.next_lesson_title, 18) : '—'}</dd>
              </div>
            </dl>
          </div>
        </article>
      </section>

      <section className="learn-os-continue learn-reveal">
        <header className="learn-os-section-title">
          <h2>Khoá học & lộ trình</h2>
          <button type="button" onClick={() => setActiveLearnView('lesson')}>Mở bài học</button>
        </header>
        <div className="learn-os-course-strip">
          {dashboard.courseCards.map((item) => (
            <button key={item.title} type="button" className="learn-os-course-card" onClick={() => setActiveLearnView('lesson')}>
              <div className={`learn-os-course-card__cover ${item.tone}`}>
                {item.icon}
                <span>{item.tag}</span>
              </div>
              <strong>{item.title}</strong>
              <p>{item.meta}</p>
              <div className="learn-os-course-card__bar">
                <i style={{ width: `${item.progress}%` }} />
                <small>{item.progress}%</small>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="learn-os-main-row learn-reveal">
        <article className="learn-os-card learn-os-card--recommended">
          <header className="learn-os-card__head">
            <h2>Gợi ý cho bạn</h2>
            <button type="button" className="learn-os-link-btn" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}>Làm mới</button>
          </header>
          <div className="learn-os-recommended-list">
            {dashboard.recommended.map((item) => (
              <article key={item.title} className="learn-os-recommended-item">
                <div className="learn-os-recommended-item__thumb is-cover-dark">{item.badge}</div>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.summary}</p>
                </div>
                <div className="learn-os-recommended-item__meta">
                  <span>{item.meta}</span>
                  <em>{item.score}</em>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="learn-os-card learn-os-card--stats">
          <header className="learn-os-card__head">
            <h2>Số liệu runtime</h2>
            <span className="learn-os-chip-alt">SQLite</span>
          </header>
          <div className="learn-os-stat-grid">
            {dashboard.statGrid.map(({ label, value, delta }) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
                <small>{delta}</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="learn-os-dashboard-grid learn-os-dashboard-grid--bottom learn-reveal">
        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <h2>Thư viện sách</h2>
            <button type="button" className="learn-os-link-btn" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning', 'assets'] })}>Làm mới</button>
          </header>
          <div className="learn-os-reading-row">
            {dashboard.readingLibrary.map((item) => (
              <button key={item.asset_id} type="button" className="learn-os-book-mini" onClick={() => setActiveBook(item)}>
                <span className="is-cover-paper">{shortTitle(item.title, 18)}</span>
                <strong>{item.title}</strong>
                <small>{item.file_name}</small>
                <em>{formatBytes(item.size_bytes)}</em>
              </button>
            ))}
            {!dashboard.readingLibrary.length ? <p className="learn-os-muted">Chưa có sách trong thư viện local.</p> : null}
          </div>
        </article>

        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <h2>Bài học gần nhất trong lộ trình</h2>
            <button type="button" className="learn-os-link-btn" onClick={() => setActiveLearnView('lesson')}>Mở bài học</button>
          </header>
          <div className="learn-os-live-list">
            {dashboard.pathLessons.slice(0, 4).map((item, index) => (
              <button key={item.lesson_id} type="button" className="learn-os-live-row" onClick={() => setQuestion(`Giải thích bài ${item.title} cho tôi.`)}>
                <span>{item.status === 'completed' ? 'XONG' : item.is_next ? 'TIẾP' : `L${index + 1}`}</span>
                <strong>{item.title}<small>{contentTypeLabel(item.content_type)} · {tierLabel(item.tier)}</small></strong>
                <em>{item.estimated_minutes}m</em>
                <b>{item.status === 'completed' ? 'Ôn lại' : 'Học'}</b>
              </button>
            ))}
            {!dashboard.pathLessons.length ? <p className="learn-os-muted">Lộ trình chưa được sinh. Hoàn tất onboarding để mở bài học.</p> : null}
          </div>
        </article>
      </section>

      <section className="learn-os-dashboard-grid learn-os-dashboard-grid--footer learn-reveal">
        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <div>
              <h2>Kế hoạch tuần này</h2>
              <p>{dashboard.studyWeekLabel}</p>
            </div>
            <span className="learn-os-chip-alt">Hôm nay</span>
          </header>
          <div className="learn-os-study-plan">
            <div className="learn-os-calendar-strip">
              {dashboard.studyDays.map((day, index) => (
                <span key={day} className={index === 0 ? 'is-active' : ''}>{day}</span>
              ))}
            </div>
            {dashboard.studyPlan.length ? dashboard.studyPlan.map((item) => (
              <label key={item.lesson_id} className="learn-os-task-row">
                <input type="checkbox" readOnly checked={item.status === 'completed'} />
                <strong>{item.task}<small>{item.sub}</small></strong>
                <em>{item.time}</em>
              </label>
            )) : <p className="learn-os-muted">Chưa có việc trong tuần.</p>}
          </div>
        </article>

        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <div>
              <h2>Bridge sang thực hành</h2>
              <p>Áp dụng bài học vào các surface mô phỏng.</p>
            </div>
          </header>
          <div className="learn-os-bridge-list">
            <button type="button" className="learn-os-bridge-row" onClick={() => onOpenGuidedInvesting?.('market_context')}>
              <strong>Guided Investing<small>Đọc rủi ro & drawdown với BCTC</small></strong>
              <ArrowRightIcon size={16} />
            </button>
            <button type="button" className="learn-os-bridge-row" onClick={() => onOpenInsights?.()}>
              <strong>Insights<small>Xem dữ liệu thị trường để nối ngữ cảnh</small></strong>
              <ArrowRightIcon size={16} />
            </button>
          </div>
        </article>
      </section>

      <article className="learn-os-card learn-os-card--catalog learn-reveal">
        <header className="learn-os-card__head">
          <div>
            <p className="learn-os-eyebrow">Thư viện học liệu</p>
            <h2>Catalog từ arXiv · MIT · Yale · archive.org</h2>
            <p>Curated bởi crawler — dữ liệu từ <code>learning_courses/videos/books/papers</code>.</p>
          </div>
          <div className="learn-os-inline-actions">
            <button
              type="button"
              className="learn-os-btn learn-os-btn--ghost"
              onClick={() => {
                setCatalogTopic('')
                setCatalogSearch('')
              }}
            >
              Đặt lại bộ lọc
            </button>
          </div>
        </header>

        <div className="learn-os-catalog-toolbar">
          <nav className="learn-os-catalog-kinds" aria-label="Loại tài nguyên">
            {[
              ['video', 'Video', dashboard.mediaCounts.videos || 0],
              ['book', 'Sách', dashboard.mediaCounts.books || 0],
              ['paper', 'Paper', 0],
              ['course', 'Khoá học', 0],
            ].map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={catalogKind === id ? 'is-active' : ''}
                onClick={() => setCatalogKind(id)}
              >
                {label}
              </button>
            ))}
          </nav>

          <div className="learn-os-catalog-filter-bar">
            {catalogTopics.length ? (
              <div className="learn-os-filter-select-wrapper">
                <select
                  className="learn-os-catalog-select"
                  value={catalogTopic}
                  onChange={(e) => setCatalogTopic(e.target.value)}
                  aria-label="Chọn chủ đề"
                >
                  <option value="">Tất cả chủ đề</option>
                  {catalogTopics.map((topic) => (
                    <option key={topic.topic_id} value={topic.topic_id}>
                      {topic.label_vi} ({topic.resource_count || 0})
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            <div className="learn-os-catalog-search-wrapper">
              <span className="learn-os-catalog-search-icon">🔍</span>
              <input
                type="text"
                className="learn-os-catalog-search-input"
                value={catalogSearch}
                onChange={(e) => setCatalogSearch(e.target.value)}
                placeholder={`Tìm kiếm ${
                  catalogKind === 'video'
                    ? 'video'
                    : catalogKind === 'book'
                    ? 'sách'
                    : catalogKind === 'paper'
                    ? 'tài liệu'
                    : 'khoá học'
                }...`}
              />
              {catalogSearch && (
                <button
                  type="button"
                  className="learn-os-catalog-search-clear"
                  onClick={() => setCatalogSearch('')}
                  title="Xóa tìm kiếm"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        </div>

        {catalogLoading ? <p className="learn-os-muted">Đang tải catalog…</p> : null}
        {catalogError ? <p className="learn-os-error">{catalogError}</p> : null}

        {!catalogLoading && !catalogError && !catalogItems.length ? (
          <div className="learn-os-catalog-empty">
            <p>Catalog chưa có dữ liệu. Chạy <code>risk-learning-crawl</code> để fill.</p>
          </div>
        ) : null}

        {!catalogLoading && !catalogError && catalogItems.length > 0 && !filteredCatalogItems.length ? (
          <div className="learn-os-catalog-empty">
            <p>Không tìm thấy tài liệu nào khớp với từ khóa hoặc chủ đề đã chọn.</p>
          </div>
        ) : null}

        <div className="learn-os-catalog-list">
          {filteredCatalogItems.map((item) => (
            <CatalogCard key={item[`${catalogKind}_id`]} kind={catalogKind} item={item} />
          ))}
        </div>
      </article>

      <article className="learn-os-card learn-os-card--media learn-reveal">
        <header className="learn-os-card__head">
          <div>
            <p className="learn-os-eyebrow">Media Library</p>
            <h2>Video, audio và sách từ thư mục local của bạn</h2>
            <p>
              Nguồn đọc từ <code>data/learning_assets/videos</code>, <code>data/learning_assets/audios</code> và{' '}
              <code>data/learning_assets/books</code>.
              Cover sách tự nhận từ <code>data/learning_assets/images</code> cùng tên file.
            </p>
          </div>
          <div className="learn-os-inline-actions">
            <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning', 'assets'] })}>
              Refresh media
            </button>
          </div>
        </header>
        {assetLoading ? <p className="learn-os-muted">Đang quét media local...</p> : null}
        {assetError ? <p className="learn-os-error">{assetError}</p> : null}

        <section className="learn-os-media-section">
          <h3>Danh sách video ({videoAssets.length})</h3>
          <div className="learn-os-video-grid">
            {videoAssets.map((item) => (
              <article key={item.asset_id} className="learn-os-video-card">
                <MediaCover item={item} variant="video" />
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.file_name} · {formatBytes(item.size_bytes)}</small>
                </div>
                <div className="learn-os-inline-actions">
                  <a className="learn-os-btn learn-os-btn--ghost" href={item.url} target="_blank" rel="noreferrer">
                    Xem video
                  </a>
                </div>
              </article>
            ))}
            {!videoAssets.length && !assetLoading ? (
              <p className="learn-os-muted">Chưa có video. Thêm file vào `data/learning_assets/videos` rồi bấm Refresh media.</p>
            ) : null}
          </div>
        </section>

        <section className="learn-os-media-section">
          <h3>Danh sách audio ({audioAssets.length})</h3>
          <div className="learn-os-audio-grid">
            {audioAssets.map((item) => (
              <article key={item.asset_id} className="learn-os-audio-card">
                <MediaCover item={item} variant="audio" />
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.file_name} · {formatBytes(item.size_bytes)}</small>
                </div>
                <audio controls preload="none" src={item.url} />
              </article>
            ))}
            {!audioAssets.length && !assetLoading ? (
              <p className="learn-os-muted">Chưa có audio. Thêm file vào `data/learning_assets/audios` rồi bấm Refresh media.</p>
            ) : null}
          </div>
        </section>

        <section className="learn-os-media-section">
          <h3>Danh sách sách ({bookAssets.length})</h3>
          <div className="learn-os-book-grid">
            {bookAssets.map((item) => (
              <article key={item.asset_id} className="learn-os-book-card">
                <BookCoverPreview item={item} />
                <div>
                  <strong>{item.title}</strong>
                  <small>{item.file_name}</small>
                  <small>{formatBytes(item.size_bytes)}</small>
                </div>
                <div className="learn-os-inline-actions">
                  <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={() => setActiveBook(item)}>
                    Đọc sách
                  </button>
                  <a className="learn-os-btn learn-os-btn--ghost" href={item.url} target="_blank" rel="noreferrer">
                    Mở file
                  </a>
                </div>
              </article>
            ))}
            {!bookAssets.length && !assetLoading ? (
              <p className="learn-os-muted">
                Chưa có sách. Thêm file vào `data/learning_assets/books` (pdf/epub) và cover ảnh vào
                `data/learning_assets/images` cùng tên file.
              </p>
            ) : null}
          </div>
        </section>
      </article>

      <section className="learn-os-layout learn-reveal">
        <article id="learn-lesson-card" className="learn-os-card learn-os-card--lesson">
          <header className="learn-os-card__head">
            <div>
              <p className="learn-os-eyebrow">Bài học hôm nay</p>
              <h2>{lesson?.title || data.next_lesson_title}</h2>
              <p>{lesson?.summary || data.recommendation_summary}</p>
            </div>
            <div className="learn-os-pills">
              <span>{tierLabel(lesson?.tier)}</span>
              <span>{contentTypeLabel(lesson?.content_type)}</span>
              <span>{lesson?.estimated_minutes || 3} phút</span>
            </div>
          </header>

          {lessonLoading ? <p className="learn-os-muted">Đang tải nội dung bài học...</p> : null}
          {lessonError ? <p className="learn-os-error">{lessonError}</p> : null}

          {lesson?.body?.length ? (
            <div className="learn-os-reading">
              {lesson.body.map((block) => (
                <p key={block}>{block}</p>
              ))}
            </div>
          ) : (
            <p className="learn-os-muted">Chưa có nội dung bài chi tiết.</p>
          )}

          {lesson?.glossary?.length ? (
            <div className="learn-os-glossary">
              <h3>Glossary nhanh</h3>
              <div className="learn-os-glossary-grid">
                {lesson.glossary.map((term) => (
                  <article key={term.term}>
                    <strong>{term.term}</strong>
                    <p>{term.definition}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : null}

          {lesson?.quiz_questions?.length ? (
            <div className="learn-os-quiz">
              <h3>Quiz kiểm tra hiểu</h3>
              {lesson.quiz_questions.map((quiz) => (
                <article key={quiz.question_id} className="learn-os-quiz-item">
                  <p>{quiz.prompt}</p>
                  <div className="learn-os-options">
                    {quiz.options.map((option) => {
                      const selected = answers[quiz.question_id] === option
                      return (
                        <button
                          key={option}
                          type="button"
                          className={`learn-os-option ${selected ? 'is-selected' : ''}`}
                          onClick={() => setAnswers((current) => ({ ...current, [quiz.question_id]: option }))}
                        >
                          {option}
                        </button>
                      )
                    })}
                  </div>
                </article>
              ))}
              <div className="learn-os-inline-actions">
                <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={handleQuizSubmit} disabled={submittingQuiz}>
                  {submittingQuiz ? 'Đang chấm quiz...' : 'Nộp quiz'}
                </button>
                <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={handleComplete} disabled={completingLesson}>
                  {completingLesson ? 'Đang cập nhật...' : 'Đánh dấu hoàn thành'}
                </button>
              </div>
              {quizResult ? (
                <div className={`learn-os-quiz-result ${quizResult.passed ? 'is-pass' : 'is-retry'}`}>
                  <strong>Score: {quizResult.score}</strong>
                  <p>{quizResult.passed ? 'Bạn đã qua quiz. Tiếp tục bài kế tiếp nhé.' : 'Chưa sao, làm lại lần nữa để nắm chắc hơn.'}</p>
                  {quizResult.explanations?.length ? (
                    <ul>
                      {quizResult.explanations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </article>

        <div className="learn-os-sidebar">
          <article className="learn-os-card">
            <header className="learn-os-card__head">
              <div>
                <p className="learn-os-eyebrow">AI Companion</p>
                <h2>Tutor + Coach luôn sẵn sàng</h2>
              </div>
            </header>
            {coach ? (
              <div className="learn-os-coach">
                <strong>{coach.title}</strong>
                <p>{coach.message}</p>
              </div>
            ) : (
              <p className="learn-os-muted">Coach sẽ xuất hiện khi có đủ ngữ cảnh.</p>
            )}
            <div className="learn-os-prompt-list">
              {LEARN_QUICK_PROMPTS.map((prompt) => (
                <button key={prompt} type="button" className="learn-os-option" onClick={() => applyPrompt(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} />
            <div className="learn-os-inline-actions">
              <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={handleTutor} disabled={askingTutor || !lesson}>
                {askingTutor ? 'Tutor đang trả lời...' : 'Hỏi Tutor'}
              </button>
              {onOpenCommunity ? (
                <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={() => onOpenCommunity('risk-literacy-circle')}>
                  Học cùng Community
                </button>
              ) : null}
            </div>
            {tutor ? (
              <div className="learn-os-tutor-answer">
                <strong>{tutor.summary}</strong>
                <p>{tutor.explanation}</p>
                <small>{tutor.check_question}</small>
              </div>
            ) : null}
          </article>

          <article className="learn-os-card">
            <header className="learn-os-card__head">
              <div>
                <p className="learn-os-eyebrow">Gợi ý theo lộ trình</p>
                <h2>Bổ trợ nhanh trước/sau bài học</h2>
              </div>
            </header>
            <section className="learn-os-resource-block">
              <h3>Video picks theo bài hiện tại</h3>
              <div className="learn-os-resource-list">
                {resourceBundle.videos.map((item) => (
                  <a key={item.id} href={item.href} target="_blank" rel="noreferrer" className="learn-os-resource">
                    <strong>{item.title}</strong>
                    <small>{item.duration}</small>
                  </a>
                ))}
              </div>
            </section>
            <section className="learn-os-resource-block">
              <h3>Book notes theo bài hiện tại</h3>
              <div className="learn-os-resource-list">
                {resourceBundle.books.map((item) => (
                  item.href ? (
                    <a key={item.id} href={item.href} target="_blank" rel="noreferrer" className="learn-os-resource">
                      <strong>{item.title}</strong>
                      <p>{item.summary}</p>
                    </a>
                  ) : (
                    <article key={item.id} className="learn-os-resource">
                      <strong>{item.title}</strong>
                      <p>{item.summary}</p>
                    </article>
                  )
                ))}
              </div>
            </section>
            <section className="learn-os-resource-block">
              <h3>Practical lesson</h3>
              <div className="learn-os-resource-list">
                {resourceBundle.practical.map((item) => (
                  <article key={item.id} className="learn-os-resource">
                    <strong>{item.title}</strong>
                    <button
                      type="button"
                      className="learn-os-btn learn-os-btn--ghost"
                      onClick={() => runPracticalCta(item.ctaType)}
                    >
                      {item.ctaLabel}
                    </button>
                  </article>
                ))}
              </div>
            </section>
          </article>

          {contextCards.length ? (
            <article className="learn-os-card">
              <header className="learn-os-card__head">
                <div>
                  <p className="learn-os-eyebrow">Context-aware explainers</p>
                  <h2>Học theo ngữ cảnh bạn đang xem</h2>
                </div>
              </header>
              <ul className="learn-os-context-list">
                {contextCards.map((item) => (
                  <li key={item.trigger}>
                    <strong>{item.recommended_lesson_title}</strong>
                    <p>{item.reason}</p>
                    <div className="learn-os-inline-actions">
                      {onOpenGuidedInvesting ? (
                        <button
                          type="button"
                          className="learn-os-btn learn-os-btn--ghost"
                          onClick={() => onOpenGuidedInvesting(item.trigger === 'drawdown' ? 'market_context' : 'watchlist')}
                        >
                          Mở card liên quan
                        </button>
                      ) : null}
                      {onOpenCommunity ? (
                        <button
                          type="button"
                          className="learn-os-btn learn-os-btn--ghost"
                          onClick={() => onOpenCommunity(item.trigger === 'drawdown' ? 'risk-literacy-circle' : 'company-case-room')}
                        >
                          Mở thảo luận
                        </button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            </article>
          ) : null}
        </div>
      </section>

      <section className="learn-os-tutor-full learn-reveal" aria-label="Hỏi Tutor">
        <header className="learn-os-card__head">
          <div>
            <p className="learn-os-eyebrow">Tutor AI</p>
            <h2>Hỏi gì về tài chính cũng được</h2>
            <p>Tutor sẽ trả lời dựa trên bài học hiện tại + lộ trình cá nhân.</p>
          </div>
        </header>

        <div className="learn-os-tutor-thread">
          {tutorThread.length === 0 ? (
            <p className="learn-os-muted">Chưa có câu hỏi. Gõ bên dưới để bắt đầu.</p>
          ) : tutorThread.map((entry, index) => (
            <article key={index} className={`learn-os-tutor-entry is-${entry.role}`}>
              <strong>{entry.role === 'user' ? 'Bạn' : 'Tutor'}</strong>
              <p>{entry.text}</p>
              {entry.check ? <small>Câu hỏi kiểm tra: {entry.check}</small> : null}
            </article>
          ))}
        </div>

        <div className="learn-os-prompt-list">
          {LEARN_QUICK_PROMPTS.map((prompt) => (
            <button key={prompt} type="button" className="learn-os-option" onClick={() => applyPrompt(prompt)}>
              {prompt}
            </button>
          ))}
        </div>

        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={3}
          placeholder="Đặt câu hỏi cho Tutor…"
        />
        <div className="learn-os-inline-actions">
          <button
            type="button"
            className="learn-os-btn learn-os-btn--primary"
            onClick={async () => {
              if (!question.trim() || !lesson) return
              const userText = question.trim()
              setTutorThread((current) => [...current, { role: 'user', text: userText }])
              setQuestion('')
              try {
                const payload = await askTutorMutation.mutateAsync({
                  sessionId,
                  lessonId: lesson.lesson_id,
                  question: userText,
                })
                setTutorThread((current) => [...current, {
                  role: 'tutor',
                  text: `${payload.summary}\n\n${payload.explanation}`,
                  check: payload.check_question,
                }])
              } catch (err) {
                setTutorThread((current) => [...current, { role: 'tutor', text: `Lỗi: ${err.message}` }])
              }
            }}
            disabled={askingTutor || !lesson}
          >
            {askingTutor ? 'Tutor đang trả lời…' : 'Gửi câu hỏi'}
          </button>
          <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={() => setTutorThread([])}>
            Xoá hội thoại
          </button>
        </div>
      </section>

      <footer className="learn-os-footer-note learn-reveal">
        <p>
          Learn Hub ưu tiên giáo dục và quản trị rủi ro. Nội dung không phải khuyến nghị mua/bán cá nhân hóa.
        </p>
        <div>
          {onOpenAdmin ? (
            <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={onOpenAdmin}>
              Mở Content Ops
            </button>
          ) : null}
        </div>
      </footer>

      <FloatingAssistant sessionId={sessionId} surface="learning" surfaceLabel="Learn Hub" />
    </section>
  )
}

function useLearnDashboardMotion(isReady, activeView) {
  // Disabled motion observer to prevent white screen issues.
  // The CSS default opacity is 1, so without adding 'is-motion-ready', 
  // the content will just appear normally without the scroll reveal animation.
  useEffect(() => {
    // If the class was left over from a previous render, clean it up
    const root = document.querySelector('.learn-os-page')
    if (root) {
      root.classList.remove('is-motion-ready')
      const items = Array.from(root.querySelectorAll('.learn-reveal'))
      items.forEach((item) => item.classList.add('is-visible'))
    }
  }, [isReady, activeView])
}

function BookReaderWorkspace({ book, sessionId, onClose, asPage = false }) {
  const noteTextareaRef = useRef(null)
  const uploadInputRef = useRef(null)
  const pageElementRefs = useRef(new Map())
  const pageBadgeTimerRef = useRef(null)

  const [pages, setPages] = useState(() => [createNotebookPage({ title: 'Trang 1' })])
  const [activePageId, setActivePageId] = useState('')
  const [scrollTargetPageId, setScrollTargetPageId] = useState('')
  const [visiblePageBadgeId, setVisiblePageBadgeId] = useState('')
  const [savedAt, setSavedAt] = useState('')
  const [editorMode, setEditorMode] = useState('type')
  const [drawColor, setDrawColor] = useState('#0b5a50')
  const [drawSize, setDrawSize] = useState(2.2)
  const [eraserSize, setEraserSize] = useState(32)

  const resolvedActivePageId = activePageId || pages[0]?.id || ''
  const activePageIndex = pages.findIndex((page) => page.id === resolvedActivePageId)
  const activePage = activePageIndex >= 0 ? pages[activePageIndex] : pages[0] || null

  useEffect(() => {
    document.body.classList.add('learn-reader-active')
    return () => document.body.classList.remove('learn-reader-active')
  }, [])

  useEffect(() => {
    const storageKey = readerStorageKey(sessionId, book.asset_id)
    const payload = safeJsonParse(window.localStorage.getItem(storageKey) || '')
    const hydratedPages = hydrateNotebookPages(payload)
    const nextPages = hydratedPages.length ? hydratedPages : [createNotebookPage({ title: 'Trang 1' })]
    const nextActivePageId = nextPages.some((page) => page.id === payload?.activePageId)
      ? payload.activePageId
      : nextPages[0].id
    setPages(nextPages)
    setActivePageId(nextActivePageId)
    setSavedAt(typeof payload?.savedAt === 'string' ? payload.savedAt : '')
    setEditorMode('type')
  }, [book.asset_id, sessionId])

  useEffect(() => {
    if (!pages.length) return
    if (!activePageId || !pages.some((page) => page.id === activePageId)) {
      setActivePageId(pages[0].id)
    }
  }, [activePageId, pages])

  useEffect(() => {
    if (!scrollTargetPageId) return
    window.requestAnimationFrame(() => {
      pageElementRefs.current.get(scrollTargetPageId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setScrollTargetPageId('')
    })
  }, [scrollTargetPageId])

  useEffect(() => () => {
    if (pageBadgeTimerRef.current) window.clearTimeout(pageBadgeTimerRef.current)
  }, [])

  function revealPageBadge(pageId) {
    if (!pageId) return
    if (pageBadgeTimerRef.current) window.clearTimeout(pageBadgeTimerRef.current)
    setVisiblePageBadgeId(pageId)
    pageBadgeTimerRef.current = window.setTimeout(() => {
      setVisiblePageBadgeId('')
      pageBadgeTimerRef.current = null
    }, 2000)
  }

  function updateActivePage(patch) {
    if (!resolvedActivePageId) return
    setPages((current) => current.map((page) => {
      if (page.id !== resolvedActivePageId) return page
      const nextPatch = typeof patch === 'function' ? patch(page) : patch
      return {
        ...page,
        ...nextPatch,
        updatedAt: new Date().toISOString(),
      }
    }))
  }

  function syncCanvasInto(pageId) {
    if (!pageId) return
  }

  async function pasteImagesFromClipboard(event, pageId = resolvedActivePageId) {
    const items = Array.from(event.clipboardData?.items || [])
    const files = items
      .filter((item) => item.type.startsWith('image/'))
      .map((item) => item.getAsFile())
      .filter(Boolean)
    if (!files.length) return
    event.preventDefault()
    const next = await Promise.all(files.map(fileToDataUrl))
    const normalized = next.filter(Boolean)
    if (!normalized.length) return
    appendInlineImages(pageId, normalized)
  }

  useEffect(() => {
    function handleWindowPaste(event) {
      const target = event.target
      if (target?.tagName === 'TEXTAREA') return
      pasteImagesFromClipboard(event)
    }

    window.addEventListener('paste', handleWindowPaste)
    return () => window.removeEventListener('paste', handleWindowPaste)
    // pasteImagesFromClipboard closes over the active page id through the dependency above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedActivePageId])

  function appendInlineImages(pageId, srcList) {
    updatePageById(pageId || resolvedActivePageId, (page) => {
      const existing = normalizeNoteImages(page.images)
      const nextImages = srcList.map((src, index) => createNoteImage(src, existing.length + index))
      return { images: [...existing, ...nextImages] }
    })
  }

  async function handleImageUpload(event) {
    const files = Array.from(event.target.files || [])
    if (!files.length) return
    const next = await Promise.all(files.map(fileToDataUrl))
    const normalized = next.filter(Boolean)
    if (!normalized.length) return
    appendInlineImages(resolvedActivePageId, normalized)
    event.target.value = ''
  }

  function updatePageById(pageId, patch) {
    if (!pageId) return
    setPages((current) => current.map((page) => {
      if (page.id !== pageId) return page
      const nextPatch = typeof patch === 'function' ? patch(page) : patch
      return {
        ...page,
        ...nextPatch,
        updatedAt: new Date().toISOString(),
      }
    }))
  }

  function updateImageAt(pageId, index, patch) {
    updatePageById(pageId, (page) => {
      const images = normalizeNoteImages(page.images)
      return {
        images: images.map((image, idx) => (idx === index ? { ...image, ...patch } : image)),
      }
    })
  }

  function removeImageFromPage(pageId, index) {
    updatePageById(pageId, (page) => ({ images: normalizeNoteImages(page.images).filter((_, idx) => idx !== index) }))
  }

  function clearDrawing() {
    updatePageById(resolvedActivePageId, { drawingDataUrl: '' })
  }

  function handleSelectPage(pageId) {
    if (!pageId || pageId === resolvedActivePageId) return
    setActivePageId(pageId)
    setScrollTargetPageId(pageId)
    setEditorMode('type')
  }

  function handleAddPage() {
    syncCanvasInto(resolvedActivePageId)
    let createdId = ''
    setPages((current) => {
      const createdPage = createNotebookPage({ title: `Trang ${current.length + 1}` })
      createdId = createdPage.id
      const currentIndex = current.findIndex((page) => page.id === resolvedActivePageId)
      if (currentIndex < 0) return [...current, createdPage]
      const next = [...current]
      next.splice(currentIndex + 1, 0, createdPage)
      return next
    })
    if (createdId) setActivePageId(createdId)
    if (createdId) setScrollTargetPageId(createdId)
    if (createdId) revealPageBadge(createdId)
    setEditorMode('type')
  }

  function saveReaderState() {
    const storageKey = readerStorageKey(sessionId, book.asset_id)
    const savedIso = new Date().toISOString()
    const activeId = resolvedActivePageId || pages[0]?.id || ''
    const pagesToSave = (pages.length ? pages : [createNotebookPage({ title: 'Trang 1' })]).map((page) => (
      page.id === activeId ? { ...page, updatedAt: savedIso } : page
    ))
    const activeForExport = pagesToSave.find((page) => page.id === activeId) || pagesToSave[0]
    const payload = {
      pages: pagesToSave,
      activePageId: activeForExport?.id || '',
      noteHtml: composeNoteHtml(activeForExport?.noteText || '', activeForExport?.images || []),
      noteText: activeForExport?.noteText || '',
      images: activeForExport?.images || [],
      drawingDataUrl: activeForExport?.drawingDataUrl || '',
      savedAt: savedIso,
    }
    window.localStorage.setItem(storageKey, JSON.stringify(payload))
    setPages(pagesToSave)
    setSavedAt(savedIso)
  }

  function closeAndPersist() {
    saveReaderState()
    onClose()
  }

  function switchMode(nextMode) {
    setEditorMode(nextMode)
    if (nextMode === 'draw' || nextMode === 'erase') {
      noteTextareaRef.current?.blur()
      return
    }
    window.setTimeout(() => {
      noteTextareaRef.current?.focus()
    }, 0)
  }

  const canInlinePdf = /\.pdf$/i.test(book.file_name || '')
  const pdfBookModeUrl = canInlinePdf
    ? `${book.url}#toolbar=0&navpanes=0&statusbar=0&messages=0&page=1&view=FitH&zoom=page-width`
    : book.url
  const toolbarButtonClass = 'learn-reader-toolbar-button'
  const activeToolbarButtonClass = 'learn-reader-toolbar-button learn-reader-toolbar-button--active'

  return (
    <div className={`learn-reader-shell fixed inset-0 ${asPage ? 'z-[120]' : 'z-[120]'} bg-slate-100`}>
      {!asPage ? <div className="absolute inset-0 bg-black/70 backdrop-blur-[6px]" onClick={closeAndPersist} /> : null}
      <div className="learn-reader-frame relative flex h-full min-h-0 flex-col overflow-hidden bg-slate-100 text-slate-900">
        <header className="flex h-10 shrink-0 items-center justify-between gap-3 border-b border-slate-300 bg-white px-3">
          <div className="flex min-w-0 items-center gap-3">
            <strong className="truncate text-sm font-semibold text-slate-900">{book.title}</strong>
            <span className="rounded border border-slate-300 bg-slate-50 px-2 py-0.5 text-[0.66rem] font-semibold uppercase tracking-[0.08em] text-slate-500">
              {activePage ? `Note ${activePageIndex + 1}/${pages.length}` : 'Note'}
            </span>
          </div>
          <div className="learn-reader-toolbar">
            <button type="button" className={toolbarButtonClass} onClick={handleAddPage} title="Thêm trang">
              <span aria-hidden="true">+</span>
              <span className="ml-1">Trang</span>
            </button>
            <button type="button" className={toolbarButtonClass} onClick={() => uploadInputRef.current?.click()} title="Chèn ảnh">
              <span aria-hidden="true">□</span>
              <span className="ml-1">Ảnh</span>
            </button>
            <button type="button" className={toolbarButtonClass} onClick={clearDrawing} title="Xóa nét vẽ">
              <span aria-hidden="true">⌫</span>
            </button>
            <button
              type="button"
              className={editorMode === 'type' ? activeToolbarButtonClass : toolbarButtonClass}
              onClick={() => switchMode('type')}
              title="Gõ chữ"
            >
              <span aria-hidden="true">T</span>
            </button>
            <button
              type="button"
              className={editorMode === 'draw' ? activeToolbarButtonClass : toolbarButtonClass}
              onClick={() => switchMode('draw')}
              title="Bút vẽ"
            >
              <span aria-hidden="true">✎</span>
            </button>
            <button
              type="button"
              className={editorMode === 'erase' ? activeToolbarButtonClass : toolbarButtonClass}
              onClick={() => switchMode('erase')}
              title="Tẩy nét vẽ"
            >
              <span aria-hidden="true">Tẩy</span>
            </button>
            <label className="learn-reader-control" title="Kích thước tẩy">
              <span aria-hidden="true">Tẩy</span>
              <input
                type="range"
                className="learn-reader-range learn-reader-range--eraser"
                min={8}
                max={96}
                step={2}
                value={eraserSize}
                onChange={(event) => setEraserSize(Number(event.target.value))}
                aria-label="Kích thước tẩy"
              />
            </label>
            <label className="learn-reader-control">
              <span aria-hidden="true">●</span>
              <input className="learn-reader-color" type="color" value={drawColor} onChange={(event) => setDrawColor(event.target.value)} />
            </label>
            <label className="learn-reader-control">
              <span aria-hidden="true">—</span>
              <input
                type="range"
                className="learn-reader-range"
                min={1}
                max={12}
                step={0.5}
                value={drawSize}
                onChange={(event) => setDrawSize(Number(event.target.value))}
              />
            </label>
            <button type="button" className={toolbarButtonClass} onClick={saveReaderState}>Lưu</button>
            {asPage ? (
              <button type="button" className={toolbarButtonClass} onClick={closeAndPersist}>Learn</button>
            ) : null}
            <button type="button" className={activeToolbarButtonClass} onClick={closeAndPersist}>Đóng</button>
          </div>
        </header>

        <div className="learn-reader-main grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-2">
          <section className="learn-reader-book-pane min-h-0 overflow-hidden border-r border-slate-300 bg-white">
            {canInlinePdf ? (
              <object data={pdfBookModeUrl} type="application/pdf" aria-label={book.title} className="h-full w-full bg-white">
                <iframe className="h-full w-full border-0" src={pdfBookModeUrl} title={book.title} />
              </object>
            ) : (
              <div className="grid h-full place-content-center justify-items-center gap-3 text-center">
                <p className="text-sm text-slate-600">Định dạng này chưa hỗ trợ xem trực tiếp trong app.</p>
                <a className={activeToolbarButtonClass} href={book.url} target="_blank" rel="noreferrer">
                  Mở file ở tab mới
                </a>
              </div>
            )}
          </section>

          <aside className="learn-reader-note-pane flex min-h-0 flex-col overflow-hidden bg-white">
            <div className="flex h-10 shrink-0 items-center gap-2 border-b border-slate-200 bg-slate-50 px-3">
              <label className="learn-reader-page-picker">
                <span>Trang</span>
                <select
                  className="learn-reader-select"
                  value={resolvedActivePageId}
                  onChange={(event) => handleSelectPage(event.target.value)}
                  aria-label="Chọn trang ghi chú"
                >
                  {pages.map((page, index) => (
                    <option key={page.id} value={page.id}>
                      {page.title || `Trang ${index + 1}`}
                    </option>
                  ))}
                </select>
              </label>
              <input
                type="text"
                className="learn-reader-title-input"
                value={activePage?.title || ''}
                onChange={(event) => updateActivePage({ title: event.target.value })}
                placeholder={`Trang ${Math.max(activePageIndex + 1, 1)}`}
                aria-label="Tên trang ghi chú hiện tại"
              />
            </div>

            <input
              ref={uploadInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="hidden"
            />

            <div className="learn-reader-note-scroll min-h-0 flex-1 overflow-y-auto bg-slate-100 p-4 pb-0 [scrollbar-width:thin]">
              <div className="mx-auto grid w-full max-w-[900px] gap-8">
                {pages.map((page, index) => (
                  <NotePaper
                    key={page.id}
                    page={page}
                    pageIndex={index}
                    isActive={page.id === resolvedActivePageId}
                    showPageLabel={page.id === visiblePageBadgeId}
                    editorMode={editorMode}
                    drawColor={drawColor}
                    drawSize={drawSize}
                    eraserSize={eraserSize}
                    setPageRef={(node) => {
                      if (node) pageElementRefs.current.set(page.id, node)
                      else pageElementRefs.current.delete(page.id)
                    }}
                    onActivate={() => setActivePageId(page.id)}
                    onTextChange={(noteText) => updatePageById(page.id, { noteText })}
                    onDrawingChange={(drawingDataUrl) => updatePageById(page.id, { drawingDataUrl })}
                    onImageChange={(imageIndex, patch) => updateImageAt(page.id, imageIndex, patch)}
                    onImageRemove={(imageIndex) => removeImageFromPage(page.id, imageIndex)}
                    onPaste={(event) => pasteImagesFromClipboard(event, page.id)}
                    onTypeMode={() => setEditorMode('type')}
                  />
                ))}
              </div>

              <div className="mx-auto mt-3 flex w-full max-w-[900px] items-center justify-between gap-3">
                <button type="button" className={toolbarButtonClass} onClick={handleAddPage}>+ Trang mới</button>
                <small className="text-[0.72rem] text-slate-500">{savedAt ? `Lần lưu gần nhất: ${new Date(savedAt).toLocaleString('vi-VN')}` : 'Chưa lưu.'}</small>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

function NotePaper({
  page,
  pageIndex,
  isActive,
  showPageLabel,
  editorMode,
  drawColor,
  drawSize,
  eraserSize,
  setPageRef,
  onActivate,
  onTextChange,
  onDrawingChange,
  onImageChange,
  onImageRemove,
  onPaste,
  onTypeMode,
}) {
  const canvasRef = useRef(null)
  const pointerStateRef = useRef({ drawing: false, x: 0, y: 0 })
  const imageDragRef = useRef(null)
  const images = normalizeNoteImages(page.images)

  useEffect(() => {
    drawPersistedCanvas(page.drawingDataUrl || null, canvasRef.current)
  }, [page.drawingDataUrl, page.id])

  function snapshotCanvas() {
    return canvasRef.current?.toDataURL('image/png') || ''
  }

  function pointerDown(event) {
    onActivate()
    if (!['draw', 'erase'].includes(editorMode) || !canvasRef.current) return
    event.preventDefault()
    const { x, y } = pointerPosition(event, canvasRef.current)
    pointerStateRef.current = { drawing: true, x, y }
    if (typeof event.currentTarget?.setPointerCapture === 'function') {
      event.currentTarget.setPointerCapture(event.pointerId)
    }
  }

  function pointerMove(event) {
    if (!['draw', 'erase'].includes(editorMode)) return
    const state = pointerStateRef.current
    const canvas = canvasRef.current
    if (!state.drawing || !canvas) return
    event.preventDefault()
    const context = canvas.getContext('2d')
    if (!context) return
    const next = pointerPosition(event, canvas)
    context.save()
    context.globalCompositeOperation = editorMode === 'erase' ? 'destination-out' : 'source-over'
    context.strokeStyle = editorMode === 'erase' ? 'rgba(0,0,0,1)' : drawColor
    context.lineWidth = editorMode === 'erase' ? eraserSize : drawSize
    context.lineCap = 'round'
    context.lineJoin = 'round'
    context.beginPath()
    context.moveTo(state.x, state.y)
    context.lineTo(next.x, next.y)
    context.stroke()
    context.restore()
    pointerStateRef.current = { drawing: true, x: next.x, y: next.y }
  }

  function pointerUp() {
    if (pointerStateRef.current.drawing) {
      onDrawingChange(snapshotCanvas())
    }
    pointerStateRef.current = { drawing: false, x: 0, y: 0 }
  }

  function imagePointerDown(event, index, mode = 'move') {
    event.preventDefault()
    event.stopPropagation()
    onActivate()
    const pageRect = event.currentTarget.closest('[data-note-paper]')?.getBoundingClientRect()
    const image = images[index]
    if (!pageRect || !image) return
    imageDragRef.current = {
      index,
      mode,
      startClientX: event.clientX,
      startClientY: event.clientY,
      startX: image.x,
      startY: image.y,
      startWidth: image.width,
      pageWidth: pageRect.width,
    }
    if (typeof event.currentTarget?.setPointerCapture === 'function') {
      event.currentTarget.setPointerCapture(event.pointerId)
    }
  }

  function imagePointerMove(event) {
    const drag = imageDragRef.current
    if (!drag) return
    event.preventDefault()
    const deltaX = event.clientX - drag.startClientX
    const deltaY = event.clientY - drag.startClientY
    if (drag.mode === 'resize') {
      onImageChange(drag.index, {
        width: Math.round(Math.min(720, Math.max(96, drag.startWidth + deltaX))),
      })
      return
    }
    const nextX = drag.startX + (deltaX / Math.max(drag.pageWidth, 1)) * 100
    onImageChange(drag.index, {
      x: Math.round(Math.min(82, Math.max(0, nextX)) * 10) / 10,
      y: Math.round(Math.min(1500, Math.max(0, drag.startY + deltaY))),
    })
  }

  function imagePointerUp() {
    imageDragRef.current = null
  }

  return (
    <section
      ref={setPageRef}
      data-note-paper
      className={`relative min-h-[calc(100vh-9.5rem)] w-full overflow-hidden rounded-sm border bg-white shadow-sm ${isActive ? 'border-teal-600 ring-2 ring-teal-500/20' : 'border-slate-300'}`}
      onPointerDown={onActivate}
    >
      {showPageLabel ? (
        <span className="absolute left-3 top-2 z-[4] rounded border border-slate-200 bg-white/90 px-1.5 py-0.5 text-[0.62rem] font-semibold uppercase tracking-[0.08em] text-slate-400">
          Trang {pageIndex + 1}
        </span>
      ) : null}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 z-[1] h-full w-full touch-none bg-transparent opacity-100 ${['draw', 'erase'].includes(editorMode) && isActive ? 'pointer-events-auto cursor-crosshair' : 'pointer-events-none'}`}
        width={960}
        height={1400}
        onPointerDown={pointerDown}
        onPointerMove={pointerMove}
        onPointerUp={pointerUp}
        onPointerLeave={pointerUp}
        onPointerCancel={pointerUp}
      />
      <textarea
        className={`relative z-[2] min-h-[calc(100vh-9.5rem)] w-full resize-none border-0 !bg-transparent px-12 py-10 text-base leading-8 text-slate-900 caret-teal-700 outline-none placeholder:text-slate-400 ${['draw', 'erase'].includes(editorMode) && isActive ? 'pointer-events-none select-none' : 'pointer-events-auto'}`}
        value={page.noteText || ''}
        onChange={(event) => onTextChange(event.target.value)}
        onPaste={onPaste}
        onFocus={() => {
          onActivate()
          onTypeMode()
        }}
        spellCheck={false}
        style={{ backgroundColor: 'transparent', color: '#0f172a', WebkitTextFillColor: '#0f172a' }}
        placeholder="Viết ghi chú..."
      />
      {images.map((image, index) => (
        <figure
          key={`${image.src}-${index}`}
          className="group absolute z-[3] m-0 overflow-hidden rounded border border-slate-300 bg-white shadow-sm"
          style={{
            left: `${image.x}%`,
            top: `${image.y}px`,
            width: `${image.width}px`,
          }}
          onPointerDown={(event) => imagePointerDown(event, index, 'move')}
          onPointerMove={imagePointerMove}
          onPointerUp={imagePointerUp}
          onPointerCancel={imagePointerUp}
          onPointerLeave={imagePointerUp}
        >
          <img className="block h-auto w-full object-contain" src={image.src} alt={`note-image-${index + 1}`} />
          <button
            type="button"
            className="absolute right-1 top-1 hidden min-h-0 rounded bg-white/90 px-1.5 py-0.5 text-[0.65rem] font-semibold text-slate-700 shadow-none group-hover:inline-flex"
            onClick={() => onImageRemove(index)}
            aria-label={`Xóa ảnh ${index + 1}`}
          >
            x
          </button>
          <span
            className="absolute bottom-1 right-1 hidden h-4 w-4 cursor-nwse-resize rounded-sm border border-teal-700 bg-white/90 group-hover:block"
            onPointerDown={(event) => imagePointerDown(event, index, 'resize')}
            aria-hidden="true"
          />
        </figure>
      ))}
    </section>
  )
}

function readerStorageKey(sessionId, assetId) {
  return `learn-reader:${sessionId}:${assetId}`
}

function createNotebookPage(seed = {}) {
  const uniqueId = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    ? crypto.randomUUID()
    : `page-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const normalizedImages = normalizeNoteImages(seed.images)
  return {
    id: typeof seed.id === 'string' && seed.id ? seed.id : uniqueId,
    title: typeof seed.title === 'string' && seed.title.trim() ? seed.title.trim() : '',
    noteText: typeof seed.noteText === 'string' ? seed.noteText : '',
    images: normalizedImages,
    drawingDataUrl: typeof seed.drawingDataUrl === 'string' && seed.drawingDataUrl.startsWith('data:image/')
      ? seed.drawingDataUrl
      : '',
    updatedAt: typeof seed.updatedAt === 'string' ? seed.updatedAt : new Date().toISOString(),
  }
}

function hydrateNotebookPages(payload) {
  if (Array.isArray(payload?.pages) && payload.pages.length) {
    return payload.pages.map((page, index) => createNotebookPage({
      id: page?.id,
      title: page?.title || `Trang ${index + 1}`,
      noteText: page?.noteText,
      images: page?.images,
      drawingDataUrl: page?.drawingDataUrl,
      updatedAt: page?.updatedAt,
    }))
  }

  const legacyText = typeof payload?.noteText === 'string'
    ? payload.noteText
    : extractPlainTextFromHtml(payload?.noteHtml || '')
  const legacyImages = Array.isArray(payload?.images)
    ? normalizeNoteImages(payload.images)
    : extractImagesFromHtml(payload?.noteHtml || '')
  const legacyDrawing = typeof payload?.drawingDataUrl === 'string' ? payload.drawingDataUrl : ''
  return [createNotebookPage({
    title: 'Trang 1',
    noteText: legacyText,
    images: legacyImages,
    drawingDataUrl: legacyDrawing,
    updatedAt: payload?.savedAt,
  })]
}

function safeJsonParse(value) {
  if (!value) return null
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function drawPersistedCanvas(dataUrl, canvas) {
  if (!canvas) return
  const context = canvas.getContext('2d')
  if (!context) return
  context.clearRect(0, 0, canvas.width, canvas.height)
  if (!dataUrl) return
  const image = new Image()
  image.onload = () => {
    context.clearRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
  }
  image.src = dataUrl
}

function pointerPosition(event, canvas) {
  const rect = canvas.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * canvas.width
  const y = ((event.clientY - rect.top) / rect.height) * canvas.height
  return { x, y }
}

async function fileToDataUrl(file) {
  if (!file) return ''
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
    reader.onerror = () => reject(new Error('Không đọc được ảnh'))
    reader.readAsDataURL(file)
  })
}

function filterAssetsByType(items, targetType) {
  return (items || []).filter((item) => {
    const mime = String(item?.mime_type || '').toLowerCase()
    const extension = fileExtension(item?.file_name)
    if (targetType === 'video') return mime.startsWith('video/') || VIDEO_EXTENSIONS.has(extension)
    if (targetType === 'audio') return mime.startsWith('audio/') || AUDIO_EXTENSIONS.has(extension)
    return true
  })
}

function dedupeAssetsById(items) {
  const map = new Map()
  ;(items || []).forEach((item) => {
    const key = item?.asset_id || item?.url || item?.file_name
    if (!key || map.has(key)) return
    map.set(key, item)
  })
  return Array.from(map.values())
}

function fileExtension(fileName) {
  const value = String(fileName || '')
  const index = value.lastIndexOf('.')
  if (index <= -1) return ''
  return value.slice(index + 1).toLowerCase()
}

function shortTitle(title, max = 32) {
  const value = String(title || '').trim()
  if (!value) return 'Untitled'
  if (value.length <= max) return value
  return `${value.slice(0, max - 1)}…`
}

function MediaCover({ item, variant }) {
  if (item.cover_url) {
    return <img className="learn-os-media-thumb" src={item.cover_url} alt={`Cover ${item.title}`} />
  }
  return (
    <div className={`learn-os-media-thumb learn-os-media-thumb--fallback ${variant === 'audio' ? 'is-audio' : 'is-video'}`}>
      <small>{variant === 'audio' ? 'AUDIO' : 'VIDEO'}</small>
      <strong>{shortTitle(item.title, 28)}</strong>
      <span>.{fileExtension(item.file_name) || 'file'}</span>
    </div>
  )
}

function BookCoverPreview({ item }) {
  if (item.cover_url) {
    return <img src={item.cover_url} alt={`Bìa ${item.title}`} />
  }
  const isPdf = /\.pdf$/i.test(item.file_name || '')
  if (isPdf) {
    return (
      <div className="learn-os-book-preview-pdf">
        <iframe
          src={`${item.url}#page=1&view=FitH&zoom=page-width`}
          title={`preview-${item.title}`}
          loading="lazy"
        />
      </div>
    )
  }
  return (
    <div className="learn-os-book-cover-fallback">
      <small>BOOK</small>
      <span>{shortTitle(item.title, 38)}</span>
    </div>
  )
}

function extractPlainTextFromHtml(html) {
  if (!html) return ''
  const container = document.createElement('div')
  container.innerHTML = html
  return container.textContent || ''
}

function extractImagesFromHtml(html) {
  if (!html) return []
  const container = document.createElement('div')
  container.innerHTML = html
  return Array.from(container.querySelectorAll('img'))
    .map((item) => item.getAttribute('src') || '')
    .filter((src) => src.startsWith('data:image/'))
    .map((src, index) => createNoteImage(src, index))
}

function composeNoteHtml(noteText, images) {
  const escaped = escapeHtml(noteText).replace(/\n/g, '<br>')
  const imageBlocks = normalizeNoteImages(images)
    .map((image) => `<p><img src="${image.src}" alt="note-image" /></p>`)
    .join('')
  return `<p>${escaped || ''}</p>${imageBlocks}`
}

function normalizeNoteImages(images) {
  if (!Array.isArray(images)) return []
  return images
    .map((item, index) => {
      if (typeof item === 'string' && item.startsWith('data:image/')) {
        return createNoteImage(item, index)
      }
      if (!item || typeof item !== 'object') return null
      const src = typeof item.src === 'string' ? item.src : ''
      if (!src.startsWith('data:image/')) return null
      return {
        src,
        x: clampNumber(item.x, 6, 70, 8 + (index % 3) * 8),
        y: clampNumber(item.y, 72, 1200, 112 + index * 28),
        width: clampNumber(item.width, 120, 520, 280),
      }
    })
    .filter(Boolean)
}

function createNoteImage(src, index = 0) {
  return {
    src,
    x: 8 + (index % 3) * 8,
    y: 112 + index * 32,
    width: 300,
  }
}

function clampNumber(value, min, max, fallback) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return fallback
  return Math.min(max, Math.max(min, numeric))
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function tierLabel(tier) {
  if (tier === 'financial_basics') return 'Financial basics'
  if (tier === 'basic_investing_literacy') return 'Investing literacy'
  if (tier === 'product_tool_literacy') return 'Tool literacy'
  return 'Foundation'
}

function contentTypeLabel(contentType) {
  if (contentType === 'micro_lesson') return 'Micro lesson'
  if (contentType === 'practical_tool_lesson') return 'Practical tool lesson'
  if (contentType === 'contextual_explainer') return 'Contextual explainer'
  return 'Guided lesson'
}

function kindLabel(kind) {
  if (kind === 'video') return 'Video'
  if (kind === 'book') return 'Sách'
  if (kind === 'paper') return 'Paper'
  if (kind === 'course') return 'Khoá học'
  return kind
}

function CatalogCard({ kind, item }) {
  const title = item.title || 'Untitled'
  const meta = []
  if (kind === 'video') {
    if (item.channel) meta.push(item.channel)
    if (item.duration_seconds) meta.push(`${Math.round(item.duration_seconds / 60)} phút`)
  } else if (kind === 'book') {
    if (item.author) meta.push(item.author)
    if (item.publication_year) meta.push(String(item.publication_year))
  } else if (kind === 'paper') {
    const authors = Array.isArray(item.authors) ? item.authors : []
    if (authors.length) meta.push(authors.slice(0, 2).join(', ') + (authors.length > 2 ? '…' : ''))
    if (item.category) meta.push(item.category)
  } else if (kind === 'course') {
    if (item.provider) meta.push(item.provider)
    if (item.instructor) meta.push(item.instructor)
  }
  meta.push((item.language || 'en').toUpperCase())

  const description = item.description || item.abstract || ''
  const thumbnail = item.thumbnail_url || item.cover_url || null
  const downloadUrl = item.pdf_url || item.download_url || ''

  const renderIcon = () => {
    if (kind === 'video') return <PlayIcon size={28} />
    if (kind === 'book') return <BookIcon size={28} />
    if (kind === 'paper') return <FileTextIcon size={28} />
    if (kind === 'course') return <TargetIcon size={28} />
    return <span>{kind.toUpperCase()}</span>
  }

  return (
    <article className={`learn-os-catalog-card is-${kind}`}>
      <div className="learn-os-catalog-card__thumb">
        {thumbnail ? (
          <img src={thumbnail} alt="" loading="lazy" />
        ) : (
          <div className="learn-os-catalog-card__icon-fallback">
            {renderIcon()}
          </div>
        )}
      </div>
      <div className="learn-os-catalog-card__body">
        <div className="learn-os-catalog-card__title-row">
          <strong>{title}</strong>
        </div>
        <div className="learn-os-catalog-card__meta-row">
          <span className={`learn-os-kind-badge tag-${kind}`}>{kindLabel(kind)}</span>
          <small className="learn-os-catalog-card__meta">{meta.join(' · ')}</small>
        </div>
        {description ? (
          <p className="learn-os-catalog-card__desc">
            {description.slice(0, 240)}{description.length > 240 ? '…' : ''}
          </p>
        ) : null}
      </div>
      <div className="learn-os-catalog-card__actions">
        <a className="learn-os-btn learn-os-btn--primary learn-os-catalog-btn" href={item.url} target="_blank" rel="noreferrer">
          Mở tài liệu
        </a>
        {downloadUrl ? (
          <a className="learn-os-btn learn-os-btn--ghost learn-os-catalog-btn" href={downloadUrl} target="_blank" rel="noreferrer">
            Tải PDF
          </a>
        ) : null}
      </div>
    </article>
  )
}

function StatusCard({ label, value, subtext }) {
  return (
    <article className="learn-os-status-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {subtext ? <small>{subtext}</small> : null}
    </article>
  )
}

function ActionCard({ title, detail, eta, actionLabel, onAction }) {
  return (
    <article className="learn-os-action-card">
      <h3>{title}</h3>
      <p>{detail}</p>
      <div className="learn-os-action-card__foot">
        <small>{eta}</small>
        <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={onAction}>
          {actionLabel}
        </button>
      </div>
    </article>
  )
}

function formatBytes(bytes) {
  const value = Number(bytes)
  if (!Number.isFinite(value) || value <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  const amount = value / (1024 ** index)
  return `${amount.toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

function buildRealResourceBundle({ lesson, videoAssets, audioAssets, bookAssets }) {
  const tier = lesson?.tier || ''
  const titleNeedle = normalizeSearchText(`${lesson?.title || ''} ${lesson?.summary || ''} ${tierLabel(tier)}`)
  const matchesLesson = (item) => {
    const haystack = normalizeSearchText(`${item.title || ''} ${item.file_name || ''}`)
    return titleNeedle.split(' ').some((token) => token.length > 3 && haystack.includes(token))
  }
  const videos = [...(videoAssets || []), ...(audioAssets || [])]
    .filter(matchesLesson)
    .slice(0, 3)
    .map((item) => ({
      id: item.asset_id,
      title: item.title,
      duration: `${formatBytes(item.size_bytes)} · ${fileExtension(item.file_name).toUpperCase()}`,
      href: item.url,
    }))
  const books = (bookAssets || [])
    .filter(matchesLesson)
    .slice(0, 3)
    .map((item) => ({
      id: item.asset_id,
      title: item.title,
      summary: `${item.file_name} · ${formatBytes(item.size_bytes)}`,
      href: item.url,
    }))
  return {
    videos,
    books,
    practical: buildPracticalActions(lesson),
  }
}

function normalizeSearchText(value) {
  return String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function buildPracticalActions(lesson) {
  if (!lesson) return []
  if (lesson.content_type === 'practical_tool_lesson' && lesson.lesson_id?.includes('goal')) {
    return [{ id: 'guided', title: 'Áp dụng bài học bằng cách đọc rủi ro trong BCTC.', ctaLabel: 'Mở Guided Investing', ctaType: 'guided_investing' }]
  }
  if (lesson.tier === 'product_tool_literacy') {
    return [{ id: 'insights', title: 'Xem dữ liệu trong app để nối bài học với bối cảnh thật.', ctaLabel: 'Mở Insights', ctaType: 'insights' }]
  }
  if (lesson.tier === 'basic_investing_literacy') {
    return [{ id: 'guided', title: 'Đọc rủi ro và drawdown bằng Guided Investing.', ctaLabel: 'Mở Guided Investing', ctaType: 'guided_investing' }]
  }
  return [{ id: 'guided', title: 'Dùng Guided Investing để nối bài học với dữ liệu doanh nghiệp.', ctaLabel: 'Mở Guided Investing', ctaType: 'guided_investing' }]
}

function buildLearningDashboard({ data, lesson, contextCards, videoAssets, audioAssets, bookAssets, resourceBundle }) {
  const completion = Math.max(0, data?.completion_pct || 0)
  const pathLessons = data?.path_lessons?.length ? data.path_lessons : []
  const courseRows = data?.courses?.length ? data.courses : []
  const metricRows = data?.stats?.length ? data.stats : []
  const topics = data?.topics?.length
    ? data.topics.map((topic, index) => ({
        label: topic.label,
        count: `${topic.course_count} courses · ${topic.lesson_count} lessons`,
        icon: topicIcon(topic.tier, index),
      }))
    : [{
        label: data?.path_label || 'Current Path',
        count: `${pathLessons.length || 0} lessons`,
        icon: <BookIcon size={22} />,
      }]
  const courseCards = courseRows.length
    ? courseRows.map((course, index) => ({
        title: course.title,
        meta: `${course.lesson_count} lessons · ${tierLabel(course.tier)}`,
        tag: 'Course',
        progress: course.progress_pct,
        tone: ['is-navy', 'is-emerald', 'is-purple', 'is-amber', 'is-paper'][index % 5],
        icon: topicIcon(course.tier, index, 34),
      }))
    : pathLessons.map((item, index) => ({
        title: item.title,
        meta: `${contentTypeLabel(item.content_type)} · ${item.estimated_minutes}m`,
        tag: item.status === 'completed' ? 'Done' : 'Lesson',
        progress: item.status === 'completed' ? 100 : item.is_next ? Math.max(10, completion) : 0,
        tone: ['is-navy', 'is-emerald', 'is-purple', 'is-amber', 'is-paper'][index % 5],
        icon: <BookIcon size={34} />,
      }))
  const recommended = [
    ...(lesson ? [{
      title: lesson.title,
      summary: lesson.summary,
      meta: `${contentTypeLabel(lesson.content_type)} · ${lesson.estimated_minutes}m`,
      score: lesson.progress_status === 'completed' ? 'Done' : 'Next',
      badge: shortBadge(lesson.title),
    }] : []),
    ...pathLessons
      .filter((item) => item.lesson_id !== lesson?.lesson_id)
      .slice(0, 2)
      .map((item) => ({
        title: item.title,
        summary: item.summary,
        meta: `${contentTypeLabel(item.content_type)} · ${item.estimated_minutes}m`,
        score: item.status === 'completed' ? 'Done' : 'Path',
        badge: shortBadge(item.title),
      })),
  ]
  const statGrid = metricRows.length
    ? metricRows.map((item) => ({ label: item.label, value: item.value, delta: item.detail || 'SQLite runtime' }))
    : [
        { label: 'Lessons Completed', value: `${data?.completed_lessons || 0}`, delta: 'Current path progress' },
        { label: 'Path Progress', value: `${completion}%`, delta: data?.path_label || 'Active path' },
      ]
  const readingLibrary = (bookAssets || []).slice(0, 4)
  const studyPlan = pathLessons.slice(0, 3).map((item) => ({
    lesson_id: item.lesson_id,
    task: item.status === 'completed' ? `Review: ${item.title}` : `Complete: ${item.title}`,
    sub: tierLabel(item.tier),
    time: `${item.estimated_minutes}m`,
    status: item.status,
  }))
  const completedCount = Number(metricRows.find((item) => item.metric_id === 'completed_lessons')?.value || data?.completed_lessons || 0)
  return {
    topics,
    courseCards,
    recommended,
    statGrid,
    readingLibrary,
    pathLessons,
    studyDays: nextSevenStudyDays(),
    studyWeekLabel: buildStudyWeekLabel(),
    studyPlan,
    pathSteps: [
      { id: 'foundations', title: 'Foundations', subtitle: 'Nền tảng tài chính', state: 'is-active' },
      { id: 'risk', title: 'Risk', subtitle: 'Quản trị rủi ro', state: completion >= 25 ? 'is-active' : 'is-idle' },
      { id: 'analysis', title: 'Analysis', subtitle: 'Ứng dụng dữ liệu', state: completion >= 50 ? 'is-active' : 'is-idle' },
      { id: 'investing', title: 'Investing', subtitle: 'Đầu tư cơ bản', state: completion >= 75 ? 'is-active' : 'is-idle' },
    ],
    stats: [
      { label: 'Learning Streak', value: `${Math.max(3, Math.round(completion / 2))} ngày`, subtext: 'Tuyệt vời! Hãy duy trì nhé!' },
      { label: 'Completed Lessons', value: `${data?.completed_lessons || 0} bài`, subtext: 'Trong tổng số lộ trình hiện tại' },
      { label: 'Current Path', value: data?.path_label || 'Financial Foundations', subtext: `Đã hoàn thành ${completion}%` },
      { label: 'Recommended Next', value: data?.next_lesson_title || 'Ngân sách là gì?', subtext: 'Bài học tiếp theo trong lộ trình' },
    ],
    trackRows: [
      { id: 'path-current', title: data?.path_label || 'Financial Foundations', subtitle: 'Nền tảng tài chính', progress: completion, status: 'Đang học' },
      { id: 'risk-market', title: 'Risk & Market Basics', subtitle: 'Rủi ro & thị trường cơ bản', progress: Math.max(8, Math.round(completion * 0.65)), status: 'Chưa bắt đầu' },
      { id: 'analysis-plan', title: 'Analysis Planning', subtitle: 'Lập kế hoạch đọc dữ liệu', progress: Math.max(0, completion - 12), status: 'Chưa bắt đầu' },
      { id: 'investing', title: 'Investing Basics', subtitle: 'Đầu tư cơ bản', progress: Math.max(0, completion - 24), status: 'Chưa bắt đầu' },
    ],
    learnToday: [
      { title: contextCards[0]?.recommended_lesson_title || 'Risk-on / Risk-off là gì?', summary: contextCards[0]?.reason || 'Hiểu cách thị trường dịch chuyển giữa các chế độ rủi ro.', meta: '5 phút • Dễ', ctaType: 'insights' },
      { title: 'Tỷ giá ảnh hưởng thế nào?', summary: contextCards[1]?.reason || 'Tìm hiểu tác động của tỷ giá đến doanh nghiệp và danh mục đầu tư.', meta: '6 phút • Dễ', ctaType: 'guided_investing' },
      { title: 'Lãi suất tác động ra sao?', summary: 'Hiểu cơ chế lãi suất và ảnh hưởng đến thị trường tài chính.', meta: '6 phút • Trung bình', ctaType: 'insights' },
    ],
    weeklyProgress: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((day, index) => {
      const minutes = 18 + ((completion + index * 8) % 25)
      return { day, minutes, height: Math.min(100, Math.round((minutes / 45) * 100)) }
    }),
    achievements: [
      ['First Step', `Hoàn thành ${completedCount} bài học`, completedCount > 0 ? 'Earned' : 'In progress', 'is-green'],
      ['Quiz Practice', metricRows.find((item) => item.metric_id === 'quiz_attempts')?.value || '0 attempts', 'SQLite', 'is-teal'],
      ['Study Time', metricRows.find((item) => item.metric_id === 'study_minutes')?.value || '0m', 'Runtime', 'is-amber'],
      ['Current Path', data?.path_label || 'Learning path', `${completion}%`, 'is-purple'],
    ],
    mediaCounts: {
      videos: videoAssets.length,
      audios: audioAssets.length,
      books: bookAssets.length,
    },
    resourceCounts: {
      videos: resourceBundle.videos.length,
      books: resourceBundle.books.length,
      practical: resourceBundle.practical.length,
    },
  }
}

function topicIcon(tier, index = 0, size = 22) {
  if (tier === 'financial_basics') return <PiggyBankIcon size={size} />
  if (tier === 'basic_investing_literacy') return <LineChartIcon size={size} />
  if (tier === 'product_tool_literacy') return <CalculatorIcon size={size} />
  return [<BookIcon size={size} />, <GlobeIcon size={size} />, <ShieldIcon size={size} />][index % 3]
}

function shortBadge(title) {
  const words = String(title || 'Lesson').split(/\s+/).filter(Boolean)
  return words.slice(0, 2).join('\n').toUpperCase()
}

function nextSevenStudyDays() {
  const formatter = new Intl.DateTimeFormat('vi-VN', { weekday: 'short', day: 'numeric' })
  const today = new Date()
  return Array.from({ length: 7 }, (_, index) => {
    const next = new Date(today)
    next.setDate(today.getDate() + index)
    return formatter.format(next)
  })
}

function buildStudyWeekLabel() {
  const today = new Date()
  const end = new Date(today)
  end.setDate(today.getDate() + 6)
  const fmt = new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit' })
  return `${fmt.format(today)} – ${fmt.format(end)}, ${today.getFullYear()}`
}
