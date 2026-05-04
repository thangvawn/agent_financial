import { useEffect, useMemo, useState } from 'react'

import { askFinancialHealthCoach, fetchFinancialHealthSnapshot, submitFinancialHealthAssessment } from '../../modules/financial-health'
import { ShieldIcon, ShieldPlusIcon, ActivityIcon, CheckCircleIcon, ArrowRightIcon, BarChartIcon, TrendingUpIcon, PiggyBankIcon, CalculatorIcon, ScaleIcon, ClockIcon, UsersIcon } from '../../shared/Icons'
import './financial-health.css'

const DEFAULT_FORM = {
  monthly_income_range: 'mid',
  income_stability_level: 'mostly_stable',
  expense_discipline_level: 'mostly_disciplined',
  emergency_fund_months_band: '1_to_3m',
  monthly_debt_payment_ratio_band: '10_to_30pct',
  savings_rate_band: '10_to_20pct',
  liquidity_stress_level: 'rare',
  has_basic_insurance: true,
  has_high_interest_debt: false,
  wants_to_start_investing: false,
}

const MONTH_LABELS = ['Tháng 12', 'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5']

export default function FinancialHealthPage({ sessionId, onCompleted, onOpenGuidedInvesting, onBack }) {
  const [snapshot, setSnapshot] = useState(null)
  const [coach, setCoach] = useState(null)
  const [loading, setLoading] = useState(Boolean(sessionId))
  const [assessing, setAssessing] = useState(false)
  const [coachLoading, setCoachLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadSnapshot() {
      if (!sessionId) {
        setLoading(false)
        return
      }
      setLoading(true)
      setError('')
      try {
        const payload = await fetchFinancialHealthSnapshot(sessionId)
        if (!cancelled) setSnapshot(payload)
      } catch (err) {
        if (!cancelled) setSnapshot(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadSnapshot()
    return () => {
      cancelled = true
    }
  }, [sessionId])

  const dashboard = useMemo(() => buildHealthDashboard(snapshot), [snapshot])

  async function handleSubmit() {
    if (!sessionId || assessing) return
    setAssessing(true)
    setError('')
    try {
      const payload = await submitFinancialHealthAssessment({
        session_id: sessionId,
        ...DEFAULT_FORM,
      })
      setSnapshot(payload)
      setCoach(null)
      onCompleted?.(payload)
    } catch (err) {
      setError(err.message || 'Không tạo được Financial Health snapshot.')
    } finally {
      setAssessing(false)
    }
  }

  async function handleCoach() {
    if (!sessionId || coachLoading) return
    setCoachLoading(true)
    setError('')
    try {
      const payload = await askFinancialHealthCoach(sessionId, 'investment_readiness')
      setCoach(payload)
    } catch (err) {
      setError(err.message || 'Không tải được coach.')
    } finally {
      setCoachLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <section className="fh-page">
        <div className="fh-empty">
          <h1>Financial Health cần session onboarding để cá nhân hóa.</h1>
          <p>Hoàn tất onboarding trước để hệ thống đánh giá đúng bối cảnh dòng tiền và mục tiêu của bạn.</p>
          {onBack ? (
            <button type="button" className="fh-btn fh-btn--primary" onClick={onBack}>
              Về Home
            </button>
          ) : null}
        </div>
      </section>
    )
  }

  if (loading) {
    return (
      <section className="fh-page">
        <div className="fh-empty">
          <p className="fh-kicker">Financial Health</p>
          <h1>Đang tải hồ sơ sức khỏe tài chính...</h1>
        </div>
      </section>
    )
  }

  return (
    <section className="fh-page">
      <header className="fh-hero">
        <div className="fh-hero__copy">
          <p className="fh-hero__eyebrow">Tổng quan cá nhân</p>
          <h1>Financial Health</h1>
          <p>
            Đánh giá sức khỏe tài chính cá nhân của bạn trên nhiều khía cạnh, từ dòng tiền, quỹ dự phòng cho tới
            độ sẵn sàng cho mục tiêu và đầu tư.
          </p>

          <div className="fh-hero__summary">
            <div className="fh-hero__score-box">
              <span className="fh-hero__score-label">Health Score</span>
              <div className="fh-hero__score-value">
                <strong>{dashboard.score}</strong>
                <span>/ 100</span>
              </div>
            </div>
            <div className="fh-hero__status-box">
              <span className="fh-hero__status-label">Trạng thái hiện tại</span>
              <strong className="fh-hero__status-value text-amber-400">{dashboard.band}</strong>
            </div>
          </div>

          <div className="fh-hero__actions">
            <button type="button" className="fh-btn fh-btn--primary" onClick={handleSubmit} disabled={assessing}>
              {snapshot ? (assessing ? 'Đang làm mới...' : 'Làm mới đánh giá') : assessing ? 'Đang đánh giá...' : 'Bắt đầu đánh giá'}
            </button>
            <button type="button" className="fh-btn fh-btn--ghost" onClick={() => onOpenGuidedInvesting?.('portfolio_review')}>
              Review cash flow
            </button>
            <button type="button" className="fh-btn fh-btn--ghost" onClick={handleCoach} disabled={coachLoading}>
              {coachLoading ? 'Đang hỏi Coach...' : 'Hỏi Coach'}
            </button>
          </div>
          {error ? <p className="fh-error">{error}</p> : null}
        </div>

        <div className="fh-radar">
          <div className="fh-radar__title-wrap">
            <ActivityIcon size={20} className="text-teal-400" />
            <p className="fh-radar__title">Sức khỏe tài chính của bạn</p>
          </div>
          <div className="fh-radar__frame">
            <div className="fh-radar__ring" />
            <div className="fh-radar__ring fh-radar__ring--inner" />
            <div className="fh-radar__ring fh-radar__ring--inner-2" />
            <div className="fh-radar__grid">
              {dashboard.subscores.map((item, index) => (
                <div key={item.key} className={`fh-radar__point fh-radar__point--${index + 1}`}>
                  <span>{item.label}</span>
                  <strong>{item.score}/100</strong>
                </div>
              ))}
            </div>
            <svg viewBox="0 0 200 200" className="fh-radar__chart" aria-hidden="true">
              <polygon className="fh-radar__outline" points={dashboard.radarOutline} />
              <polygon className="fh-radar__fill" points={dashboard.radarFill} />
            </svg>
          </div>
        </div>
      </header>

      <section className="fh-stats">
        {dashboard.stats.map((item, index) => {
          const icons = [<ActivityIcon size={24} />, <ShieldIcon size={24} />, <BarChartIcon size={24} />, <ScaleIcon size={24} />, <TrendingUpIcon size={24} />]
          return (
            <article key={item.label} className="fh-stat-card">
              <div className={`fh-stat-icon text-${item.tone}-600 bg-${item.tone}-50`}>
                {icons[index]}
              </div>
              <div className="fh-stat-content">
                <p>{item.label}</p>
                <strong>{item.value}</strong>
                <span>{item.subtext}</span>
              </div>
            </article>
          )
        })}
      </section>

      <section className="fh-grid fh-grid--top">
        <article className="fh-card">
          <div className="fh-card__head">
            <h2>Health Breakdown</h2>
          </div>
          <div className="fh-breakdown">
            {dashboard.subscores.map((item) => (
              <div key={item.key} className="fh-breakdown__row">
                <div className="fh-breakdown__meta">
                  <strong>{item.label}</strong>
                  <span>{item.reason}</span>
                </div>
                <div className="fh-breakdown__bar-container">
                  <div className="fh-breakdown__bar">
                    <span style={{ width: `${item.score}%` }} className={`is-${item.tone}`} />
                  </div>
                </div>
                <div className="fh-breakdown__score">
                  <b>{item.score}/100</b>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="fh-card">
          <div className="fh-card__head">
            <h2>Top Priorities</h2>
            <button type="button" className="fh-text-btn" onClick={handleCoach}>Xem tất cả</button>
          </div>
          <div className="fh-priorities">
            {dashboard.priorities.map((item, index) => (
              <div key={item.code} className="fh-priority">
                <div className={`fh-priority__index is-${item.tone}`}>{index + 1}</div>
                <div className="fh-priority__content">
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
                <em className={`fh-pill fh-pill--${item.tone}`}>{item.impact}</em>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="fh-grid fh-grid--middle">
        <article className="fh-card fh-card--wide">
          <div className="fh-card__head">
            <h2>Monthly Cash Flow Overview</h2>
            <span className="fh-chip">6 tháng gần nhất</span>
          </div>
          <div className="fh-bars">
            <div className="fh-bars__y-axis">
              <span>100%</span>
              <span>50%</span>
              <span>0%</span>
            </div>
            {dashboard.cashflow.map((item) => (
              <div key={item.label} className="fh-bars__item">
                <div className="fh-bars__stack">
                  <i style={{ height: `${item.savings}%` }} className="is-savings" title={`Tiết kiệm: ${item.savings}%`} />
                  <i style={{ height: `${item.expense}%` }} className="is-expense" title={`Chi tiêu: ${item.expense}%`} />
                  <i style={{ height: `${item.income - item.expense - item.savings}%` }} className="is-income" title={`Thu nhập còn lại`} />
                </div>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
          <div className="fh-bars__legend">
            <span><i className="is-savings"/> Tiết kiệm</span>
            <span><i className="is-expense"/> Chi tiêu cố định</span>
            <span><i className="is-income"/> Khác</span>
          </div>
        </article>

        <article className="fh-card fh-card--aside">
          <div className="fh-card__head">
            <h2>Savings Rate</h2>
          </div>
          <div className="fh-aside-kpi">
            <PiggyBankIcon size={48} className="text-teal-500 mb-2" />
            <strong>{dashboard.savingsRate}</strong>
            <span>{dashboard.savingsNote}</span>
          </div>
        </article>
      </section>

      <section className="fh-grid fh-grid--bottom">
        <article className="fh-card">
          <div className="fh-card__head">
            <h2>Risk Signals</h2>
          </div>
          <div className="fh-signal-list">
            {dashboard.signals.map((item) => (
              <div key={item.code} className="fh-signal">
                <div className={`fh-signal__icon text-${item.tone}-500 bg-${item.tone}-50`}>
                  <ShieldIcon size={20} />
                </div>
                <div className="fh-signal__content">
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
                <em className={`fh-pill fh-pill--${item.tone}`}>{item.label}</em>
              </div>
            ))}
          </div>
        </article>

        <article className="fh-card">
          <div className="fh-card__head">
            <h2>Recommended Actions</h2>
          </div>
          <div className="fh-action-grid">
            {dashboard.actions.map((item) => (
              <button key={item.code} type="button" className="fh-action-card" onClick={() => onOpenGuidedInvesting?.('portfolio_review')}>
                <div className="fh-action-card__icon"><CheckCircleIcon size={20} className="text-teal-600"/></div>
                <div className="fh-action-card__content">
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
                <ArrowRightIcon size={18} className="text-slate-400" />
              </button>
            ))}
          </div>
        </article>
      </section>

      <section className="fh-grid fh-grid--footer">
        <article className="fh-card">
          <div className="fh-card__head">
            <h2>Progress this month</h2>
          </div>
          <div className="fh-progress-grid">
            {dashboard.progress.map((item) => (
              <div key={item.label} className="fh-mini-metric">
                <p>{item.label}</p>
                <strong>{item.value}</strong>
                <span className="text-teal-600"><TrendingUpIcon size={14} className="inline mr-1" /> {item.delta}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="fh-card">
          <div className="fh-card__head">
            <h2>Learn for your health</h2>
          </div>
          <div className="fh-link-grid">
            {dashboard.learnLinks.map((item) => (
              <button key={item.title} type="button" className="fh-link-card" onClick={() => onOpenGuidedInvesting?.('market_context')}>
                <div className="fh-link-card__icon text-teal-600 bg-teal-50"><ClockIcon size={20} /></div>
                <div className="fh-link-card__content">
                  <strong>{item.title}</strong>
                  <p>{item.kind === 'lesson' ? 'Bài học đề xuất' : 'Module liên quan'}</p>
                </div>
              </button>
            ))}
          </div>
        </article>
      </section>
    </section>
  )
}

function buildHealthDashboard(snapshot) {
  const subscores = (snapshot?.subscores || DEFAULT_SUBSCORES).slice(0, 5).map((item) => ({
    key: item.key,
    label: item.label,
    score: item.score,
    reason: item.reason,
    hint: item.improvement_hint,
    tone: scoreTone(item.score),
  }))
  const actions = (snapshot?.actions || DEFAULT_ACTIONS).slice(0, 4)
  const flags = (snapshot?.flags || DEFAULT_FLAGS).slice(0, 4)
  const score = snapshot?.health_score ?? 72
  const savingsRate = findScore(subscores, 'Spending Control', 74)

  return {
    score,
    band: humanizeBand(snapshot?.score_band || 'stable_but_needs_improvement'),
    subscores,
    stats: [
      { label: 'Health Score', value: `${score} /100`, subtext: 'Cập nhật theo snapshot mới nhất', tone: scoreTone(score) },
      { label: 'Emergency Fund', value: `${Math.max(1, Math.round(findScore(subscores, 'Cash Buffer', 68) / 25))},4 tháng`, subtext: 'Ổn định', tone: 'green' },
      { label: 'Monthly Cash Flow', value: '+4.250.000 đ', subtext: 'Dương', tone: 'green' },
      { label: 'Debt Pressure', value: `${Math.max(12, 100 - findScore(subscores, 'Debt Load', 58))}%`, subtext: 'Cần cải thiện', tone: 'amber' },
      { label: 'Goal Readiness', value: `${findScore(subscores, 'Goal Readiness', 70)}%`, subtext: 'Trung bình', tone: scoreTone(findScore(subscores, 'Goal Readiness', 70)) },
    ],
    priorities: actions.map((item, index) => ({
      ...item,
      impact: index < 2 ? 'Tác động cao' : 'Tác động trung bình',
      tone: index < 2 ? 'red' : 'amber',
    })),
    cashflow: MONTH_LABELS.map((label, index) => ({
      label,
      income: 60 + ((score + index * 5) % 28),
      expense: 38 + ((score + index * 7) % 24),
      savings: 18 + ((savingsRate + index * 6) % 22),
    })),
    savingsRate: `${Math.round(savingsRate / 4)}%`,
    savingsNote: `Tăng ${Math.max(1, Math.round((savingsRate - 60) / 4))}% so với tháng trước`,
    signals: flags.map((item) => ({
      ...item,
      tone: severityTone(item.severity),
      label: severityLabel(item.severity),
    })),
    actions,
    progress: subscores.slice(0, 3).map((item) => ({
      label: item.label,
      value: `${item.score}${item.label === 'Cash Buffer' || item.label === 'Goal Readiness' ? ' /100' : '%'}`,
      delta: item.score >= 70 ? 'Đang đi đúng hướng' : 'Cần theo dõi thêm',
    })),
    learnLinks: snapshot?.educational_links?.length ? snapshot.educational_links : DEFAULT_LINKS,
    defaultCoach: snapshot?.transparency_note || 'Ưu tiên đầu tiên là tạo khoảng thở cho dòng tiền trước khi tăng độ phức tạp của kế hoạch đầu tư.',
    radarOutline: '100,28 155,70 137,138 63,138 45,70',
    radarFill: buildRadarFill(subscores),
  }
}

function buildRadarFill(items) {
  const points = [
    [100, 100 - items[0].score * 0.72],
    [100 + items[1].score * 0.58, 100 - items[1].score * 0.2],
    [100 + items[2].score * 0.42, 100 + items[2].score * 0.52],
    [100 - items[3].score * 0.42, 100 + items[3].score * 0.52],
    [100 - items[4].score * 0.58, 100 - items[4].score * 0.2],
  ]
  return points.map(([x, y]) => `${Math.round(x)},${Math.round(y)}`).join(' ')
}

function findScore(items, label, fallback) {
  return items.find((item) => item.label === label)?.score ?? fallback
}

function scoreTone(score) {
  if (score >= 72) return 'green'
  if (score >= 55) return 'amber'
  return 'red'
}

function severityTone(severity) {
  if (severity === 'high') return 'red'
  if (severity === 'medium') return 'amber'
  return 'green'
}

function severityLabel(severity) {
  if (severity === 'high') return 'Cao'
  if (severity === 'medium') return 'Trung bình'
  return 'Thấp'
}

function humanizeBand(value) {
  return String(value)
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

const DEFAULT_SUBSCORES = [
  { key: 'cash_buffer', label: 'Cash Buffer', score: 68, reason: 'Tích lũy quỹ dự phòng', improvement_hint: 'Gần đạt mức an toàn' },
  { key: 'debt_load', label: 'Debt Load', score: 58, reason: 'Kiểm soát tỷ lệ nợ', improvement_hint: 'Tỷ lệ nợ còn cao' },
  { key: 'spending_control', label: 'Spending Control', score: 74, reason: 'Kiểm soát chi tiêu', improvement_hint: 'Đang làm tốt' },
  { key: 'income_stability', label: 'Income Stability', score: 76, reason: 'Sự ổn định thu nhập', improvement_hint: 'Ổn định tốt' },
  { key: 'goal_readiness', label: 'Goal Readiness', score: 70, reason: 'Sẵn sàng đạt mục tiêu', improvement_hint: 'Cần rõ ràng hơn' },
]

const DEFAULT_FLAGS = [
  { code: 'low_buffer', severity: 'high', title: 'Quỹ dự phòng còn thấp', description: 'Ưu tiên nâng quỹ dự phòng lên 3-6 tháng chi phí sinh hoạt.' },
  { code: 'fixed_cost_up', severity: 'medium', title: 'Chi phí cố định có xu hướng tăng', description: 'Theo dõi nhóm chi tiêu định kỳ để tránh bào mòn dòng tiền.' },
  { code: 'debt_ratio', severity: 'medium', title: 'Tỷ lệ trả nợ cao', description: 'Giảm áp lực nợ xuống dưới 30% thu nhập.' },
  { code: 'spending_gap', severity: 'low', title: 'Chi tiêu phát sinh chưa kiểm soát', description: 'Thiết lập ngưỡng chi tiêu linh hoạt theo tuần.' },
]

const DEFAULT_ACTIONS = [
  { code: 'buffer_plan', title: 'Tạo kế hoạch quỹ dự phòng', description: 'Xác định mục tiêu và lịch tích lũy rõ ràng.' },
  { code: 'budget_review', title: 'Rà soát ngân sách hàng tháng', description: 'Phân loại và tối ưu chi tiêu hiệu quả.' },
  { code: 'debt_plan', title: 'Xây dựng kế hoạch trả nợ', description: 'Chọn chiến lược phù hợp để giảm nợ nhanh hơn.' },
  { code: 'health_recheck', title: 'Bắt đầu đánh giá sức khỏe tài chính', description: 'Thiết lập baseline và theo dõi tiến bộ.' },
]

const DEFAULT_LINKS = [
  { kind: 'lesson', id: 'emergency-fund-101', title: 'Quỹ khẩn cấp là gì?' },
  { kind: 'lesson', id: 'cashflow-101', title: 'Cách kiểm soát dòng tiền' },
  { kind: 'module', id: 'goals', title: 'Tỷ lệ an toàn là bao nhiêu?' },
]
