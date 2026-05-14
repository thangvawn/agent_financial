import { useEffect, useMemo, useRef, useState } from 'react'

import {
  LEARN_QUICK_PROMPTS,
  askLearningTutor,
  completeLearningLesson,
  fetchLearningAssets,
  fetchLearningCoach,
  fetchLearningContext,
  fetchLearningLesson,
  getLessonResourceBundle,
  submitLearningQuiz,
  useLearningHome,
} from '../../modules/learning'
import { PlayIcon, BookIcon, HeadphonesIcon, TargetIcon, LightbulbIcon, PiggyBankIcon, CalculatorIcon, ScaleIcon, ShieldIcon, ShieldPlusIcon, PlantIcon, FlagIcon, LineChartIcon, PieChartIcon, FileTextIcon, FlameIcon, StarIcon, CheckCircleIcon, ClockIcon, ArrowRightIcon, BarChartIcon, TrendingUpIcon, GlobeIcon, PercentIcon } from '../../shared/Icons'
import './learning.css'

const VIDEO_EXTENSIONS = new Set(['mp4', 'webm', 'mov', 'm4v', 'avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'flv', '3gp'])
const AUDIO_EXTENSIONS = new Set(['mp3', 'wav', 'm4a', 'aac', 'ogg', 'oga', 'flac', 'opus'])

export default function LearningHomePage({
  sessionId,
  onBack,
  onOpenAdmin,
  onOpenGuidedInvesting,
  onOpenCommunity,
  onOpenGoals,
  onOpenFinancialHealth,
  onOpenInsights,
}) {
  const [refreshKey, setRefreshKey] = useState(0)
  const { data, isLoading, error } = useLearningHome(sessionId, refreshKey)
  const [lesson, setLesson] = useState(null)
  const [lessonLoading, setLessonLoading] = useState(false)
  const [lessonError, setLessonError] = useState('')
  const [quizResult, setQuizResult] = useState(null)
  const [tutor, setTutor] = useState(null)
  const [coach, setCoach] = useState(null)
  const [contextCards, setContextCards] = useState([])
  const [question, setQuestion] = useState('Tóm tắt bài này như cho người mới bắt đầu.')
  const [answers, setAnswers] = useState({})
  const [submittingQuiz, setSubmittingQuiz] = useState(false)
  const [completingLesson, setCompletingLesson] = useState(false)
  const [askingTutor, setAskingTutor] = useState(false)

  const [assetRefreshKey, setAssetRefreshKey] = useState(0)
  const [assetLoading, setAssetLoading] = useState(false)
  const [assetError, setAssetError] = useState('')
  const [videoAssets, setVideoAssets] = useState([])
  const [audioAssets, setAudioAssets] = useState([])
  const [bookAssets, setBookAssets] = useState([])
  const [activeBook, setActiveBook] = useState(null)

  const resourceBundle = useMemo(() => getLessonResourceBundle(lesson), [lesson])
  const completionText = useMemo(() => `${Math.max(0, data?.completion_pct || 0)}%`, [data?.completion_pct])
  const dashboard = useMemo(
    () => buildLearningDashboard({ data, lesson, contextCards, videoAssets, audioAssets, bookAssets, resourceBundle }),
    [audioAssets, bookAssets, contextCards, data, lesson, resourceBundle, videoAssets],
  )
  useLearnDashboardMotion()

  useEffect(() => {
    let cancelled = false

    async function run() {
      if (!data?.next_lesson_id || !sessionId) return
      setLessonLoading(true)
      setLessonError('')

      const [lessonResult, coachResult, drawdownContext, compoundContext] = await Promise.allSettled([
        fetchLearningLesson(sessionId, data.next_lesson_id),
        fetchLearningCoach(sessionId, 'continue_path'),
        fetchLearningContext('drawdown'),
        fetchLearningContext('compound_interest'),
      ])

      if (cancelled) return

      if (lessonResult.status === 'fulfilled') {
        setLesson(lessonResult.value)
        setQuizResult(null)
        setTutor(null)
        setAnswers({})
      } else {
        setLesson(null)
        setLessonError(lessonResult.reason?.message || 'Không tải được bài học tiếp theo.')
      }

      setCoach(coachResult.status === 'fulfilled' ? coachResult.value : null)

      const contexts = []
      if (drawdownContext.status === 'fulfilled') contexts.push(drawdownContext.value)
      if (compoundContext.status === 'fulfilled') contexts.push(compoundContext.value)
      setContextCards(contexts)
      setLessonLoading(false)
    }

    void run()
    return () => {
      cancelled = true
    }
  }, [data?.next_lesson_id, refreshKey, sessionId])

  useEffect(() => {
    let cancelled = false

    async function loadAssets() {
      if (!sessionId) return
      setAssetLoading(true)
      setAssetError('')
      const [videoResult, audioResult, bookResult] = await Promise.allSettled([
        fetchLearningAssets('videos'),
        fetchLearningAssets('audios'),
        fetchLearningAssets('books'),
      ])
      if (cancelled) return

      if (videoResult.status === 'fulfilled') {
        setVideoAssets(filterAssetsByType(videoResult.value.items || [], 'video'))
      } else {
        setVideoAssets([])
      }
      if (audioResult.status === 'fulfilled') {
        const audios = filterAssetsByType(audioResult.value.items || [], 'audio')
        setAudioAssets(dedupeAssetsById(audios))
      } else if (videoResult.status === 'fulfilled') {
        const fallbackAudios = filterAssetsByType(videoResult.value.items || [], 'audio')
        setAudioAssets(dedupeAssetsById(fallbackAudios))
      } else {
        setAudioAssets([])
      }
      if (bookResult.status === 'fulfilled') {
        setBookAssets(bookResult.value.items || [])
      } else {
        setBookAssets([])
      }

      if (videoResult.status === 'rejected' && audioResult.status === 'rejected' && bookResult.status === 'rejected') {
        setAssetError('Không tải được danh sách media local.')
      }
      setAssetLoading(false)
    }

    void loadAssets()
    return () => {
      cancelled = true
    }
  }, [assetRefreshKey, sessionId])

  async function handleQuizSubmit() {
    if (!lesson || submittingQuiz) return
    setSubmittingQuiz(true)
    setLessonError('')
    try {
      const payload = await submitLearningQuiz(sessionId, lesson.lesson_id, answers)
      setQuizResult(payload)
      setRefreshKey((current) => current + 1)
    } catch (err) {
      setLessonError(err.message)
    } finally {
      setSubmittingQuiz(false)
    }
  }

  async function handleComplete() {
    if (!lesson || completingLesson) return
    setCompletingLesson(true)
    setLessonError('')
    try {
      const payload = await completeLearningLesson(sessionId, lesson.lesson_id)
      setLesson(payload)
      setRefreshKey((current) => current + 1)
    } catch (err) {
      setLessonError(err.message)
    } finally {
      setCompletingLesson(false)
    }
  }

  async function handleTutor() {
    if (!lesson || askingTutor) return
    setAskingTutor(true)
    setLessonError('')
    try {
      const payload = await askLearningTutor(sessionId, lesson.lesson_id, question)
      setTutor(payload)
    } catch (err) {
      setLessonError(err.message)
    } finally {
      setAskingTutor(false)
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
    if (ctaType === 'financial_health' && onOpenFinancialHealth) {
      onOpenFinancialHealth()
      return
    }
    if (ctaType === 'goals' && onOpenGoals) {
      onOpenGoals('')
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
          <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={() => setRefreshKey((v) => v + 1)}>
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
    <section className="learn-os-page">
      <header className="learn-os-topbar">
        <div>
          <h1>Learn Hub</h1>
          <p>Explore financial knowledge. Learn at your pace. Master your future.</p>
        </div>
        <label className="learn-os-search">
          <span aria-hidden="true">⌕</span>
          <input type="search" placeholder="Search for courses, topics, books..." />
        </label>
        <div className="learn-os-topbar-actions">
          <button type="button" aria-label="Notifications">!</button>
          <button type="button" aria-label="Settings">⚙</button>
        </div>
      </header>

      <section className="learn-os-topic-carousel learn-reveal" aria-label="Explore topics">
        <header className="learn-os-section-title">
          <h2>Explore Topics</h2>
          <button type="button" onClick={() => setAssetRefreshKey((v) => v + 1)}>View all</button>
        </header>
        <div className="learn-os-topic-strip">
          {[
            { label: 'Microeconomics', count: '32 Courses', icon: <BarChartIcon size={22} /> },
            { label: 'Macroeconomics', count: '28 Courses', icon: <GlobeIcon size={22} /> },
            { label: 'CFA Program', count: '45 Courses', icon: <BookIcon size={22} /> },
            { label: 'Risk Management', count: '24 Courses', icon: <ShieldIcon size={22} /> },
            { label: 'Corporate Finance', count: '26 Courses', icon: <CalculatorIcon size={22} /> },
            { label: 'Investments', count: '30 Courses', icon: <PieChartIcon size={22} /> },
          ].map((topic, index) => (
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
            <strong>Your Learning Progress</strong>
          </header>
          <div className="learn-os-progress-card__body">
            <div className="learn-os-ring-wrap">
              <svg viewBox="0 0 36 36" className="learn-os-progress-ring">
                <path className="learn-os-progress-ring__bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path className="learn-os-progress-ring__value" strokeDasharray={`${data?.completion_pct || 12}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div>
                <strong>{completionText}</strong>
                <span>Overall Progress</span>
              </div>
            </div>
            <dl className="learn-os-progress-metrics">
              <div>
                <dt>Courses Enrolled</dt>
                <dd>{dashboard.stats[2].value}</dd>
              </div>
              <div>
                <dt>Completed</dt>
                <dd>{dashboard.stats[1].value}</dd>
              </div>
              <div>
                <dt>Study Streak</dt>
                <dd>{dashboard.stats[0].value}</dd>
              </div>
            </dl>
          </div>
        </article>

        <article className="learn-os-goal-card">
          <span>This Week's Goal</span>
          <strong>Learn 5 lessons</strong>
          <div className="learn-os-goal-line">
            <i style={{ width: `${Math.min(100, Math.max(24, (data?.completion_pct || 45) + 18))}%` }} />
          </div>
          <small>{Math.min(5, Math.max(1, Math.round((data?.completion_pct || 45) / 18)))} / 5 lessons</small>
          <blockquote>The beautiful thing about learning is that no one can take it away from you.</blockquote>
        </article>

        <article className="learn-os-activity-card">
          <header className="learn-os-activity-head">
            <strong>Your Activity</strong>
            <span>Less <i /> <i /> <i /> More</span>
          </header>
          <div className="learn-os-activity-grid" aria-hidden="true">
            {Array.from({ length: 49 }, (_, index) => (
              <span key={index} className={`is-${(index * 7 + Math.floor(index / 5)) % 5}`} />
            ))}
          </div>
          <div className="learn-os-activity-days">
            {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, index) => <span key={`${day}-${index}`}>{day}</span>)}
          </div>
        </article>
      </section>

      <section className="learn-os-continue learn-reveal">
        <header className="learn-os-section-title">
          <h2>Continue Learning</h2>
          <button type="button" onClick={() => document.getElementById('learn-lesson-card')?.scrollIntoView({ behavior: 'smooth' })}>View all</button>
        </header>
        <div className="learn-os-course-strip">
          {[
            { title: 'Microeconomics Basics', meta: 'Chapter 3: Supply and Demand', tag: 'Video', progress: 75, tone: 'is-navy', icon: <LineChartIcon size={34} /> },
            { title: 'Macroeconomics Overview', meta: 'Chapter 2: GDP & Economic Growth', tag: 'Course', progress: 40, tone: 'is-emerald', icon: <GlobeIcon size={34} /> },
            { title: 'CFA Level I - Quantitative Methods', meta: 'Reading 5: Time Value of Money', tag: 'Course', progress: 60, tone: 'is-purple', icon: <BookIcon size={34} /> },
            { title: 'Risk Management Fundamentals', meta: 'Chapter 1: Risk Concepts', tag: 'Video', progress: 20, tone: 'is-amber', icon: <ShieldIcon size={34} /> },
            { title: 'The Intelligent Investor', meta: 'by Benjamin Graham', tag: 'Book', progress: 33, tone: 'is-paper', icon: <FileTextIcon size={34} /> },
          ].map((item) => (
            <button key={item.title} type="button" className="learn-os-course-card" onClick={() => document.getElementById('learn-lesson-card')?.scrollIntoView({ behavior: 'smooth' })}>
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
            <h2>Recommended for You</h2>
            <button type="button" className="learn-os-link-btn" onClick={() => setRefreshKey((v) => v + 1)}>View all</button>
          </header>
          <div className="learn-os-recommended-list">
            <article className="learn-os-recommended-item">
              <div className="learn-os-recommended-item__thumb is-cover-dark">CREDIT<br />ANALYSIS</div>
              <div>
                <strong>Credit Analysis Essentials</strong>
                <p>Learn how to evaluate credit risk and make better lending decisions.</p>
              </div>
              <div className="learn-os-recommended-item__meta">
                <span>Course · Intermediate</span>
                <em>4.6</em>
              </div>
            </article>
            <article className="learn-os-recommended-item">
              <div className="learn-os-recommended-item__thumb is-cover-dark">FINANCIAL<br />MODELING</div>
              <div>
                <strong>Financial Modeling with Excel</strong>
                <p>Build robust financial models and forecast with confidence.</p>
              </div>
              <div className="learn-os-recommended-item__meta">
                <span>Course · Intermediate</span>
                <em>4.7</em>
              </div>
            </article>
          </div>
        </article>

        <article className="learn-os-card learn-os-card--stats">
          <header className="learn-os-card__head">
            <h2>Learning Statistics</h2>
            <span className="learn-os-chip-alt">This Month</span>
          </header>
          <div className="learn-os-stat-grid">
            {[
              ['Total Study Time', '48h 30m', '12% vs last month'],
              ['Lessons Completed', '86', '18% vs last month'],
              ['Quizzes Completed', '42', '20% vs last month'],
              ['Avg. Score', '78%', '8% vs last month'],
            ].map(([label, value, delta]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
                <small>{delta}</small>
              </div>
            ))}
          </div>
          <div className="learn-os-line-chart" aria-hidden="true">
            <svg viewBox="0 0 760 180" preserveAspectRatio="none">
              <path className="learn-os-line-chart__grid" d="M0 40H760 M0 90H760 M0 140H760" />
              <path className="learn-os-line-chart__fill" d="M0 130 C80 116 120 92 184 92 C240 92 244 122 300 114 C365 104 392 136 456 104 C532 66 552 24 620 78 C680 126 702 116 760 98 L760 180 L0 180 Z" />
              <path className="learn-os-line-chart__line" d="M0 130 C80 116 120 92 184 92 C240 92 244 122 300 114 C365 104 392 136 456 104 C532 66 552 24 620 78 C680 126 702 116 760 98" />
              {[0, 184, 300, 456, 560, 680, 760].map((x, index) => (
                <circle key={x} cx={x} cy={[130, 92, 114, 104, 38, 116, 98][index]} r="5" />
              ))}
            </svg>
            <div className="learn-os-chart-labels">
              {['May 1', 'May 8', 'May 15', 'May 22', 'May 29', 'May 31'].map((label) => <span key={label}>{label}</span>)}
            </div>
          </div>
        </article>
      </section>

      <section className="learn-os-dashboard-grid learn-os-dashboard-grid--bottom learn-reveal">
        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <h2>Reading Library</h2>
            <button type="button" className="learn-os-link-btn" onClick={() => setAssetRefreshKey((v) => v + 1)}>View all</button>
          </header>
          <div className="learn-os-reading-row">
            {[
              ['The Intelligent Investor', 'Benjamin Graham', 'Saved', 'is-cover-dark'],
              ['Security Analysis 6th Edition', 'Benjamin Graham', 'Reading', 'is-cover-dark'],
              ['Common Stocks and Uncommon Profits', 'Philip A. Fisher', 'Saved', 'is-cover-paper'],
              ["Poor Charlie's Almanack", 'Charlie Munger', 'Reading', 'is-cover-blue'],
            ].map(([title, author, state, tone]) => (
              <button key={title} type="button" className="learn-os-book-mini" onClick={() => setQuestion(`Tóm tắt sách ${title} cho sinh viên tài chính.`)}>
                <span className={tone}>{title.split(' ').slice(0, 2).join(' ')}</span>
                <strong>{title}</strong>
                <small>{author}</small>
                <em>{state}</em>
              </button>
            ))}
          </div>
        </article>

        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <h2>Upcoming Live Classes</h2>
            <button type="button" className="learn-os-link-btn" onClick={handleTutor}>View all</button>
          </header>
          <div className="learn-os-live-list">
            {[
              ['JUN 03', 'Understanding Interest Rates & Bond Pricing', 'Prof. David Lin', '07:00 PM'],
              ['JUN 07', 'Equity Valuation Methods', 'Maria Chen', '06:00 PM'],
              ['JUN 10', 'Portfolio Risk & Diversification', 'James Patel', '07:00 PM'],
            ].map(([date, title, teacher, time]) => (
              <button key={title} type="button" className="learn-os-live-row" onClick={() => setQuestion(`Chuẩn bị câu hỏi cho lớp ${title}.`)}>
                <span>{date}</span>
                <strong>{title}<small>{teacher} · Live Webinar</small></strong>
                <em>{time}</em>
                <b>Register</b>
              </button>
            ))}
          </div>
        </article>
      </section>

      <section className="learn-os-dashboard-grid learn-os-dashboard-grid--footer learn-reveal">
        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <div>
              <h2>Study Plan</h2>
              <p>May 26 - June 1, 2025</p>
            </div>
            <span className="learn-os-chip-alt">Today</span>
          </header>
          <div className="learn-os-study-plan">
            <div className="learn-os-calendar-strip">
              {['Mon 26', 'Tue 27', 'Wed 28', 'Thu 29', 'Fri 30', 'Sat 31', 'Sun 1'].map((day, index) => (
                <span key={day} className={index === 0 ? 'is-active' : ''}>{day}</span>
              ))}
            </div>
            {[
              ['Complete: GDP & Economic Growth', 'Macroeconomics Overview', '30m'],
              ['Watch: Supply and Demand in Action', 'Microeconomics Basics', '45m'],
              ['Quiz: Market Equilibrium', 'Microeconomics Basics', '20m'],
            ].map(([task, sub, time], index) => (
              <label key={task} className="learn-os-task-row">
                <input type="checkbox" defaultChecked={index === 0} />
                <strong>{task}<small>{sub}</small></strong>
                <em>{time}</em>
              </label>
            ))}
          </div>
        </article>

        <article className="learn-os-card">
          <header className="learn-os-card__head">
            <div>
              <h2>Achievements</h2>
            </div>
            <button type="button" className="learn-os-link-btn" onClick={() => setRefreshKey((v) => v + 1)}>View all</button>
          </header>
          <div className="learn-os-achievement-grid">
            {[
              ['First Steps', 'Complete your first course', 'Earned', 'is-green'],
              ['Consistent Learner', 'Maintain a 7-day study streak', 'Earned', 'is-amber'],
              ['Quiz Master', 'Score 80% or higher in 10 quizzes', '7/10', 'is-teal'],
              ['Course Explorer', 'Complete 10 courses', '8/10', 'is-purple'],
            ].map((item, index) => {
              const icons = [<StarIcon size={28} fill="currentColor" />, <FlameIcon size={28} fill="currentColor" />, <LightbulbIcon size={28} fill="currentColor" />, <BookIcon size={28} />]
              return (
                <article key={item[0]} className="learn-os-achievement">
                  <div className={`learn-os-achievement-badge ${item[3]}`}>
                    {icons[index]}
                  </div>
                  <strong>{item[0]}</strong>
                  <span>{item[1]}</span>
                  <em>{item[2]}</em>
                </article>
              )
            })}
          </div>
        </article>
      </section>

      <section className="learn-os-card learn-os-community learn-reveal">
        <header className="learn-os-card__head">
          <h2>Community & Support</h2>
        </header>
        <div className="learn-os-community-grid">
          <article>
            <h3>Top Discussions</h3>
            {['How to build a strong DCF model?', 'Career advice for aspiring CFA candidates', 'Best resources for learning derivatives'].map((item) => (
              <button key={item} type="button" onClick={() => onOpenCommunity?.('learning')}>{item}<span>24m</span></button>
            ))}
          </article>
          <article>
            <h3>Ask the Mentor</h3>
            <p>Get answers from finance professionals and educators.</p>
            <div className="learn-os-avatar-row"><span>A</span><span>M</span><span>J</span><em>+8</em></div>
            <button type="button" className="learn-os-btn learn-os-btn--primary" onClick={handleTutor}>Ask a Question</button>
          </article>
          <article>
            <h3>Study Groups</h3>
            {['CFA Level I Aspirants', 'Financial Modeling Enthusiasts', 'Investment Club'].map((item) => (
              <button key={item} type="button" onClick={() => onOpenCommunity?.('learning')}>{item}<b>Join</b></button>
            ))}
          </article>
        </div>
      </section>

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
            <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={() => setAssetRefreshKey((v) => v + 1)}>
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
          {onOpenGoals ? (
            <button type="button" className="learn-os-btn learn-os-btn--ghost" onClick={() => onOpenGoals('')}>
              Mở Goals
            </button>
          ) : null}
        </div>
      </footer>
    </section>
  )
}

function useLearnDashboardMotion() {
  useEffect(() => {
    const root = document.querySelector('.learn-os-page')
    if (!root) return undefined

    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const items = Array.from(root.querySelectorAll('.learn-reveal'))
    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
      items.forEach((item) => item.classList.add('is-visible'))
      return undefined
    }

    root.classList.add('is-motion-ready')
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        })
      },
      { threshold: 0.12, rootMargin: '0px 0px -8% 0px' },
    )

    items.forEach((item) => observer.observe(item))
    return () => {
      observer.disconnect()
      root.classList.remove('is-motion-ready')
    }
  }, [])
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

function buildLearningDashboard({ data, lesson, contextCards, videoAssets, audioAssets, bookAssets, resourceBundle }) {
  const completion = Math.max(0, data?.completion_pct || 0)
  const lessonMinutes = Math.max(lesson?.estimated_minutes || 5, 5)
  return {
    pathSteps: [
      { id: 'foundations', title: 'Foundations', subtitle: 'Nền tảng tài chính', state: 'is-active' },
      { id: 'risk', title: 'Risk', subtitle: 'Quản trị rủi ro', state: completion >= 25 ? 'is-active' : 'is-idle' },
      { id: 'goals', title: 'Goals', subtitle: 'Lập kế hoạch', state: completion >= 50 ? 'is-active' : 'is-idle' },
      { id: 'investing', title: 'Investing', subtitle: 'Đầu tư cơ bản', state: completion >= 75 ? 'is-active' : 'is-idle' },
    ],
    stats: [
      { label: 'Learning Streak', value: `${Math.max(3, Math.round(completion / 2))} ngày`, subtext: 'Tuyệt vời! Hãy duy trì nhé!' },
      { label: 'Completed Lessons', value: `${data?.completed_lessons || 0} bài`, subtext: 'Trong tổng số lộ trình hiện tại' },
      { label: 'Current Path', value: data?.path_label || 'Financial Foundations', subtext: `Đã hoàn thành ${completion}%` },
      { label: 'Recommended Next', value: data?.next_lesson_title || 'Ngân sách là gì?', subtext: 'Bài học tiếp theo trong lộ trình' },
    ],
    recommended: [
      {
        title: data?.next_lesson_title || 'Quỹ khẩn cấp: Tại sao và bắt đầu từ đâu?',
        summary: lesson?.summary || data?.recommendation_summary || 'Hiểu tầm quan trọng của quỹ khẩn cấp và cách xây dựng quỹ dự phòng.',
        minutes: lessonMinutes,
        level: tierLabel(lesson?.tier).replace('Financial basics', 'Dễ'),
      },
      {
        title: 'Ngân sách là gì?',
        summary: 'Học cách lập ngân sách 50/30/20 để kiểm soát chi tiêu và đạt mục tiêu tài chính.',
        minutes: 6,
        level: 'Dễ',
      },
      {
        title: 'Thu nhập - Chi tiêu - Tiết kiệm: Cân bằng ra sao?',
        summary: 'Tìm hiểu nguyên tắc cân bằng tài chính cá nhân để sống thoải mái và tiến bộ mỗi ngày.',
        minutes: 7,
        level: 'Trung bình',
      },
    ],
    trackRows: [
      { id: 'path-current', title: data?.path_label || 'Financial Foundations', subtitle: 'Nền tảng tài chính', progress: completion, status: 'Đang học' },
      { id: 'risk-market', title: 'Risk & Market Basics', subtitle: 'Rủi ro & thị trường cơ bản', progress: Math.max(8, Math.round(completion * 0.65)), status: 'Chưa bắt đầu' },
      { id: 'goal-plan', title: 'Goal Planning', subtitle: 'Lập kế hoạch mục tiêu', progress: Math.max(0, completion - 12), status: 'Chưa bắt đầu' },
      { id: 'investing', title: 'Investing Basics', subtitle: 'Đầu tư cơ bản', progress: Math.max(0, completion - 24), status: 'Chưa bắt đầu' },
    ],
    topics: ['Saving', 'Budgeting', 'Debt', 'Emergency Fund', 'Risk', 'News', 'BCTC Basics', 'Portfolio Basics'],
    learnToday: [
      { title: contextCards[0]?.recommended_lesson_title || 'Risk-on / Risk-off là gì?', summary: contextCards[0]?.reason || 'Hiểu cách thị trường dịch chuyển giữa các chế độ rủi ro.', meta: '5 phút • Dễ', ctaType: 'insights' },
      { title: 'Tỷ giá ảnh hưởng thế nào?', summary: contextCards[1]?.reason || 'Tìm hiểu tác động của tỷ giá đến doanh nghiệp và danh mục đầu tư.', meta: '6 phút • Dễ', ctaType: 'guided_investing' },
      { title: 'Lãi suất tác động ra sao?', summary: 'Hiểu cơ chế lãi suất và ảnh hưởng đến thị trường tài chính.', meta: '6 phút • Trung bình', ctaType: 'financial_health' },
    ],
    weeklyProgress: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((day, index) => {
      const minutes = 18 + ((completion + index * 8) % 25)
      return { day, minutes, height: Math.min(100, Math.round((minutes / 45) * 100)) }
    }),
    achievements: [
      { title: 'Consistent Learner', subtitle: `${Math.max(3, Math.round(completion / 2))} ngày liên tiếp`, tone: 'is-teal' },
      { title: 'Quick Starter', subtitle: `Hoàn thành ${Math.max(1, data?.completed_lessons || 0)} bài học`, tone: 'is-green' },
      { title: 'Curious Mind', subtitle: `${Math.max(3, LEARN_QUICK_PROMPTS.length)} câu hỏi cho Tutor`, tone: 'is-amber' },
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
