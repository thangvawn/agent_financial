import { accountStorageKey } from '../../../shared/auth/accountContext'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  BarChart3,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Clock3,
  Flag,
  Highlighter,
  ListChecks,
  MinusCircle,
  RotateCcw,
  Target,
  X,
} from 'lucide-react'

import { getQuestionStatus, MOCK_EXAM } from '../content/mockExamData'
import './mock-exam-room.css'

const storageKey = owner => accountStorageKey(owner, `mock-exam:v2:${MOCK_EXAM.id}`)

function readSavedState(owner) {
  if (!owner || typeof window === 'undefined') return null
  try {
    const saved = JSON.parse(window.localStorage.getItem(storageKey(owner)) || 'null')
    if (!saved || saved.examId !== MOCK_EXAM.id || saved.mode !== 'running' || !saved.startedAt) return null
    return saved
  } catch {
    return null
  }
}

function initialSavedState(owner) {
  const saved = readSavedState(owner)
  if (!saved) return null
  const elapsed = Math.floor((Date.now() - Number(saved.startedAt)) / 1000)
  return {
    ...saved,
    remaining: Math.max(0, MOCK_EXAM.timeLimitSeconds - elapsed),
    answers: saved.answers && typeof saved.answers === 'object' ? saved.answers : {},
    flags: new Set(Array.isArray(saved.flags) ? saved.flags : []),
    highlighted: new Set(Array.isArray(saved.highlighted) ? saved.highlighted : []),
    eliminated: saved.eliminated && typeof saved.eliminated === 'object' ? saved.eliminated : {},
  }
}

function formatTime(totalSeconds) {
  const safe = Math.max(0, Number(totalSeconds) || 0)
  const minutes = Math.floor(safe / 60)
  const seconds = safe % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function readSavedAnswers(value) {
  return value && typeof value === 'object' ? value : {}
}

function readSavedSet(value) {
  return new Set(Array.isArray(value) ? value : [])
}

export default function MockExamRoomPage({ onBack, accountId }) {
  const key = storageKey(accountId)
  const resumed = useMemo(() => initialSavedState(accountId), [accountId])
  const [mode, setMode] = useState(resumed ? 'running' : 'lobby')
  const [attemptMode, setAttemptMode] = useState(resumed?.attemptMode === 'practice' ? 'practice' : 'exam')
  const [startedAt, setStartedAt] = useState(resumed?.startedAt || null)
  const [remaining, setRemaining] = useState(resumed?.remaining ?? MOCK_EXAM.timeLimitSeconds)
  const [currentIndex, setCurrentIndex] = useState(resumed?.currentIndex || 0)
  const [answers, setAnswers] = useState(() => readSavedAnswers(resumed?.answers))
  const [flags, setFlags] = useState(() => readSavedSet(resumed?.flags ? [...resumed.flags] : []))
  const [highlighted, setHighlighted] = useState(() => readSavedSet(resumed?.highlighted ? [...resumed.highlighted] : []))
  const [eliminated, setEliminated] = useState(() => resumed?.eliminated || {})
  const [textSize, setTextSize] = useState('normal')
  const [isRailOpen, setIsRailOpen] = useState(false)
  const [modal, setModal] = useState(null)
  const [result, setResult] = useState(null)

  const question = MOCK_EXAM.questions[currentIndex] || MOCK_EXAM.questions[0]
  const sessionSize = MOCK_EXAM.sessionQuestionCount || Math.ceil(MOCK_EXAM.questions.length / 2)
  const sessionNumber = (MOCK_EXAM.sessionNumber || 1) + Math.floor(currentIndex / sessionSize)
  const sessionQuestionNumber = (currentIndex % sessionSize) + 1
  const answeredCount = Object.keys(answers).filter((id) => Boolean(answers[id])).length
  const flaggedCount = flags.size
  const progressPct = Math.round((answeredCount / MOCK_EXAM.questionCount) * 100)

  function startExam(selectedMode = 'exam') {
    const now = Date.now()
    const safeMode = selectedMode === 'practice' ? 'practice' : 'exam'
    setStartedAt(now)
    setAttemptMode(safeMode)
    setRemaining(MOCK_EXAM.timeLimitSeconds)
    setCurrentIndex(0)
    setAnswers({})
    setFlags(new Set())
    setHighlighted(new Set())
    setEliminated({})
    setResult(null)
    setModal(null)
    setMode('running')
  }

  const goToQuestion = useCallback((index) => {
    const safeIndex = Math.max(0, Math.min(MOCK_EXAM.questions.length - 1, index))
    setCurrentIndex(safeIndex)
    setIsRailOpen(false)
  }, [])

  const selectOption = useCallback((questionId, optionId) => {
    if (eliminated[questionId]?.includes(optionId)) return
    setAnswers((previous) => ({ ...previous, [questionId]: optionId }))
  }, [eliminated])

  const toggleFlag = useCallback((questionId) => {
    setFlags((previous) => {
      const next = new Set(previous)
      if (next.has(questionId)) next.delete(questionId)
      else next.add(questionId)
      return next
    })
  }, [])

  const toggleHighlight = useCallback((questionId) => {
    setHighlighted((previous) => {
      const next = new Set(previous)
      if (next.has(questionId)) next.delete(questionId)
      else next.add(questionId)
      return next
    })
  }, [])

  const toggleEliminate = useCallback((questionId, optionId) => {
    setEliminated((previous) => {
      const current = new Set(previous[questionId] || [])
      if (current.has(optionId)) current.delete(optionId)
      else current.add(optionId)
      const next = { ...previous }
      if (current.size) next[questionId] = [...current]
      else delete next[questionId]
      return next
    })
    if (answers[questionId] === optionId) {
      setAnswers((previous) => {
        const next = { ...previous }
        delete next[questionId]
        return next
      })
    }
  }, [answers])

  const calculateResult = useCallback((reason = 'manual', remainingOverride = null) => {
    const correctCount = MOCK_EXAM.questions.reduce(
      (count, item) => count + (answers[item.id] === item.correctOptionId ? 1 : 0),
      0,
    )
    const score = Math.round((correctCount / MOCK_EXAM.questionCount) * 100)
    const domainResults = MOCK_EXAM.questions.reduce((accumulator, item) => {
      const current = accumulator[item.domain] || { domain: item.domain, total: 0, correct: 0 }
      current.total += 1
      if (answers[item.id] === item.correctOptionId) current.correct += 1
      accumulator[item.domain] = current
      return accumulator
    }, {})
    return {
      score,
      correctCount,
      total: MOCK_EXAM.questionCount,
      answeredCount,
      flaggedCount,
      flaggedIds: [...flags],
      attemptMode,
      reason,
      timeUsed: MOCK_EXAM.timeLimitSeconds - (remainingOverride ?? remaining),
      domains: Object.values(domainResults).map((item) => ({ ...item, pct: Math.round((item.correct / item.total) * 100) })),
    }
  }, [answers, answeredCount, attemptMode, flaggedCount, flags, remaining])

  const finishExam = useCallback((reason = 'manual', remainingOverride = null) => {
    const nextResult = calculateResult(reason, remainingOverride)
    setResult(nextResult)
    setMode('submitted')
    setModal(null)
    if (key && typeof window !== 'undefined') {
      try { window.localStorage.removeItem(key) } catch { /* storage is optional */ }
    }
  }, [calculateResult, key])

  const finishExamRef = useRef(finishExam)
  useEffect(() => {
    finishExamRef.current = finishExam
  }, [finishExam])

  function requestSubmit() {
    if (answeredCount < MOCK_EXAM.questionCount) setModal('submit')
    else finishExam('manual')
  }

  function requestLeave() {
    if (mode === 'running') setModal('leave')
    else onBack?.()
  }

  useEffect(() => {
    if (mode !== 'running' || !startedAt) return undefined

    const tick = () => {
      const nextRemaining = Math.max(0, MOCK_EXAM.timeLimitSeconds - Math.floor((Date.now() - Number(startedAt)) / 1000))
      setRemaining(nextRemaining)
      if (nextRemaining === 0) finishExamRef.current('timeout', nextRemaining)
    }

    tick()
    const timer = window.setInterval(tick, 1000)
    return () => window.clearInterval(timer)
  }, [mode, startedAt])

  useEffect(() => {
    if (!key || mode !== 'running' || !startedAt || typeof window === 'undefined') return
    const payload = {
      examId: MOCK_EXAM.id,
      mode,
      startedAt,
      attemptMode,
      currentIndex,
      remaining,
      answers,
      flags: [...flags],
      highlighted: [...highlighted],
      eliminated,
    }
    try { window.localStorage.setItem(key, JSON.stringify(payload)) } catch { /* storage is optional */ }
  }, [answers, attemptMode, currentIndex, eliminated, flags, highlighted, mode, remaining, startedAt, key])

  useEffect(() => {
    if (mode !== 'running') return undefined
    function handleKeyDown(event) {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return
      if (event.key === 'ArrowRight') { event.preventDefault(); goToQuestion(Math.min(MOCK_EXAM.questions.length - 1, currentIndex + 1)) }
      if (event.key === 'ArrowLeft') { event.preventDefault(); goToQuestion(Math.max(0, currentIndex - 1)) }
      if (event.key.toLowerCase() === 'f') { event.preventDefault(); toggleFlag(question.id) }
      if (event.key.toLowerCase() === 'h') { event.preventDefault(); toggleHighlight(question.id) }
      if (/^[1-3]$/.test(event.key)) {
        const option = question.options[Number(event.key) - 1]
        if (option) selectOption(question.id, option.id)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, goToQuestion, mode, question, selectOption, toggleFlag, toggleHighlight])

  if (mode === 'lobby') {
    return <ExamLobby onBack={onBack} onStart={startExam} />
  }

  if (mode === 'submitted') {
    return (
      <ExamResult
        result={result}
        answers={answers}
        onBack={onBack}
        onRetry={startExam}
      />
    )
  }

  return (
    <section className={`mock-room mock-room--text-${textSize}`} data-domain="mock_exam" data-testid="mock-exam-room">
      <header className="mock-room__topbar">
        <button type="button" className="mock-room__exit" onClick={requestLeave} aria-label="Thoát phòng thi">
          <ArrowLeft size={17} aria-hidden="true" />
          <span>Thoát</span>
        </button>
        <div className="mock-room__identity">
          <span className="mock-room__kicker">{MOCK_EXAM.eyebrow} · SESSION {sessionNumber}/{MOCK_EXAM.sessionCount || 2}</span>
          <h1>{MOCK_EXAM.title}</h1>
        </div>
        <div className="mock-room__top-progress" aria-label={`Đã trả lời ${answeredCount} trên ${MOCK_EXAM.questionCount} câu`}>
          <span>Tiến độ</span>
          <strong>{answeredCount}/{MOCK_EXAM.questionCount}</strong>
          <div className="mock-room__progress-track"><span style={{ width: `${progressPct}%` }} /></div>
        </div>
        <div className={`mock-room__timer ${remaining <= 300 ? 'is-warning' : ''}`} aria-live="polite">
          <Clock3 size={17} aria-hidden="true" />
          <span>{formatTime(remaining)}</span>
        </div>
        <button type="button" className="mock-room__rail-toggle" onClick={() => setIsRailOpen((open) => !open)} aria-expanded={isRailOpen}>
          <ListChecks size={17} aria-hidden="true" />
          <span>Câu hỏi</span>
        </button>
      </header>

      <div className="mock-room__workspace">
        <aside className={`mock-room__rail ${isRailOpen ? 'is-open' : ''}`} aria-label="Điều hướng câu hỏi">
          <div className="mock-room__rail-head">
            <div>
              <span className="mock-room__section-label">NAVIGATOR</span>
              <h2>Câu hỏi</h2>
            </div>
            <button type="button" className="mock-room__rail-close" onClick={() => setIsRailOpen(false)} aria-label="Đóng danh sách câu hỏi"><X size={16} /></button>
          </div>
          <p className="mock-room__rail-note">Chọn số câu để chuyển nhanh. Màu xanh là đã trả lời, vàng là đang gắn cờ.</p>
          <div className="mock-room__question-grid">
            {MOCK_EXAM.questions.map((item, index) => {
              const status = getQuestionStatus(item, answers, flags)
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`mock-room__question-number is-${status} ${index === currentIndex ? 'is-current' : ''}`}
                  onClick={() => goToQuestion(index)}
                  aria-label={`Câu ${item.number}, ${statusLabel(status)}`}
                  aria-current={index === currentIndex ? 'step' : undefined}
                >
                  {item.number}
                  {status === 'flagged' ? <Flag size={11} aria-hidden="true" /> : null}
                </button>
              )
            })}
          </div>
          <div className="mock-room__legend">
            <span><i className="is-answered" /> Đã trả lời</span>
            <span><i className="is-flagged" /> Xem lại</span>
            <span><i className="is-unanswered" /> Chưa làm</span>
          </div>
          <div className="mock-room__rail-summary">
            <div><strong>{answeredCount}</strong><span>đã trả lời</span></div>
            <div><strong>{flaggedCount}</strong><span>gắn cờ</span></div>
            <div><strong>{MOCK_EXAM.questionCount - answeredCount}</strong><span>còn lại</span></div>
          </div>
        </aside>

        <main className="mock-room__main" aria-label="Nội dung câu hỏi">
          <div className="mock-room__main-head">
            <div>
              <span className="mock-room__section-label">SESSION {sessionNumber} · CÂU {sessionQuestionNumber} / {sessionSize} · TỔNG {question.number} / {MOCK_EXAM.questionCount}</span>
              <div className="mock-room__question-meta">
                <span>{question.domain}</span>
                <span className="mock-room__dot" aria-hidden="true">·</span>
                <span>{question.difficulty}</span>
              </div>
            </div>
            <span className="mock-room__shortcut-note">{attemptMode === 'practice' ? 'LUYỆN TẬP · giải thích hiện sau khi chọn' : 'THI THẬT · đáp án mở sau khi nộp'} · ← → chuyển câu · F gắn cờ</span>
          </div>

          <article className="mock-room__question-card">
            <div className="mock-room__question-card-top">
              <span className="mock-room__question-index">Q{String(question.number).padStart(2, '0')}</span>
              <span className="mock-room__question-status">{answers[question.id] ? 'Đã chọn đáp án' : 'Chưa trả lời'}</span>
            </div>
            <p className={`mock-room__prompt ${highlighted.has(question.id) ? 'is-highlighted' : ''}`}>{question.prompt}</p>
            <p className="mock-room__context">{question.context}</p>

            <div className="mock-room__options" role="radiogroup" aria-label={`Đáp án cho câu ${question.number}`}>
              {question.options.map((option, optionIndex) => {
                const isSelected = answers[question.id] === option.id
                const isEliminated = eliminated[question.id]?.includes(option.id)
                return (
                  <div key={option.id} className={`mock-room__option-wrap ${isSelected ? 'is-selected' : ''} ${isEliminated ? 'is-eliminated' : ''}`}>
                    <button
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      className="mock-room__option"
                      onClick={() => selectOption(question.id, option.id)}
                      disabled={isEliminated}
                    >
                      <span className="mock-room__option-key">{String.fromCharCode(65 + optionIndex)}</span>
                      <span className="mock-room__option-label">{option.label}</span>
                      {isSelected ? <CheckCircle2 size={18} aria-label="Đã chọn" /> : null}
                    </button>
                    <button
                      type="button"
                      className="mock-room__eliminate"
                      onClick={() => toggleEliminate(question.id, option.id)}
                      aria-label={`${isEliminated ? 'Bỏ gạch' : 'Gạch'} phương án ${String.fromCharCode(65 + optionIndex)}`}
                      aria-pressed={isEliminated}
                    >
                      <MinusCircle size={15} aria-hidden="true" />
                    </button>
                  </div>
                )
              })}
            </div>

            <div className="mock-room__tools">
              <button type="button" className={flags.has(question.id) ? 'is-active' : ''} onClick={() => toggleFlag(question.id)} aria-pressed={flags.has(question.id)}>
                <Flag size={16} aria-hidden="true" />
                {flags.has(question.id) ? 'Đã gắn cờ' : 'Gắn cờ xem lại'}
              </button>
              <button type="button" className={highlighted.has(question.id) ? 'is-active' : ''} onClick={() => toggleHighlight(question.id)} aria-pressed={highlighted.has(question.id)}>
                <Highlighter size={16} aria-hidden="true" />
                {highlighted.has(question.id) ? 'Bỏ nổi bật' : 'Nổi bật câu hỏi'}
              </button>
              <span className="mock-room__tool-hint">Phương án gạch bỏ sẽ không thể chọn.</span>
            </div>
            {attemptMode === 'practice' && answers[question.id] ? (
              <PracticeFeedback question={question} answerId={answers[question.id]} />
            ) : null}
          </article>

          <footer className="mock-room__bottom-bar">
            <div className="mock-room__font-controls" aria-label="Điều chỉnh cỡ chữ">
              <span>Cỡ chữ</span>
              {['small', 'normal', 'large'].map((size) => (
                <button key={size} type="button" className={textSize === size ? 'is-active' : ''} onClick={() => setTextSize(size)} aria-label={`Cỡ chữ ${size}`} aria-pressed={textSize === size}>
                  {size === 'small' ? 'A−' : size === 'large' ? 'A+' : 'A'}
                </button>
              ))}
            </div>
            <div className="mock-room__pager">
              <button type="button" onClick={() => goToQuestion(currentIndex - 1)} disabled={currentIndex === 0}>
                <ChevronLeft size={17} aria-hidden="true" /> Trước
              </button>
              {currentIndex === MOCK_EXAM.questions.length - 1 ? (
                <button type="button" className="is-submit" onClick={requestSubmit}><Check size={17} aria-hidden="true" /> Nộp bài</button>
              ) : (
                <button type="button" className="is-next" onClick={() => goToQuestion(currentIndex + 1)}>Tiếp theo <ChevronRight size={17} aria-hidden="true" /></button>
              )}
            </div>
          </footer>
        </main>
      </div>

      {modal ? (
        <ExamModal
          type={modal}
          unanswered={MOCK_EXAM.questionCount - answeredCount}
          flagged={flaggedCount}
          onClose={() => setModal(null)}
          attemptMode={attemptMode}
          onConfirm={modal === 'submit' ? () => finishExam('manual') : () => { setModal(null); onBack?.() }}
        />
      ) : null}
    </section>
  )
}

function ExamLobby({ onBack, onStart }) {
  const [selectedMode, setSelectedMode] = useState('exam')
  const domains = MOCK_EXAM.topicWeights || [...new Set(MOCK_EXAM.questions.map((item) => item.domain))].map((domain) => ({ domain }))
  return (
    <section className="mock-room mock-room--lobby" data-domain="mock_exam_lobby">
      <div className="mock-room__lobby-nav">
        <button type="button" className="mock-room__exit" onClick={onBack}><ArrowLeft size={17} aria-hidden="true" /> <span>Về Learn Hub</span></button>
        <span className="mock-room__lobby-mark"><Target size={16} aria-hidden="true" /> NORTHSTAR · CFA PRACTICE ROOM</span>
      </div>
      <div className="mock-room__lobby-grid">
        <div className="mock-room__lobby-copy">
          <span className="mock-room__kicker">{MOCK_EXAM.program} · {MOCK_EXAM.levelLabel} · BLUEPRINT {MOCK_EXAM.blueprintYear}</span>
          <h1>{MOCK_EXAM.title}</h1>
          <p>{MOCK_EXAM.description}</p>
          <div className="mock-room__mode-picker" aria-label="Chọn cách làm bài">
            <button
              type="button"
              className={`mock-room__mode-option ${selectedMode === 'exam' ? 'is-selected' : ''}`}
              onClick={() => setSelectedMode('exam')}
              aria-pressed={selectedMode === 'exam'}
            >
              <span className="mock-room__mode-option-title">Thi thử</span>
              <span>Chấm và mở lời giải sau khi nộp</span>
            </button>
            <button
              type="button"
              className={`mock-room__mode-option ${selectedMode === 'practice' ? 'is-selected' : ''}`}
              onClick={() => setSelectedMode('practice')}
              aria-pressed={selectedMode === 'practice'}
            >
              <span className="mock-room__mode-option-title">Luyện tập</span>
              <span>Xem đáp án và giải thích ngay sau mỗi câu</span>
            </button>
          </div>
          <div className="mock-room__lobby-actions">
            <button type="button" className="mock-room__primary-cta" onClick={() => onStart(selectedMode)}>{selectedMode === 'practice' ? 'Bắt đầu luyện tập' : 'Bắt đầu phòng thi'} <ChevronRight size={18} aria-hidden="true" /></button>
            <span className="mock-room__autosave-note">Không cần đăng ký thêm · tiến độ tự lưu trên thiết bị</span>
          </div>
        </div>
        <div className="mock-room__lobby-card">
          <div className="mock-room__lobby-card-head"><span>THÔNG SỐ PHIÊN THI</span><BarChart3 size={18} aria-hidden="true" /></div>
          <div className="mock-room__lobby-stats">
            <div><strong>{MOCK_EXAM.questionCount}</strong><span>Câu / session</span></div>
            <div><strong>{Math.round(MOCK_EXAM.timeLimitSeconds / 60)}′</strong><span>Thời lượng</span></div>
            <div><strong>{MOCK_EXAM.benchmarkScore}%</strong><span>Benchmark học tập</span></div>
          </div>
          <div className="mock-room__lobby-divider" />
          <div className="mock-room__format-note">
            <span>FORMAT CHÍNH THỨC</span>
            <strong>{MOCK_EXAM.officialFormat}</strong>
            <small>{MOCK_EXAM.scaledFormat}</small>
          </div>
          <div className="mock-room__lobby-divider" />
          <div className="mock-room__lobby-domains">
            <span>10 topic trong blueprint {MOCK_EXAM.blueprintYear}</span>
            <div>{domains.map(({ domain, weight }) => <span key={domain} title={weight || ''}>{domain}{weight ? ` · ${weight}` : ''}</span>)}</div>
          </div>
        </div>
      </div>
      <div className="mock-room__instruction-grid">
        {MOCK_EXAM.instructions.map((instruction, index) => (
          <div key={instruction} className="mock-room__instruction"><span>0{index + 1}</span><p>{instruction}</p></div>
        ))}
      </div>
      <p className="mock-room__disclaimer"><CircleAlert size={15} aria-hidden="true" /> <span>Nội dung do Northstar tự biên soạn theo blueprint công khai để học tập; không phải đề chính thức và không được CFA Institute hay AlphaMock bảo trợ. <a href={MOCK_EXAM.officialSourceUrl} target="_blank" rel="noreferrer">Format CFA</a> · <a href={MOCK_EXAM.publicSampleUrl} target="_blank" rel="noreferrer">Sample CFA công khai</a> · <a href={MOCK_EXAM.alphaMockUrl} target="_blank" rel="noreferrer">Mở đề AlphaMock</a></span></p>
    </section>
  )
}

function ExamResult({ result, answers, onBack, onRetry }) {
  const [reviewFilter, setReviewFilter] = useState('all')
  if (!result) return null
  const weakest = [...result.domains].sort((a, b) => a.pct - b.pct)[0]
  const reviewItems = MOCK_EXAM.questions.filter((item) => {
    const isAnswered = Boolean(answers[item.id])
    const isCorrect = answers[item.id] === item.correctOptionId
    if (reviewFilter === 'wrong') return isAnswered && !isCorrect
    if (reviewFilter === 'unanswered') return !isAnswered
    if (reviewFilter === 'flagged') return result.flaggedIds?.includes(item.id)
    return true
  })
  const reviewCounts = {
    all: MOCK_EXAM.questions.length,
    wrong: MOCK_EXAM.questions.filter((item) => answers[item.id] && answers[item.id] !== item.correctOptionId).length,
    unanswered: MOCK_EXAM.questions.filter((item) => !answers[item.id]).length,
    flagged: result.flaggedIds?.length || 0,
  }
  return (
    <section className="mock-room mock-room--result" data-domain="mock_exam_result">
      <header className="mock-room__result-topbar">
        <button type="button" className="mock-room__exit" onClick={onBack}><ArrowLeft size={17} aria-hidden="true" /> <span>Về Learn Hub</span></button>
        <span className="mock-room__lobby-mark"><Target size={16} aria-hidden="true" /> KẾT QUẢ PHÒNG THI</span>
      </header>
      <main className="mock-room__result-content">
        <div className="mock-room__result-hero">
          <div>
            <span className="mock-room__kicker">ĐÃ HOÀN THÀNH · {result.reason === 'timeout' ? 'HẾT GIỜ' : 'BẠN ĐÃ NỘP BÀI'}</span>
            <h1>{result.score >= MOCK_EXAM.benchmarkScore ? 'Nền tảng đang đi đúng hướng.' : 'Bạn đã có bản đồ để học tiếp.'}</h1>
            <p>Điểm tổng chỉ là benchmark học tập, không phải MPS hay kết quả của CFA Institute. {result.attemptMode === 'practice' ? 'Bạn đã luyện với lời giải tức thì.' : 'Bạn đã hoàn thành chế độ thi thử.'} Hãy xem topic nào cần được củng cố trước khi làm phiên tiếp theo.</p>
          </div>
          <div className={`mock-room__score-ring ${result.score >= MOCK_EXAM.benchmarkScore ? 'is-benchmark' : 'is-review'}`}>
            <strong>{result.score}</strong><span>/ 100</span>
          </div>
        </div>
        <div className="mock-room__result-summary">
          <div><CheckCircle2 size={17} aria-hidden="true" /><strong>{result.correctCount}/{result.total}</strong><span>câu đúng</span></div>
          <div><Clock3 size={17} aria-hidden="true" /><strong>{formatTime(result.timeUsed)}</strong><span>thời gian dùng</span></div>
          <div><ListChecks size={17} aria-hidden="true" /><strong>{result.answeredCount}/{result.total}</strong><span>đã trả lời</span></div>
          <div><Flag size={17} aria-hidden="true" /><strong>{result.flaggedCount}</strong><span>câu gắn cờ</span></div>
        </div>
        <div className="mock-room__result-grid">
          <section className="mock-room__result-panel">
            <div className="mock-room__result-panel-head"><div><span className="mock-room__section-label">NĂNG LỰC</span><h2>Chân dung hiện tại</h2></div><BarChart3 size={19} aria-hidden="true" /></div>
            <div className="mock-room__domain-results">
              {result.domains.map((item) => (
                <div key={item.domain} className="mock-room__domain-row">
                  <div><span>{item.domain}</span><strong>{item.correct}/{item.total}</strong></div>
                  <div className="mock-room__domain-track"><span style={{ width: `${item.pct}%` }} /></div>
                </div>
              ))}
            </div>
            <div className="mock-room__weakest"><CircleAlert size={17} aria-hidden="true" /><p><strong>Ưu tiên ôn lại: {weakest?.domain}.</strong> Mở bài học liên quan rồi quay lại làm lại đề để kiểm tra mức tiến bộ.</p></div>
          </section>
          <section className="mock-room__result-panel mock-room__result-panel--actions">
            <span className="mock-room__section-label">BƯỚC TIẾP THEO</span>
            <h2>Biến kết quả thành hành động</h2>
            <p>Đọc lại giải thích cho câu sai và ghi lại một điều bạn sẽ kiểm chứng trong dữ liệu thực tế.</p>
            <button type="button" className="mock-room__primary-cta" onClick={onRetry}><RotateCcw size={17} aria-hidden="true" /> Làm lại phòng thi</button>
            <button type="button" className="mock-room__secondary-cta" onClick={onBack}><ArrowLeft size={17} aria-hidden="true" /> Chọn bài học để ôn</button>
          </section>
        </div>
        <section className="mock-room__review">
          <div className="mock-room__result-panel-head"><div><span className="mock-room__section-label">REVIEW</span><h2>Giải thích từng câu</h2></div><span className="mock-room__review-caption">{result.attemptMode === 'practice' ? 'Bạn đã xem phản hồi trong lúc luyện' : 'Chỉ hiển thị sau khi nộp bài'}</span></div>
          <div className="mock-room__review-filters" role="group" aria-label="Lọc câu hỏi cần xem lại">
            {[['all', 'Tất cả'], ['wrong', 'Câu sai'], ['unanswered', 'Chưa trả lời'], ['flagged', 'Đã gắn cờ']].map(([key, label]) => (
              <button key={key} type="button" className={reviewFilter === key ? 'is-active' : ''} onClick={() => setReviewFilter(key)} aria-pressed={reviewFilter === key}>
                {label} <span>{reviewCounts[key]}</span>
              </button>
            ))}
          </div>
          <div className="mock-room__review-list">
            {reviewItems.length ? reviewItems.map((item) => {
              const chosen = item.options.find((option) => option.id === answers[item.id])
              const correct = item.options.find((option) => option.id === item.correctOptionId)
              const isCorrect = answers[item.id] === item.correctOptionId
              return (
                <article key={item.id} className={`mock-room__review-item ${isCorrect ? 'is-correct' : 'is-wrong'}`}>
                  <div className="mock-room__review-marker">{isCorrect ? <Check size={15} aria-hidden="true" /> : <X size={15} aria-hidden="true" />}</div>
                  <div className="mock-room__review-copy"><div><span className="mock-room__review-number">Câu {item.number}</span><span className="mock-room__review-domain">{item.domain}</span></div><h3>{item.prompt}</h3><p>{item.explanation}</p><small>{isCorrect ? `Bạn chọn: ${chosen?.label || '—'}` : `Bạn chọn: ${chosen?.label || 'Chưa trả lời'} · Đáp án: ${correct?.label}`}</small><em>{item.takeaway}</em></div>
                </article>
              )
            }) : <p className="mock-room__review-empty">Không có câu nào trong bộ lọc này.</p>}
          </div>
        </section>
      </main>
    </section>
  )
}

function PracticeFeedback({ question, answerId }) {
  const isCorrect = answerId === question.correctOptionId
  const correct = question.options.find((option) => option.id === question.correctOptionId)
  return (
    <aside className={`mock-room__practice-feedback ${isCorrect ? 'is-correct' : 'is-wrong'}`} aria-live="polite">
      <div className="mock-room__practice-feedback-head">
        {isCorrect ? <CheckCircle2 size={18} aria-hidden="true" /> : <CircleAlert size={18} aria-hidden="true" />}
        <strong>{isCorrect ? 'Đúng — tiếp tục giữ nhịp.' : `Chưa đúng — đáp án là ${correct?.label || '—'}.`}</strong>
      </div>
      <p>{question.explanation}</p>
      <em>{question.takeaway}</em>
    </aside>
  )
}

function ExamModal({ type, unanswered, flagged, attemptMode, onClose, onConfirm }) {
  const isSubmit = type === 'submit'
  return (
    <div className="mock-room__modal-backdrop" role="presentation">
      <div className="mock-room__modal" role="dialog" aria-modal="true" aria-labelledby="mock-modal-title">
        <span className="mock-room__modal-icon">{isSubmit ? <CheckCircle2 size={20} aria-hidden="true" /> : <CircleAlert size={20} aria-hidden="true" />}</span>
        <h2 id="mock-modal-title">{isSubmit ? 'Nộp bài ngay?' : 'Rời phòng thi?'}</h2>
        <p>{isSubmit ? `Bạn còn ${unanswered} câu chưa trả lời${flagged ? ` và ${flagged} câu đang gắn cờ` : ''}. ${attemptMode === 'practice' ? 'Kết quả sẽ được tổng hợp sau khi nộp.' : 'Sau khi nộp, đáp án và giải thích sẽ được mở.'}` : 'Tiến độ hiện tại đã được lưu trên thiết bị. Bạn có thể quay lại để tiếp tục phiên này.'}</p>
        <div className="mock-room__modal-actions"><button type="button" className="mock-room__secondary-cta" onClick={onClose}>{isSubmit ? 'Quay lại làm' : 'Ở lại phòng thi'}</button><button type="button" className="mock-room__primary-cta" onClick={onConfirm}>{isSubmit ? 'Nộp bài' : 'Rời phòng thi'}</button></div>
      </div>
    </div>
  )
}

function statusLabel(status) {
  if (status === 'flagged') return 'đang gắn cờ'
  if (status === 'answered') return 'đã trả lời'
  return 'chưa làm'
}
