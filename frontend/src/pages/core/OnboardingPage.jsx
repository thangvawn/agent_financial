import { useState } from 'react'
import { completeOnboarding, startOnboarding, submitOnboardingAnswers } from '../../modules/home-onboarding'

const QUESTIONS = [
  {
    key: 'primary_goal',
    label: 'Bạn đến đây chủ yếu để làm gì?',
    options: [
      ['understand_finance_basics', 'Hiểu tài chính cơ bản'],
      ['manage_household_money', 'Quản lý tiền cá nhân/gia đình'],
      ['learn_investing_safely', 'Học đầu tư an toàn hơn'],
      ['deep_analysis_tools', 'Dùng công cụ phân tích sâu hơn'],
    ],
  },
  {
    key: 'knowledge_level',
    label: 'Bạn đang ở mức nào?',
    options: [
      ['beginner', 'Gần như mới bắt đầu'],
      ['basic', 'Biết một ít khái niệm cơ bản'],
      ['intermediate', 'Đã từng đầu tư / theo dõi thị trường'],
      ['advanced', 'Khá quen với phân tích và công cụ'],
    ],
  },
  {
    key: 'primary_interest',
    label: 'Điều bạn quan tâm nhất lúc này là gì?',
    options: [
      ['basics', 'Hiểu nền tảng tài chính'],
      ['cashflow', 'Kiểm soát dòng tiền'],
      ['emergency_fund', 'Lập quỹ dự phòng'],
      ['investing_basics', 'Học đầu tư cơ bản'],
      ['markets', 'Theo dõi thị trường / cổ phiếu'],
    ],
  },
  {
    key: 'current_state',
    label: 'Tình trạng hiện tại gần nhất với bạn là gì?',
    options: [
      ['no_clear_financial_system', 'Chưa quản lý tài chính rõ ràng'],
      ['income_no_long_term_plan', 'Có thu nhập nhưng chưa có kế hoạch dài hạn'],
      ['already_saving_wants_to_invest', 'Đã tiết kiệm và muốn đầu tư'],
      ['already_investing_wants_structure', 'Đã đầu tư và muốn làm bài bản hơn'],
    ],
  },
  {
    key: 'risk_tolerance_prelim',
    label: 'Bạn thường nghiêng về cách nào?',
    options: [
      ['very_cautious', 'Muốn an toàn, hiểu kỹ rồi mới làm'],
      ['moderate', 'Chấp nhận rủi ro vừa phải nếu có giải thích rõ'],
      ['balanced', 'Sẵn sàng thử nhưng muốn công cụ hỗ trợ'],
      ['advanced', 'Đã quen với biến động và cần dữ liệu sâu hơn'],
    ],
  },
]

const shellClass = 'mx-auto flex w-full max-w-7xl flex-col gap-5 rounded-[28px] border border-slate-200/70 bg-white/90 p-6 text-slate-800 shadow-[0_18px_45px_rgba(15,23,42,0.08)]'
const inputClass = 'mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-100'
const primaryButtonClass = 'inline-flex items-center rounded-full bg-teal-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-55'
const secondaryButtonClass = 'inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100'

export default function OnboardingPage({
  onCompleted,
  onOpenHome,
  onOpenGlobalTerminal,
  onOpenInsights,
  onOpenGuidedInvesting,
  onOpenProLab,
}) {
  const [sessionId, setSessionId] = useState('')
  const [answers, setAnswers] = useState({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const answeredCount = Object.keys(answers).length
  const completionPct = Math.round((answeredCount / QUESTIONS.length) * 100)

  async function ensureSession() {
    if (sessionId) return sessionId
    const payload = await startOnboarding()
    setSessionId(payload.session_id)
    return payload.session_id
  }

  async function handleComplete() {
    setLoading(true)
    setError('')
    try {
      const sid = await ensureSession()
      await submitOnboardingAnswers(sid, answers)
      const payload = await completeOnboarding(sid)
      if (onCompleted) onCompleted(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className={shellClass}>
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-amber-700">Northstar</p>
          <p className="text-lg font-semibold text-slate-900">Onboarding Engine</p>
        </div>
        <nav className="flex flex-wrap gap-2" aria-label="Onboarding navigation tabs">
          <button type="button" className={primaryButtonClass} disabled>Onboarding</button>
          <button type="button" className={secondaryButtonClass} onClick={onOpenHome}>Home</button>
          <button type="button" className={secondaryButtonClass} onClick={onOpenGlobalTerminal}>Global Terminal</button>
          <button type="button" className={secondaryButtonClass} onClick={onOpenInsights}>Insights</button>
          <button type="button" className={secondaryButtonClass} onClick={() => onOpenGuidedInvesting?.('market_context')}>Guided Investing</button>
          <button type="button" className={secondaryButtonClass} onClick={onOpenProLab}>Pro Lab</button>
        </nav>
        <div className="min-w-[180px]">
          <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-600">
            <span>{answeredCount}/{QUESTIONS.length}</span>
            <span>{completionPct}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-teal-600 transition-all duration-300" style={{ width: `${completionPct}%` }} />
          </div>
        </div>
      </header>

      <section className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">Khởi tạo nhịp đi đúng từ đầu</p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight text-slate-900">Bắt đầu từ điều phù hợp với bạn</h1>
        <p className="mt-3 max-w-3xl text-sm text-slate-600">
          Chỉ mất khoảng 1 phút để chúng tôi đưa bạn vào đúng hành trình, tránh cảm giác bị ngợp và không đẩy bạn vào dashboard quá kỹ thuật.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Engine</p>
            <p className="mt-1 text-sm font-semibold text-slate-900">Education-first</p>
          </article>
          <article className="rounded-xl border border-slate-200 bg-white p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Output</p>
            <p className="mt-1 text-sm font-semibold text-slate-900">{answeredCount >= 4 ? 'Ready profile' : 'Building profile'}</p>
          </article>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5">
        <article className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Public beta onboarding</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">Một bản đồ đủ gọn để bắt đầu</h2>
          <p className="mt-2 text-sm text-slate-600">
            5 câu hỏi này chọn điểm rơi phù hợp giữa Learn Hub, Financial Health, Goals và Guided Investing.
          </p>
        </article>

        <div className="mt-4 grid gap-4">
          {QUESTIONS.map((question, index) => (
            <article key={question.key} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="rounded-full bg-teal-50 px-2 py-0.5 text-xs font-semibold text-teal-700">Bước {index + 1}</span>
                <h2 className="text-base font-semibold text-slate-900">{question.label}</h2>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {question.options.map(([value, label]) => {
                  const isSelected = answers[question.key] === value
                  return (
                    <button
                      key={value}
                      type="button"
                      className={isSelected
                        ? 'flex items-center gap-2 rounded-xl border border-teal-600 bg-teal-50 px-3 py-2 text-left text-sm font-medium text-teal-900'
                        : 'flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm font-medium text-slate-700 hover:border-slate-300 hover:bg-slate-100'}
                      onClick={() => setAnswers((current) => ({ ...current, [question.key]: value }))}
                    >
                      <span aria-hidden="true">{isSelected ? '●' : '○'}</span>
                      {label}
                    </button>
                  )
                })}
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Đã chọn:{' '}
                <strong className="text-slate-900">
                  {question.options.find(([value]) => value === answers[question.key])?.[1] || 'Chưa có lựa chọn'}
                </strong>
              </p>
            </article>
          ))}
        </div>

        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-teal-700">Bước cuối</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Khóa lại điểm khởi đầu của bạn</h2>
          <p className="mt-2 text-sm text-slate-600">
            Sau bước này, Home sẽ mở đúng hành trình thay vì đẩy bạn vào một dashboard kỹ thuật lạnh lẽo.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button type="button" onClick={handleComplete} disabled={loading || answeredCount < QUESTIONS.length} className={primaryButtonClass}>
              {loading ? 'Đang dựng lộ trình...' : 'Hoàn tất onboarding'}
            </button>
            {answeredCount < QUESTIONS.length ? (
              <p className="text-xs text-slate-500">Còn {QUESTIONS.length - answeredCount} câu cần chọn.</p>
            ) : null}
          </div>
          {error ? <p className="mt-2 text-sm text-rose-700">{error}</p> : null}
        </div>
      </section>
    </section>
  )
}
