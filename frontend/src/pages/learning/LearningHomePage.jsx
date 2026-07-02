import { useEffect, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'

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
import {
  PlayIcon, BookIcon, HeadphonesIcon, TargetIcon, LightbulbIcon, PiggyBankIcon,
  CalculatorIcon, ScaleIcon, ShieldIcon, ShieldPlusIcon, PlantIcon, FlagIcon,
  LineChartIcon, PieChartIcon, FileTextIcon, FlameIcon, StarIcon, CheckCircleIcon,
  ClockIcon, ArrowRightIcon, BarChartIcon, TrendingUpIcon, GlobeIcon, PercentIcon,
} from '../../shared/Icons'
import { BookReaderWorkspace } from './BookReaderWorkspace'

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
      return (
        title.includes(searchLow) ||
        description.includes(searchLow) ||
        author.includes(searchLow)
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
      <section className="flex items-center justify-center p-8 min-h-[50vh] text-center">
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow max-w-md">
          <h1 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Onboarding Needed</h1>
          <p className="text-sm text-slate-500 dark:text-zinc-400 mb-4">Learn Hub cần session onboarding để cá nhân hóa lộ trình học.</p>
          {onBack && (
            <button type="button" className="px-4 py-2 bg-teal-500 text-white rounded-full text-xs font-semibold cursor-pointer" onClick={onBack}>
              Về Home
            </button>
          )}
        </div>
      </section>
    )
  }

  if (isLoading) {
    return (
      <section className="flex items-center justify-center p-8 min-h-[50vh] text-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <h1 className="text-base font-semibold text-slate-650 dark:text-zinc-400">Đang dựng lộ trình học cho bạn...</h1>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="flex items-center justify-center p-8 min-h-[50vh] text-center">
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow max-w-md">
          <h1 className="text-xl font-bold text-red-650 dark:text-red-400 mb-2">Chưa tải được dữ liệu</h1>
          <p className="text-sm text-slate-500 dark:text-zinc-400 mb-4">{error}</p>
          <button type="button" className="px-4 py-2 bg-teal-500 text-white rounded-full text-xs font-semibold cursor-pointer" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}>
            Thử lại
          </button>
        </div>
      </section>
    )
  }

  if (!data) {
    return (
      <section className="flex items-center justify-center p-8 min-h-[50vh] text-center">
        <div className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow max-w-md">
          <p className="text-sm text-slate-500 dark:text-zinc-400">Learn Hub chưa có dữ liệu. Quay lại Home để đồng bộ session.</p>
        </div>
      </section>
    )
  }

  if (activeBook) {
    return (
      <BookReaderWorkspace
        book={activeBook}
        sessionId={sessionId}
        asPage
        onClose={() => setActiveBook(null)}
      />
    )
  }

  return (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full min-h-[100dvh] bg-transparent text-slate-900 dark:text-zinc-150 font-sans py-6 md:py-8"
    >
      <div className="max-w-[1720px] mx-auto w-full flex flex-col gap-6 px-6 md:px-10">
        <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Learn Hub</h1>
          <p className="text-sm text-slate-550 dark:text-zinc-400 mt-1">{data.path_label} · {completionText} hoàn thành · dữ liệu runtime</p>
        </div>
        <div className="flex gap-2 p-0.5 bg-slate-100 dark:bg-zinc-900 rounded-full border border-slate-200/60 dark:border-zinc-800 self-start">
          {[['lesson', 'Bài học'], ['path', 'Lộ trình'], ['library', 'Thư viện'], ['tutor', 'Tutor AI']].map(([viewKey, label]) => (
            <button
              key={viewKey}
              type="button"
              className={`px-4 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-all duration-200 ${
                activeLearnView === viewKey
                  ? 'bg-teal-500 text-white shadow-sm'
                  : 'text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
              }`}
              onClick={() => setActiveLearnView(viewKey)}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* --- Tab Content: Lộ trình --- */}
      {activeLearnView === 'path' && (
        <div className="flex flex-col gap-6">
          <section className="flex flex-col gap-4">
            <header className="flex justify-between items-center">
              <h2 className="text-base font-bold text-slate-800 dark:text-zinc-350">Chủ đề theo lộ trình</h2>
              <button className="text-xs font-bold text-teal-650 dark:text-teal-400 hover:underline cursor-pointer" type="button" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}>Làm mới</button>
            </header>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
              {dashboard.topics.map((topic, index) => (
                <button
                  key={topic.label}
                  type="button"
                  className={`flex items-center gap-3 p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm hover:shadow hover:-translate-y-0.5 transition-all cursor-pointer text-left ${
                    index === 0 ? 'ring-2 ring-teal-500/20 border-teal-500 dark:border-teal-500' : ''
                  }`}
                  onClick={() => setQuestion(`Giải thích ${topic.label} cho người mới học tài chính.`)}
                >
                  <span className="w-8 h-8 rounded-full bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-450 flex items-center justify-center shrink-0 border border-teal-100 dark:border-teal-900/20">{topic.icon}</span>
                  <div className="min-w-0">
                    <strong className="block text-xs font-bold text-slate-805 dark:text-white truncate">{topic.label}</strong>
                    <small className="text-[10px] text-slate-500 dark:text-zinc-400 font-semibold">{topic.count}</small>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex items-center gap-2 text-slate-700 dark:text-zinc-300 font-semibold text-xs md:text-sm">
                <span className="w-6 h-6 rounded-full bg-teal-500 text-white flex items-center justify-center"><TrendingUpIcon size={14} /></span>
                <strong>Tiến độ học của bạn</strong>
              </header>
              <div className="flex items-center gap-6">
                <div className="relative w-20 h-20 flex items-center justify-center shrink-0">
                  <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90">
                    <path className="fill-none stroke-slate-100 dark:stroke-zinc-800" strokeWidth="3" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path className="fill-none stroke-teal-500" strokeWidth="3" strokeDasharray={`${data?.completion_pct || 12}, 100`} strokeLinecap="round" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <strong className="text-base font-extrabold text-slate-900 dark:text-white leading-none">{completionText}</strong>
                    <span className="text-[9px] text-slate-500 dark:text-zinc-450 mt-1 uppercase tracking-wider font-bold">Tổng tiến độ</span>
                  </div>
                </div>
                <dl className="flex-1 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                  <div>
                    <dt className="text-slate-500 dark:text-zinc-450">Khoá học</dt>
                    <dd className="font-bold text-slate-900 dark:text-white mt-0.5">{dashboard.stats[2].value}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500 dark:text-zinc-450">Đã xong</dt>
                    <dd className="font-bold text-slate-900 dark:text-white mt-0.5">{dashboard.stats[1].value}</dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="text-slate-500 dark:text-zinc-450">Bài kế tiếp</dt>
                    <dd className="font-bold text-slate-900 dark:text-white mt-0.5 truncate">{data?.next_lesson_title || '—'}</dd>
                  </div>
                </dl>
              </div>
            </article>

            <article className="lg:col-span-2 p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center">
                <h2 className="text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Số liệu runtime</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400">SQLite</span>
              </header>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {dashboard.statGrid.map(({ label, value, delta }) => (
                  <div key={label} className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200/60 dark:border-zinc-850">
                    <span className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">{label}</span>
                    <strong className="block text-xl font-extrabold text-slate-950 dark:text-white mt-1 leading-none">{value}</strong>
                    <small className="block text-[9px] text-slate-400 dark:text-zinc-500 mt-2 font-semibold truncate">{delta}</small>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <section className="flex flex-col gap-4">
            <header className="flex justify-between items-center">
              <h2 className="text-base font-bold text-slate-800 dark:text-zinc-350">Khoá học & lộ trình</h2>
              <button className="text-xs font-bold text-teal-650 dark:text-teal-400 hover:underline cursor-pointer" type="button" onClick={() => setActiveLearnView('lesson')}>Mở bài học</button>
            </header>
            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              {dashboard.courseCards.map((item) => (
                <button key={item.title} type="button" className="flex flex-col p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm text-left hover:shadow hover:-translate-y-0.5 transition-all cursor-pointer min-h-[190px] justify-between" onClick={() => setActiveLearnView('lesson')}>
                  <div className="w-full flex items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-zinc-850">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{item.tag}</span>
                    <span className="w-6 h-6 rounded bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-450 flex items-center justify-center shrink-0 border border-teal-100 dark:border-teal-900/10">{item.icon}</span>
                  </div>
                  <div className="flex-1 flex flex-col justify-center py-2">
                    <strong className="text-xs font-bold text-slate-900 dark:text-white leading-snug line-clamp-2">{item.title}</strong>
                    <p className="text-[10px] text-slate-500 dark:text-zinc-400 mt-1">{item.meta}</p>
                  </div>
                  <div className="w-full">
                    <div className="flex items-center justify-between text-[9px] text-slate-550 dark:text-zinc-400 font-bold mb-1">
                      <span>Tiến độ</span>
                      <span>{item.progress}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-zinc-800 overflow-hidden">
                      <div className="h-full bg-teal-500 transition-all duration-300" style={{ width: `${item.progress}%` }} />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <article className="lg:col-span-2 p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center">
                <h2 className="text-sm font-bold text-slate-800 dark:text-white">Gợi ý cho bạn</h2>
                <button type="button" className="text-xs font-bold text-teal-650 dark:text-teal-400 hover:underline cursor-pointer" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}>Làm mới</button>
              </header>
              <div className="flex flex-col gap-3">
                {dashboard.recommended.map((item) => (
                  <article key={item.title} className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200/60 dark:border-zinc-850 flex items-center justify-between gap-4 hover:border-slate-300 dark:hover:border-zinc-700 transition-all duration-200">
                    <div className="min-w-0 flex-1">
                      <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{item.title}</strong>
                      <p className="text-[11px] text-slate-550 dark:text-zinc-400 mt-0.5 line-clamp-2 leading-relaxed">{item.summary}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1.5 shrink-0">
                      <span className="text-[9px] text-slate-500 dark:text-zinc-450 font-bold">{item.meta}</span>
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-450 border border-teal-100 dark:border-teal-900/20">{item.score}</span>
                    </div>
                  </article>
                ))}
              </div>
            </article>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center">
                <h2 className="text-sm font-bold text-slate-800 dark:text-white">Bài học gần nhất</h2>
                <button type="button" className="text-xs font-bold text-teal-655 dark:text-teal-400 hover:underline cursor-pointer" onClick={() => setActiveLearnView('lesson')}>Mở bài học</button>
              </header>
              <div className="flex flex-col gap-2.5">
                {dashboard.pathLessons.slice(0, 4).map((item, index) => (
                  <button key={item.lesson_id} type="button" className="w-full flex items-center justify-between gap-3 p-2.5 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-100 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left" onClick={() => setQuestion(`Giải thích bài ${item.title} cho tôi.`)}>
                    <div className="min-w-0 flex-1">
                      <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{item.title}</strong>
                      <small className="block text-[10px] text-slate-500 dark:text-zinc-400 mt-0.5 truncate">{contentTypeLabel(item.content_type)} · {tierLabel(item.tier)}</small>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-slate-500 dark:text-zinc-400">{item.estimated_minutes}m</span>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        item.status === 'completed' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 border border-emerald-100' : 'bg-teal-50 dark:bg-teal-950/20 text-teal-600 border border-teal-100'
                      }`}>
                        {item.status === 'completed' ? 'Xong' : 'Học'}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </article>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center">
                <div>
                  <h2 className="text-sm font-bold text-slate-800 dark:text-white">Kế hoạch tuần này</h2>
                  <p className="text-[10px] text-slate-500 dark:text-zinc-450 mt-0.5">{dashboard.studyWeekLabel}</p>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400">Hôm nay</span>
              </header>
              <div className="flex flex-col gap-3">
                <div className="grid grid-cols-7 gap-1 bg-slate-50 dark:bg-zinc-950 p-2 rounded-xl border border-slate-200/50 dark:border-zinc-800">
                  {dashboard.studyDays.map((day, index) => (
                    <span key={day} className={`text-[10px] font-bold text-center py-1 rounded ${index === 0 ? 'bg-teal-500 text-white' : 'text-slate-550 dark:text-zinc-400'}`}>{day.slice(0, 3)}</span>
                  ))}
                </div>
                {dashboard.studyPlan.length ? dashboard.studyPlan.map((item) => (
                  <label key={item.lesson_id} className="flex items-center gap-3 p-2.5 rounded-xl border border-slate-250/50 dark:border-zinc-850 bg-slate-50/50 dark:bg-zinc-900">
                    <input type="checkbox" readOnly checked={item.status === 'completed'} className="rounded border-slate-300 dark:border-zinc-700 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5 cursor-not-allowed" />
                    <div className="flex-1 min-w-0">
                      <strong className="block text-xs font-semibold text-slate-800 dark:text-zinc-200 truncate">{item.task}</strong>
                      <small className="block text-[10px] text-slate-500 dark:text-zinc-400 truncate">{item.sub}</small>
                    </div>
                    <span className="text-[10px] text-slate-450 shrink-0">{item.time}</span>
                  </label>
                )) : <p className="text-xs text-slate-500 dark:text-zinc-450 text-center py-4">Chưa có việc trong tuần.</p>}
              </div>
            </article>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center">
                <div>
                  <h2 className="text-sm font-bold text-slate-800 dark:text-white">Thực hành mô phỏng</h2>
                  <p className="text-[10px] text-slate-500 dark:text-zinc-450 mt-0.5">Áp dụng lý thuyết vào thực tiễn.</p>
                </div>
              </header>
              <div className="flex flex-col gap-3">
                <button type="button" className="flex items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-100 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left" onClick={() => onOpenGuidedInvesting?.('market_context')}>
                  <div>
                    <strong className="block text-xs font-bold text-slate-900 dark:text-white">Guided Investing</strong>
                    <small className="block text-[10px] text-slate-550 dark:text-zinc-400 mt-0.5">Đọc rủi ro & drawdown với BCTC</small>
                  </div>
                  <ArrowRightIcon size={14} className="text-slate-500" />
                </button>
                <button type="button" className="flex items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-100 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left" onClick={() => onOpenInsights?.()}>
                  <div>
                    <strong className="block text-xs font-bold text-slate-900 dark:text-white">Insights Engine</strong>
                    <small className="block text-[10px] text-slate-550 dark:text-zinc-400 mt-0.5">Xem dữ liệu thị trường để nối ngữ cảnh</small>
                  </div>
                  <ArrowRightIcon size={14} className="text-slate-500" />
                </button>
              </div>
            </article>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center">
                <h2 className="text-sm font-bold text-slate-800 dark:text-white">Thư viện sách local</h2>
                <button type="button" className="text-xs font-bold text-teal-650 dark:text-teal-400 hover:underline cursor-pointer" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning', 'assets'] })}>Làm mới</button>
              </header>
              <div className="flex flex-col gap-3">
                {dashboard.readingLibrary.map((item) => (
                  <button key={item.asset_id} type="button" className="w-full flex items-center gap-3 p-2.5 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-100 dark:border-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-left" onClick={() => setActiveBook(item)}>
                    <div className="w-8 h-8 rounded bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 flex items-center justify-center shrink-0 border border-teal-100 dark:border-teal-900/10"><BookIcon size={14} /></div>
                    <div className="flex-1 min-w-0">
                      <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{item.title}</strong>
                      <span className="block text-[9px] text-slate-500 dark:text-zinc-450 truncate">{item.file_name} · {formatBytes(item.size_bytes)}</span>
                    </div>
                  </button>
                ))}
                {!dashboard.readingLibrary.length && <p className="text-xs text-slate-500 dark:text-zinc-450 text-center py-4">Chưa có sách trong thư viện local.</p>}
              </div>
            </article>
          </div>
        </div>
      )}

      {/* --- Tab Content: Thư viện --- */}
      {activeLearnView === 'library' && (
        <div className="flex flex-col gap-6">
          <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
            <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Thư viện học liệu</p>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-1">Catalog từ arXiv · MIT · Yale · archive.org</h2>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">Dữ liệu curated được quét tự động từ các nguồn học thuật uy tín.</p>
              </div>
              <button
                type="button"
                className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-zinc-800 text-slate-655 dark:text-zinc-300 hover:bg-slate-200 dark:hover:bg-zinc-700 transition cursor-pointer self-start"
                onClick={() => {
                  setCatalogTopic('')
                  setCatalogSearch('')
                }}
              >
                Đặt lại bộ lọc
              </button>
            </header>

            <div className="flex flex-col sm:flex-row gap-3 pt-3 border-t border-slate-100 dark:border-zinc-850">
              <nav className="flex bg-slate-100 dark:bg-zinc-850 rounded-lg p-0.5 border border-slate-200/50 dark:border-zinc-800 shrink-0 self-start">
                {[
                  ['video', 'Video'],
                  ['book', 'Sách'],
                  ['paper', 'Paper'],
                  ['course', 'Khoá học'],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer transition-all duration-200 ${
                      catalogKind === id
                        ? 'bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm'
                        : 'text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
                    }`}
                    onClick={() => setCatalogKind(id)}
                  >
                    {label}
                  </button>
                ))}
              </nav>

              <div className="flex-1 flex gap-3 flex-wrap">
                {catalogTopics.length ? (
                  <select
                    className="rounded-lg border border-slate-200 dark:border-zinc-750 bg-white dark:bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-slate-800 dark:text-zinc-200 outline-none"
                    value={catalogTopic}
                    onChange={(e) => setCatalogTopic(e.target.value)}
                  >
                    <option value="">Tất cả chủ đề</option>
                    {catalogTopics.map((topic) => (
                      <option key={topic.topic_id} value={topic.topic_id}>
                        {topic.label_vi} ({topic.resource_count || 0})
                      </option>
                    ))}
                  </select>
                ) : null}

                <div className="relative flex-1 min-w-[200px]">
                  <span className="absolute left-3 top-2.5 text-xs text-slate-400">🔍</span>
                  <input
                    type="text"
                    className="w-full pl-8 pr-8 py-1.5 rounded-lg border border-slate-200 dark:border-zinc-750 bg-white dark:bg-zinc-900 text-xs font-semibold text-slate-800 dark:text-zinc-200 outline-none focus:border-teal-500"
                    value={catalogSearch}
                    onChange={(e) => setCatalogSearch(e.target.value)}
                    placeholder={`Tìm kiếm ${catalogKind === 'video' ? 'video' : catalogKind === 'book' ? 'sách' : catalogKind === 'paper' ? 'tài liệu' : 'khoá học'}...`}
                  />
                  {catalogSearch && (
                    <button
                      type="button"
                      className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 dark:hover:text-white text-xs cursor-pointer"
                      onClick={() => setCatalogSearch('')}
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>
            </div>

            {catalogLoading ? <p className="text-xs text-slate-500 py-4 text-center">Đang tải catalog…</p> : null}
            {catalogError ? <p className="text-xs text-red-500 py-4 text-center">{catalogError}</p> : null}

            {!catalogLoading && !catalogError && !catalogItems.length && (
              <p className="text-xs text-slate-500 py-6 text-center">Catalog chưa có dữ liệu. Chạy `risk-learning-crawl` để fill.</p>
            )}

            {!catalogLoading && !catalogError && catalogItems.length > 0 && !filteredCatalogItems.length && (
              <p className="text-xs text-slate-500 py-6 text-center">Không tìm thấy tài liệu phù hợp.</p>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
              {filteredCatalogItems.map((item) => (
                <CatalogCard key={item[`${catalogKind}_id`]} kind={catalogKind} item={item} />
              ))}
            </div>
          </article>

          <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
            <header className="flex justify-between items-center">
              <div>
                <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-bold uppercase tracking-wider">Media Library</p>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-1">Quét từ thư mục local của bạn</h2>
              </div>
              <button type="button" className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-zinc-800 text-slate-655 dark:text-zinc-300 hover:bg-slate-200 dark:hover:bg-zinc-700 transition cursor-pointer" onClick={() => queryClient.invalidateQueries({ queryKey: ['learning', 'assets'] })}>
                Quét lại thư mục
              </button>
            </header>

            {assetLoading ? <p className="text-xs text-slate-500 text-center py-4">Đang quét media local...</p> : null}
            {assetError ? <p className="text-xs text-red-500 text-center py-4">{assetError}</p> : null}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-2">
              <section className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-700 dark:text-zinc-300 pb-2 border-b border-slate-100 dark:border-zinc-850">Video ({videoAssets.length})</h3>
                <div className="flex flex-col gap-3">
                  {videoAssets.map((item) => (
                    <article key={item.asset_id} className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-150 dark:border-zinc-800 flex items-center gap-3">
                      <div className="w-16 h-10 rounded bg-slate-200 dark:bg-zinc-800 shrink-0 overflow-hidden flex items-center justify-center text-[10px] font-bold text-slate-500">VIDEO</div>
                      <div className="min-w-0 flex-1">
                        <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{item.title}</strong>
                        <small className="block text-[9px] text-slate-500 dark:text-zinc-450 truncate mt-0.5">{item.file_name} · {formatBytes(item.size_bytes)}</small>
                      </div>
                      <a className="px-2.5 py-1.5 rounded bg-teal-500 hover:bg-teal-600 text-white text-[10px] font-bold transition cursor-pointer shrink-0" href={item.url} target="_blank" rel="noreferrer">
                        Xem
                      </a>
                    </article>
                  ))}
                  {!videoAssets.length && !assetLoading && <p className="text-xs text-slate-550 dark:text-zinc-400 text-center py-6">Chưa có video local.</p>}
                </div>
              </section>

              <section className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-700 dark:text-zinc-300 pb-2 border-b border-slate-100 dark:border-zinc-850">Audio ({audioAssets.length})</h3>
                <div className="flex flex-col gap-3">
                  {audioAssets.map((item) => (
                    <article key={item.asset_id} className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-150 dark:border-zinc-800 flex flex-col gap-2">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 flex items-center justify-center shrink-0 border border-teal-100"><HeadphonesIcon size={15} /></div>
                        <div className="min-w-0 flex-1">
                          <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{item.title}</strong>
                          <small className="block text-[9px] text-slate-500 dark:text-zinc-450 truncate mt-0.5">{item.file_name} · {formatBytes(item.size_bytes)}</small>
                        </div>
                      </div>
                      <audio controls preload="none" src={item.url} className="w-full h-8 mt-1 outline-none rounded bg-slate-100 dark:bg-zinc-800" />
                    </article>
                  ))}
                  {!audioAssets.length && !assetLoading && <p className="text-xs text-slate-550 dark:text-zinc-400 text-center py-6">Chưa có audio local.</p>}
                </div>
              </section>

              <section className="flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-700 dark:text-zinc-300 pb-2 border-b border-slate-100 dark:border-zinc-850">Sách ({bookAssets.length})</h3>
                <div className="flex flex-col gap-3">
                  {bookAssets.map((item) => (
                    <article key={item.asset_id} className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-850/40 border border-slate-150 dark:border-zinc-800 flex items-center gap-3">
                      <div className="w-10 h-14 rounded bg-slate-200 dark:bg-zinc-800 shrink-0 border border-slate-350 overflow-hidden flex items-center justify-center text-[10px] font-bold text-slate-500 text-center p-1">BOOK</div>
                      <div className="min-w-0 flex-1">
                        <strong className="block text-xs font-bold text-slate-900 dark:text-white truncate">{item.title}</strong>
                        <small className="block text-[9px] text-slate-500 dark:text-zinc-450 truncate mt-0.5">{item.file_name} · {formatBytes(item.size_bytes)}</small>
                      </div>
                      <div className="flex flex-col gap-1.5 shrink-0">
                        <button type="button" className="px-2 py-1.5 rounded bg-teal-500 hover:bg-teal-600 text-white text-[10px] font-bold cursor-pointer text-center" onClick={() => setActiveBook(item)}>
                          Đọc
                        </button>
                        <a className="px-2 py-1.5 rounded bg-slate-200 dark:bg-zinc-800 hover:bg-slate-300 text-slate-800 dark:text-zinc-200 text-[10px] font-bold text-center" href={item.url} target="_blank" rel="noreferrer">
                          File
                        </a>
                      </div>
                    </article>
                  ))}
                  {!bookAssets.length && !assetLoading && <p className="text-xs text-slate-550 dark:text-zinc-400 text-center py-6">Chưa có sách local.</p>}
                </div>
              </section>
            </div>
          </article>
        </div>
      )}

      {/* --- Tab Content: Bài học --- */}
      {activeLearnView === 'lesson' && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6 items-start">
          <article className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-6">
            <header className="flex justify-between gap-4 flex-wrap border-b border-slate-100 dark:border-zinc-850 pb-4">
              <div>
                <p className="text-[10px] text-teal-600 dark:text-teal-400 font-bold uppercase tracking-wider">Bài học hôm nay</p>
                <h2 className="text-xl font-bold text-slate-950 dark:text-white mt-1">{lesson?.title || data.next_lesson_title}</h2>
                <p className="text-xs md:text-sm text-slate-550 dark:text-zinc-400 mt-2 leading-relaxed">{lesson?.summary || data.recommendation_summary}</p>
              </div>
              <div className="flex gap-2 self-start flex-wrap">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 dark:bg-teal-950/30 text-teal-650 dark:text-teal-450 border border-teal-100 dark:border-teal-900/20">{tierLabel(lesson?.tier)}</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 dark:bg-teal-950/30 text-teal-650 dark:text-teal-450 border border-teal-100 dark:border-teal-900/20">{contentTypeLabel(lesson?.content_type)}</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-50 dark:bg-zinc-850 text-slate-600 dark:text-zinc-400 border border-slate-200 dark:border-zinc-800">{lesson?.estimated_minutes || 3} phút</span>
              </div>
            </header>

            {lessonLoading && <p className="text-sm text-slate-555 py-4">Đang tải chi tiết nội dung bài học...</p>}
            {lessonError && <p className="text-sm text-red-500 bg-red-50 dark:bg-red-950/20 p-3 rounded-lg border border-red-200">{lessonError}</p>}

            {lesson?.body?.length ? (
              <div className="flex flex-col gap-4 text-slate-700 dark:text-zinc-350 text-sm md:text-base leading-relaxed">
                {lesson.body.map((block, idx) => (
                  <p key={idx}>{block}</p>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-450 dark:text-zinc-500 py-4 text-center">Chưa có nội dung bài chi tiết.</p>
            )}

            {lesson?.glossary?.length ? (
              <div className="p-5 rounded-2xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-800/80 mt-2">
                <h3 className="text-sm font-bold text-slate-800 dark:text-white uppercase tracking-wider mb-4">Glossary nhanh</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {lesson.glossary.map((term) => (
                    <article key={term.term} className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-slate-150 dark:border-zinc-850">
                      <strong className="block text-xs font-bold text-teal-600 dark:text-teal-400">{term.term}</strong>
                      <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-1 leading-relaxed">{term.definition}</p>
                    </article>
                  ))}
                </div>
              </div>
            ) : null}

            {lesson?.quiz_questions?.length ? (
              <div className="p-5 rounded-2xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-800 mt-2 flex flex-col gap-4">
                <h3 className="text-sm font-bold text-slate-850 dark:text-white uppercase tracking-wider">Quiz kiểm tra</h3>
                {lesson.quiz_questions.map((quiz) => (
                  <article key={quiz.question_id} className="p-4 rounded-xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 flex flex-col gap-3">
                    <p className="text-xs md:text-sm font-bold text-slate-900 dark:text-white leading-relaxed">{quiz.prompt}</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {quiz.options.map((option) => {
                        const selected = answers[quiz.question_id] === option
                        return (
                          <button
                            key={option}
                            type="button"
                            className={`px-4 py-2.5 rounded-lg text-xs font-semibold cursor-pointer border text-left transition-all ${
                              selected
                                ? 'bg-teal-500 text-white border-teal-500 shadow-md shadow-teal-500/10'
                                : 'bg-slate-50 dark:bg-zinc-950 border-slate-200 dark:border-zinc-800 text-slate-700 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-zinc-850'
                            }`}
                            onClick={() => setAnswers((current) => ({ ...current, [quiz.question_id]: option }))}
                          >
                            {option}
                          </button>
                        )
                      })}
                    </div>
                  </article>
                ))}
                <div className="flex gap-3 mt-2 flex-wrap">
                  <button type="button" className="px-4 py-2 rounded-full text-xs font-bold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer transition active:scale-95 shadow-md shadow-teal-500/10" onClick={handleQuizSubmit} disabled={submittingQuiz}>
                    {submittingQuiz ? 'Chấm bài...' : 'Nộp bài quiz'}
                  </button>
                  <button type="button" className="px-4 py-2 rounded-full text-xs font-bold bg-slate-100 dark:bg-zinc-800 hover:bg-slate-205 text-slate-800 dark:text-zinc-200 border border-slate-200 dark:border-zinc-700 cursor-pointer transition active:scale-95" onClick={handleComplete} disabled={completingLesson}>
                    {completingLesson ? 'Cập nhật...' : 'Hoàn thành bài học'}
                  </button>
                </div>
                {quizResult && (
                  <div className={`p-4 rounded-xl border mt-2 flex flex-col gap-2 ${
                    quizResult.passed
                      ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/30 text-emerald-850'
                      : 'bg-amber-50 dark:bg-amber-950/20 border-amber-250 dark:border-amber-900/30 text-amber-850'
                  }`}>
                    <strong className="text-sm font-extrabold text-slate-900 dark:text-white">Score: {quizResult.score}</strong>
                    <p className="text-xs text-slate-655 dark:text-zinc-350">{quizResult.passed ? 'Bạn đã qua quiz. Tiếp tục bài học nhé!' : 'Chưa sao, làm lại lần nữa để hiểu chắc hơn.'}</p>
                    {quizResult.explanations?.length ? (
                      <ul className="list-disc pl-4 text-xs text-slate-650 dark:text-zinc-400 mt-2 flex flex-col gap-1">
                        {quizResult.explanations.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                )}
              </div>
            ) : null}
          </article>

          {/* Sidebar */}
          <div className="flex flex-col gap-6">
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">AI Companion</h3>
              {coach ? (
                <div className="p-4 rounded-xl bg-teal-50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/25">
                  <strong className="block text-xs font-bold text-teal-700 dark:text-teal-400 mb-1">{coach.title}</strong>
                  <p className="text-[11px] text-slate-650 dark:text-zinc-350 leading-relaxed">{coach.message}</p>
                </div>
              ) : (
                <p className="text-xs text-slate-400 dark:text-zinc-500 italic py-2">Coach sẽ xuất hiện khi có đủ dữ liệu học tập.</p>
              )}
              <div className="flex flex-col gap-2.5">
                <textarea
                  className="w-full p-3 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 text-xs md:text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 text-slate-800 dark:text-zinc-200 leading-normal"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  rows={3}
                  placeholder="Hỏi Companion..."
                />
                <div className="flex gap-2">
                  <button type="button" className="px-4 py-2 rounded-full text-xs font-bold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer active:scale-95 transition-all shadow-sm" onClick={handleTutor} disabled={askingTutor || !lesson}>
                    {askingTutor ? 'Đang trả lời...' : 'Hỏi Tutor'}
                  </button>
                  {onOpenCommunity && (
                    <button type="button" className="px-4 py-2 rounded-full text-xs font-bold bg-slate-100 dark:bg-zinc-800 text-slate-800 dark:text-zinc-200 border border-slate-200 dark:border-zinc-700 cursor-pointer active:scale-95 transition-all" onClick={() => onOpenCommunity('risk-literacy-circle')}>
                      Hỏi Cộng đồng
                    </button>
                  )}
                </div>
              </div>
              {tutor && (
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 text-xs flex flex-col gap-2 leading-relaxed text-slate-650 dark:text-zinc-350">
                  <strong className="text-slate-900 dark:text-white">{tutor.summary}</strong>
                  <p>{tutor.explanation}</p>
                  {tutor.check_question && <small className="text-teal-600 dark:text-teal-400 font-semibold border-t border-slate-200/50 dark:border-zinc-800/80 pt-2 mt-1">{tutor.check_question}</small>}
                </div>
              )}
            </article>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Học liệu đi kèm bài</h3>
              <div className="flex flex-col gap-4">
                <section className="flex flex-col gap-2">
                  <h4 className="text-[11px] font-bold text-slate-800 dark:text-zinc-355 uppercase">Video gợi ý</h4>
                  <div className="flex flex-col gap-2">
                    {resourceBundle.videos.map((item) => (
                      <a key={item.id} href={item.href} target="_blank" rel="noreferrer" className="flex items-center justify-between gap-3 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-zinc-850/50 border border-transparent hover:border-slate-150 dark:hover:border-zinc-800 text-xs">
                        <strong className="font-semibold text-slate-700 dark:text-zinc-300 truncate flex-1">{item.title}</strong>
                        <small className="text-[10px] text-slate-450 dark:text-zinc-500 shrink-0 font-medium">{item.duration}</small>
                      </a>
                    ))}
                    {!resourceBundle.videos.length && <p className="text-[10px] text-slate-450 italic">Không có video nào.</p>}
                  </div>
                </section>
                <section className="flex flex-col gap-2">
                  <h4 className="text-[11px] font-bold text-slate-800 dark:text-zinc-355 uppercase">Book notes</h4>
                  <div className="flex flex-col gap-2">
                    {resourceBundle.books.map((item) => (
                      item.href ? (
                        <a key={item.id} href={item.href} target="_blank" rel="noreferrer" className="flex flex-col gap-0.5 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-zinc-850/50 border border-transparent hover:border-slate-150 dark:hover:border-zinc-800 text-xs">
                          <strong className="font-semibold text-slate-700 dark:text-zinc-300 truncate">{item.title}</strong>
                          <p className="text-[10px] text-slate-450 dark:text-zinc-450 truncate">{item.summary}</p>
                        </a>
                      ) : (
                        <article key={item.id} className="flex flex-col gap-0.5 p-2 rounded-lg bg-slate-50/50 dark:bg-zinc-950/10 text-xs">
                          <strong className="font-semibold text-slate-700 dark:text-zinc-300 truncate">{item.title}</strong>
                          <p className="text-[10px] text-slate-450 dark:text-zinc-450 truncate">{item.summary}</p>
                        </article>
                      )
                    ))}
                    {!resourceBundle.books.length && <p className="text-[10px] text-slate-450 italic">Không có book note nào.</p>}
                  </div>
                </section>
                <section className="flex flex-col gap-2">
                  <h4 className="text-[11px] font-bold text-slate-800 dark:text-zinc-355 uppercase">Thực hành</h4>
                  <div className="flex flex-col gap-2">
                    {resourceBundle.practical.map((item) => (
                      <article key={item.id} className="p-3 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-800/80 flex flex-col gap-2">
                        <strong className="block text-[11px] text-slate-650 dark:text-zinc-350 leading-relaxed">{item.title}</strong>
                        <button
                          type="button"
                          className="px-3.5 py-1.5 rounded bg-teal-500 hover:bg-teal-600 text-white text-xs font-bold cursor-pointer active:scale-95 transition self-start"
                          onClick={() => runPracticalCta(item.ctaType)}
                        >
                          {item.ctaLabel}
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
              </div>
            </article>

            {contextCards.length ? (
              <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Học theo ngữ cảnh đang xem</h3>
                <ul className="flex flex-col gap-3.5">
                  {contextCards.map((item) => (
                    <li key={item.trigger} className="pb-3.5 border-b border-slate-100 dark:border-zinc-850 last:border-none last:pb-0 flex flex-col gap-2">
                      <strong className="block text-xs font-bold text-slate-900 dark:text-white leading-snug">{item.recommended_lesson_title}</strong>
                      <p className="text-[11px] text-slate-500 dark:text-zinc-450 leading-relaxed">{item.reason}</p>
                      <div className="flex gap-2 mt-1">
                        {onOpenGuidedInvesting && (
                          <button
                            type="button"
                            className="px-2.5 py-1.5 rounded text-[10px] font-bold border border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-850 cursor-pointer transition active:scale-95"
                            onClick={() => onOpenGuidedInvesting(item.trigger === 'drawdown' ? 'market_context' : 'watchlist')}
                          >
                            Mở card
                          </button>
                        )}
                        {onOpenCommunity && (
                          <button
                            type="button"
                            className="px-2.5 py-1.5 rounded text-[10px] font-bold border border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-850 cursor-pointer transition active:scale-95"
                            onClick={() => onOpenCommunity(item.trigger === 'drawdown' ? 'risk-literacy-circle' : 'company-case-room')}
                          >
                            Hỏi Group
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </article>
            ) : null}
          </div>
        </div>
      )}

      {/* --- Tab Content: Tutor AI --- */}
      {activeLearnView === 'tutor' && (
        <article className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-6 max-w-4xl mx-auto w-full">
          <header className="border-b border-slate-100 dark:border-zinc-850 pb-4">
            <p className="text-[10px] text-teal-650 dark:text-teal-400 font-bold uppercase tracking-wider">Tutor AI Workspace</p>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">Hỏi gì về tài chính cũng được</h2>
            <p className="text-xs text-slate-500 dark:text-zinc-450 mt-1">Tutor trả lời dựa trên nội dung các bài học và lộ trình cá nhân của bạn.</p>
          </header>

          <div className="min-h-[250px] max-h-[400px] overflow-y-auto bg-slate-50 dark:bg-zinc-950 p-4 rounded-xl border border-slate-200/50 dark:border-zinc-800/80 flex flex-col gap-4 [scrollbar-width:thin]">
            {tutorThread.length === 0 ? (
              <p className="text-xs text-slate-400 italic text-center my-auto">Chưa có câu hỏi. Gõ bên dưới để bắt đầu.</p>
            ) : tutorThread.map((entry, index) => (
              <article key={index} className={`p-4 rounded-xl border max-w-[85%] ${
                entry.role === 'user'
                  ? 'bg-teal-500 text-white border-teal-500 self-end ml-10'
                  : 'bg-white dark:bg-zinc-900 border-slate-200 dark:border-zinc-800 text-slate-800 dark:text-zinc-200 self-start mr-10 shadow-sm'
              }`}>
                <strong className="block text-[10px] font-bold uppercase tracking-wider mb-1.5 opacity-80">{entry.role === 'user' ? 'Bạn' : 'Tutor'}</strong>
                <p className="text-xs md:text-sm leading-relaxed whitespace-pre-wrap">{entry.text}</p>
                {entry.check && <small className="block text-[11px] text-teal-600 dark:text-teal-400 font-semibold border-t border-slate-200/50 dark:border-zinc-850/80 pt-2 mt-2">Câu hỏi tự ôn tập: {entry.check}</small>}
              </article>
            ))}
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2">
              {LEARN_QUICK_PROMPTS.map((prompt) => (
                <button key={prompt} type="button" className="px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-350 border border-slate-200 dark:border-zinc-700 cursor-pointer hover:bg-slate-200 dark:hover:bg-zinc-700 transition active:scale-95" onClick={() => applyPrompt(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>

            <textarea
              className="w-full p-3.5 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950 text-slate-805 dark:text-zinc-150 text-xs md:text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 leading-normal"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={3}
              placeholder="Đặt câu hỏi cho Tutor..."
            />
            
            <div className="flex gap-2 mt-1">
              <button
                type="button"
                className="px-4 py-2.5 rounded-full text-xs font-bold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer active:scale-95 transition-all shadow-md shadow-teal-500/10"
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
              <button type="button" className="px-4 py-2.5 rounded-full text-xs font-bold bg-slate-100 dark:bg-zinc-800 text-slate-800 dark:text-zinc-200 border border-slate-200 dark:border-zinc-700 cursor-pointer active:scale-95 transition-all" onClick={() => setTutorThread([])}>
                Xoá hội thoại
              </button>
            </div>
          </div>
        </article>
      )}

      <footer className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <p className="text-xs text-slate-500 dark:text-zinc-400 max-w-xl">
          Learn Hub ưu tiên giáo dục và quản trị rủi ro. Nội dung hoàn toàn phục vụ học tập, không cấu thành khuyến nghị mua/bán hay đầu tư.
        </p>
        <div>
          {onOpenAdmin && (
            <button type="button" className="px-3.5 py-2 rounded-lg text-xs font-bold border border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-850 cursor-pointer active:scale-95 transition" onClick={onOpenAdmin}>
              Mở Content Ops
            </button>
          )}
        </div>
      </footer>

      <FloatingAssistant sessionId={sessionId} surface="learning" surfaceLabel="Learn Hub" />
      </div>
    </motion.section>
  )
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

function BookCoverPreview({ item }) {
  if (item.cover_url) {
    return <img src={item.cover_url} alt={`Bìa ${item.title}`} />
  }
  const isPdf = /\.pdf$/i.test(item.file_name || '')
  if (isPdf) {
    return (
      <div className="w-full h-full relative overflow-hidden">
        <iframe
          src={`${item.url}#page=1&view=FitH&zoom=page-width`}
          title={`preview-${item.title}`}
          loading="lazy"
          className="w-full h-full border-0 absolute inset-0"
        />
      </div>
    )
  }
  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-3 text-center bg-slate-100 dark:bg-zinc-800 text-slate-500">
      <small className="text-[9px] font-bold uppercase tracking-wider">BOOK</small>
      <span className="text-xs font-semibold mt-1.5 leading-snug line-clamp-3">{shortTitle(item.title, 38)}</span>
    </div>
  )
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
    if (kind === 'video') return <PlayIcon size={24} />
    if (kind === 'book') return <BookIcon size={24} />
    if (kind === 'paper') return <FileTextIcon size={24} />
    if (kind === 'course') return <TargetIcon size={24} />
    return <span>{kind.toUpperCase()}</span>
  }

  return (
    <article className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-3 hover:shadow transition-all duration-300">
      <div className="w-full h-36 rounded-xl bg-slate-50 dark:bg-zinc-950 border border-slate-100 dark:border-zinc-850 overflow-hidden flex items-center justify-center shrink-0">
        {thumbnail ? (
          <img src={thumbnail} alt="" loading="lazy" className="w-full h-full object-cover" />
        ) : (
          <div className="text-teal-600 dark:text-teal-400">
            {renderIcon()}
          </div>
        )}
      </div>
      <div className="flex-1 flex flex-col gap-2 min-h-0">
        <strong className="block text-xs font-bold text-slate-900 dark:text-white leading-snug line-clamp-2">{title}</strong>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 border border-teal-100 dark:border-teal-900/10">{kindLabel(kind)}</span>
          <small className="text-[10px] text-slate-500 dark:text-zinc-400 font-medium truncate">{meta.join(' · ')}</small>
        </div>
        {description ? (
          <p className="text-[11px] text-slate-550 dark:text-zinc-400 leading-relaxed line-clamp-3">
            {description}
          </p>
        ) : null}
      </div>
      <div className="flex gap-2 pt-2 border-t border-slate-100 dark:border-zinc-850 mt-auto">
        <a className="flex-1 px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-600 text-white text-[10px] font-bold text-center transition cursor-pointer" href={item.url} target="_blank" rel="noreferrer">
          Mở tài liệu
        </a>
        {downloadUrl ? (
          <a className="flex-1 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-zinc-800 hover:bg-slate-200 text-slate-700 dark:text-zinc-300 border border-slate-200 dark:border-zinc-700 text-[10px] font-bold text-center transition cursor-pointer" href={downloadUrl} target="_blank" rel="noreferrer">
            Tải PDF
          </a>
        ) : null}
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
        icon: <BookIcon size={14} />,
      }]
  const courseCards = courseRows.length
    ? courseRows.map((course, index) => ({
        title: course.title,
        meta: `${course.lesson_count} lessons · ${tierLabel(course.tier)}`,
        tag: 'Course',
        progress: course.progress_pct,
        tone: ['navy', 'emerald', 'purple', 'amber', 'paper'][index % 5],
        icon: topicIcon(course.tier, index, 14),
      }))
    : pathLessons.map((item, index) => ({
        title: item.title,
        meta: `${contentTypeLabel(item.content_type)} · ${item.estimated_minutes}m`,
        tag: item.status === 'completed' ? 'Done' : 'Lesson',
        progress: item.status === 'completed' ? 100 : item.is_next ? Math.max(10, completion) : 0,
        tone: ['navy', 'emerald', 'purple', 'amber', 'paper'][index % 5],
        icon: <BookIcon size={14} />,
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
    weeklyProgress: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((day, index) => {
      const minutes = 18 + ((completion + index * 8) % 25)
      return { day, minutes, height: Math.min(100, Math.round((minutes / 45) * 100)) }
    }),
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

function topicIcon(tier, index = 0, size = 14) {
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
