import { useState } from 'react'
import { Check, Eye, HelpCircle, RotateCcw, Send, Sparkles } from 'lucide-react'

const QUESTION_ORDER = [
  'gross_margin_pct',
  'current_ratio',
  'quick_ratio',
  'roe_pct',
  'roa_pct',
  'ocf_to_net_income',
  'fcf_margin_pct',
  'debt_to_equity',
  'inventory_days',
  'receivable_days',
]

function finite(value) {
  if (value === null || value === undefined || typeof value === 'boolean') return null
  const normalized = typeof value === 'string'
    ? value.trim().replace(/\s+/g, '').replace(',', '.')
    : value
  if (normalized === '') return null
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function tolerance(value, unit) {
  const absolute = Math.abs(value)
  if (unit === '%') return Math.max(0.15, absolute * 0.015)
  if (unit === 'ngày') return Math.max(0.75, absolute * 0.02)
  if (unit === 'x') return Math.max(0.03, absolute * 0.015)
  return Math.max(1, absolute * 0.01)
}

function formatAnswer(value, unit) {
  const parsed = finite(value)
  if (parsed === null) return '—'
  if (unit === 'VND') {
    const absolute = Math.abs(parsed)
    const divisor = absolute >= 1e12 ? 1e12 : absolute >= 1e9 ? 1e9 : absolute >= 1e6 ? 1e6 : 1
    const suffix = divisor === 1e12 ? ' nghìn tỷ' : divisor === 1e9 ? ' tỷ' : divisor === 1e6 ? ' triệu' : ''
    return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: divisor === 1 ? 0 : 2 }).format(parsed / divisor)}${suffix}`
  }
  const digits = unit === '%' ? 2 : unit === 'ngày' ? 1 : 3
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: digits }).format(parsed)}${unit === '%' ? '%' : unit ? ` ${unit}` : ''}`
}

function candidateQuestions(company) {
  const available = new Map((company?.calculated_fields || []).map((item) => [item.field, item]))
  const ordered = QUESTION_ORDER
    .map((field) => available.get(field))
    .filter((item) => item?.status === 'calculated' && finite(item.value) !== null)
  const rest = (company?.calculated_fields || []).filter((item) => item.status === 'calculated' && finite(item.value) !== null && !ordered.includes(item))
  return [...ordered, ...rest].slice(0, 3)
}

function rawValueMap(company) {
  return new Map((company?.raw_inputs || []).map((item) => [item.field, item]))
}

export default function RawDataChallenge({ company, onComplete }) {
  const questions = candidateQuestions(company)
  const [activeIndex, setActiveIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [completed, setCompleted] = useState(false)
  const raw = rawValueMap(company)
  const question = questions[activeIndex]

  if (!questions.length) {
    return <section className="rdc-card rdc-card--empty" aria-label="Bài tập raw data"><HelpCircle size={18} /><div><strong>Chưa đủ raw data để tạo bài tính</strong><p>Hãy kiểm tra độ phủ dữ liệu trước khi đưa ra kết luận.</p></div></section>
  }

  function submitAnswer(event) {
    event.preventDefault()
    const expected = finite(question.value)
    const submitted = finite(answer)
    if (submitted === null) {
      setFeedback({ kind: 'invalid', message: 'Nhập một số hợp lệ trước khi kiểm tra.' })
      return
    }
    const delta = Math.abs(submitted - expected)
    const correct = delta <= tolerance(expected, question.unit)
    setFeedback({ kind: correct ? 'correct' : 'incorrect', delta, expected, message: correct ? 'Đúng. Bạn đã tính đúng từ raw data.' : 'Chưa khớp. Kiểm tra lại tử số, mẫu số và đơn vị.' })
  }

  function nextQuestion() {
    if (activeIndex >= questions.length - 1) {
      setCompleted(true)
      onComplete?.()
      return
    }
    setActiveIndex((value) => value + 1)
    setAnswer('')
    setFeedback(null)
    setRevealed(false)
  }

  function revealAnswer() {
    setRevealed(true)
    setFeedback({ kind: 'revealed', expected: finite(question.value), message: 'Đã mở đáp án tham chiếu. Hãy viết lại phép tính bằng lời của bạn.' })
  }

  function resetChallenge() {
    setActiveIndex(0)
    setAnswer('')
    setFeedback(null)
    setRevealed(false)
    setCompleted(false)
    onComplete?.(false)
  }

  const dependencies = question.dependencies || []
  return <section className={`rdc-card${completed ? ' is-complete' : ''}`} aria-labelledby="rdc-title">
    <header className="rdc-heading">
      <div><span className="rdc-eyebrow"><Sparkles size={13} /> RAW DATA CHALLENGE</span><h3 id="rdc-title">Tự tính {question.label}</h3><p>Nhìn khoản mục gốc trước, tự nhập kết quả rồi mới xem đáp án tham chiếu.</p></div>
      <span className="rdc-progress">{completed ? <><Check size={13} /> Đã hoàn thành</> : `Bài ${activeIndex + 1}/${questions.length}`}</span>
    </header>
    <div className="rdc-context">
      <div className="rdc-formula"><span>CÔNG THỨC</span><code>{question.formula || 'Công thức theo dữ liệu dẫn xuất'}</code></div>
      <div className="rdc-dependency-list"><span>KHOẢN MỤC GỐC</span><div>{dependencies.map((field) => { const item = raw.get(field); return <span className={item?.value == null ? 'is-missing' : ''} key={field}>{item?.label || field}: <b>{item?.value == null ? '—' : formatAnswer(item.value, item.unit)}</b></span> })}</div></div>
    </div>
    <form className="rdc-answer-form" onSubmit={submitAnswer}>
      <label><span>Kết quả của bạn</span><div><input autoComplete="off" inputMode="decimal" type="number" step="any" value={answer} onChange={(event) => { setAnswer(event.target.value); setFeedback(null) }} placeholder="Nhập kết quả…" aria-label={`Kết quả ${question.label}`} /><b>{question.unit || 'giá trị'}</b></div></label>
      <button type="submit" className="rdc-submit" disabled={!answer.trim()}><Send size={14} /> Kiểm tra</button>
    </form>
    {feedback && <div className={`rdc-feedback is-${feedback.kind}`} role="status" aria-live="polite"><span>{feedback.kind === 'correct' ? <Check size={15} /> : feedback.kind === 'revealed' ? <Eye size={15} /> : <HelpCircle size={15} />}</span><div><strong>{feedback.message}</strong>{feedback.expected !== undefined && <small>Đáp án tham chiếu: {formatAnswer(feedback.expected, question.unit)}{feedback.delta !== undefined ? ` · sai lệch ${formatAnswer(feedback.delta, question.unit)}` : ''}</small>}</div></div>}
    <footer className="rdc-actions">
      {!feedback || feedback.kind === 'incorrect' || feedback.kind === 'invalid' ? <button type="button" className="rdc-reveal" onClick={revealAnswer} disabled={revealed}><Eye size={14} /> Xem đáp án tham chiếu</button> : null}
      {feedback && (feedback.kind === 'correct' || feedback.kind === 'revealed') && !completed ? <button type="button" className="rdc-next" onClick={nextQuestion}>{activeIndex === questions.length - 1 ? 'Hoàn thành bài tính' : 'Sang khoản mục tiếp theo'} <Check size={14} /></button> : null}
      {completed ? <button type="button" className="rdc-reset" onClick={resetChallenge}><RotateCcw size={14} /> Làm lại</button> : null}
    </footer>
  </section>
}
