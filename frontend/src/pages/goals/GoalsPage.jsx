import { useEffect, useMemo, useState } from 'react'

import { checkInGoal, createGoal, explainGoal, fetchGoal, useGoals } from '../../modules/goals'
import { FlagIcon, TargetIcon, CompassIcon, ListIcon, BarChartIcon, MapPinIcon, CheckCircleIcon, ArrowRightIcon, PlusIcon } from '../../shared/Icons'
import './goals.css'

const DEFAULT_FORM = {
  goal_type: 'emergency_fund',
  goal_name: 'Quỹ khẩn cấp',
  deadline: '2027-04-30',
  target_amount: 100000000,
  current_amount: 24000000,
  priority: 'high',
  currency: 'VND',
  base_currency: 'VND',
  confidence_level: 'estimated',
}

export default function GoalsPage({ sessionId, initialGoalId = '', onBack, onOpenGuidedInvesting, onOpenCommunity, onCompleted }) {
  const [selectedGoal, setSelectedGoal] = useState(null)
  const [planner, setPlanner] = useState(null)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [creating, setCreating] = useState(false)
  const [planning, setPlanning] = useState(false)
  const [checkingIn, setCheckingIn] = useState('')
  const { data: goals, isLoading, error: listError } = useGoals(sessionId, refreshKey)

  useEffect(() => {
    let cancelled = false

    async function loadSelectedGoal(goalId) {
      if (!goalId) return
      try {
        const payload = await fetchGoal(goalId)
        if (!cancelled) setSelectedGoal(payload)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Không tải được goal.')
      }
    }

    if (initialGoalId) {
      void loadSelectedGoal(initialGoalId)
      return () => {
        cancelled = true
      }
    }

    if (!selectedGoal && goals.length) {
      void loadSelectedGoal(goals[0].goal_id)
    }

    return () => {
      cancelled = true
    }
  }, [goals, initialGoalId, selectedGoal])

  const dashboard = useMemo(() => buildGoalsDashboard(goals, selectedGoal, planner), [goals, planner, selectedGoal])

  async function handleCreate() {
    if (!sessionId || creating) return
    setCreating(true)
    setError('')
    try {
      const payload = await createGoal({
        session_id: sessionId,
        ...DEFAULT_FORM,
      })
      setSelectedGoal(payload)
      setPlanner(null)
      setRefreshKey((current) => current + 1)
      onCompleted?.(payload)
    } catch (err) {
      setError(err.message || 'Không tạo được goal.')
    } finally {
      setCreating(false)
    }
  }

  async function handlePlanner(goalId) {
    if (!goalId || planning) return
    setPlanning(true)
    setError('')
    try {
      const payload = await explainGoal(goalId)
      setPlanner(payload)
    } catch (err) {
      setError(err.message || 'Không tải được planner.')
    } finally {
      setPlanning(false)
    }
  }

  async function handleCheckIn(goal) {
    if (!goal || checkingIn) return
    setCheckingIn(goal.goal_id)
    setError('')
    try {
      const currentAmount = Math.min(goal.target_amount, goal.current_amount + Math.max(goal.monthly_contribution_needed, 1500000))
      const payload = await checkInGoal(goal.goal_id, {
        current_amount: currentAmount,
        note: 'Dashboard quick check-in',
      })
      setSelectedGoal(payload)
      setRefreshKey((current) => current + 1)
    } catch (err) {
      setError(err.message || 'Không check-in được goal.')
    } finally {
      setCheckingIn('')
    }
  }

  if (!sessionId) {
    return (
      <section className="goals-page">
        <div className="goals-empty">
          <h1>Goals cần session onboarding để gắn với hành trình tài chính của bạn.</h1>
          <p>Hoàn tất onboarding trước để hệ thống đề xuất lộ trình mục tiêu phù hợp.</p>
          {onBack ? (
            <button type="button" className="goals-btn goals-btn--primary" onClick={onBack}>
              Về Home
            </button>
          ) : null}
        </div>
      </section>
    )
  }

  if (isLoading) {
    return (
      <section className="goals-page">
        <div className="goals-empty">
          <p className="goals-kicker">Goals</p>
          <h1>Đang dựng bảng điều khiển mục tiêu...</h1>
        </div>
      </section>
    )
  }

  return (
    <section className="goals-page">
      <header className="goals-hero">
        <div className="goals-hero__copy">
          <p className="goals-hero__eyebrow">Hành trình mục tiêu</p>
          <h1>Financial Goals</h1>
          <p>
            Lập kế hoạch và theo dõi các mục tiêu tài chính của bạn với kỷ luật. Giúp bạn tiến gần hơn đến một cuộc
            sống tài chính vững vàng.
          </p>

          <div className="goals-hero__badges">
            <span>{dashboard.activeCount} mục tiêu đang hoạt động</span>
            <span className="goals-hero__divider">|</span>
            <span className="text-teal-400">{dashboard.mainStatus}</span>
          </div>

          <div className="goals-hero__actions">
            <button type="button" className="goals-btn goals-btn--primary" onClick={handleCreate} disabled={creating}>
              <PlusIcon size={16} /> {creating ? 'Đang tạo goal...' : 'Tạo goal mới'}
            </button>
            <button
              type="button"
              className="goals-btn goals-btn--ghost"
              onClick={() => handlePlanner(selectedGoal?.goal_id)}
              disabled={!selectedGoal || planning}
            >
              <CompassIcon size={16} /> {planning ? 'Đang tính planner...' : 'Review plan'}
            </button>
          </div>
          {error || listError ? <p className="goals-error">{error || listError}</p> : null}
        </div>

        <div className="goals-hero__illustration">
          <svg viewBox="0 0 400 200" className="goals-mountain" aria-hidden="true" preserveAspectRatio="none">
            <defs>
              <linearGradient id="mountain-grad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="rgba(20, 184, 166, 0.4)" />
                <stop offset="100%" stopColor="rgba(20, 184, 166, 0)" />
              </linearGradient>
            </defs>
            <path className="goals-mountain__bg" fill="url(#mountain-grad)" d="M0 200 L100 120 L180 150 L300 40 L400 90 L400 200 Z" />
            <path className="goals-mountain__line" fill="none" stroke="#14b8a6" strokeWidth="3" strokeLinejoin="round" d="M0 200 L100 120 L180 150 L300 40 L400 90" />
            
            <circle cx="100" cy="120" r="4" fill="#5eead4" />
            <circle cx="180" cy="150" r="4" fill="#5eead4" />
            <circle cx="300" cy="40" r="6" fill="#14b8a6" stroke="#fff" strokeWidth="2" />
            <circle cx="400" cy="90" r="4" fill="#5eead4" />
          </svg>

          <div className="goals-hero__overview-overlay">
            {dashboard.overview.slice(0, 3).map((item, idx) => (
              <div key={item.goal_id} className={`goals-hero-node goals-hero-node--${idx + 1}`}>
                <div className={`goals-hero-node__ring is-${item.tone}`}>
                  <svg viewBox="0 0 36 36">
                    <path className="bg" d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" />
                    <path className="val" strokeDasharray={`${item.progress}, 100`} d="M18 2 a 16 16 0 0 1 0 32 a 16 16 0 0 1 0 -32" />
                  </svg>
                  <span className="goals-hero-node__icon"><FlagIcon size={12}/></span>
                </div>
                <div className="goals-hero-node__label">
                  <strong>{item.goal_name}</strong>
                  <span>{item.progress}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </header>

      <section className="goals-stats">
        {dashboard.stats.map((item, index) => {
          const icons = [<TargetIcon size={24} />, <BarChartIcon size={24} />, <MapPinIcon size={24} />, <FlagIcon size={24} />]
          return (
            <article key={item.label} className="goals-stat-card">
              <div className={`goals-stat-icon text-${item.tone}-600 bg-${item.tone}-50`}>
                {icons[index]}
              </div>
              <div className="goals-stat-content">
                <p>{item.label}</p>
                <strong>{item.value}</strong>
                <span>{item.subtext}</span>
              </div>
            </article>
          )
        })}
      </section>

      <section className="goals-grid goals-grid--top">
        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Mục tiêu đang hoạt động</h2>
            <button type="button" className="goals-text-btn" onClick={handleCreate}>Xem tất cả</button>
          </div>
          <div className="goals-active-list">
            {dashboard.overview.map((goal) => (
              <button
                key={goal.goal_id}
                type="button"
                className={`goals-active-row ${selectedGoal?.goal_id === goal.goal_id ? 'is-active' : ''}`}
                onClick={() => fetchGoal(goal.goal_id).then(setSelectedGoal).catch((err) => setError(err.message))}
              >
                <div className="goals-active-row__main">
                  <strong>{goal.goal_name}</strong>
                  <span>Mục tiêu: {formatMoney(goal.target_amount)}</span>
                </div>
                <div className="goals-active-row__bar-wrap">
                  <div className="goals-active-row__bar">
                    <i style={{ width: `${goal.progress}%` }} className={`bg-${goal.tone}-500`} />
                  </div>
                </div>
                <b className="goals-active-row__pct">{goal.progress}%</b>
                <div className="goals-active-row__meta">
                  <span>{formatMoney(goal.current_amount)}</span>
                  <small>{goal.deadlineLabel}</small>
                </div>
                <em className={`goals-pill goals-pill--${goal.tone}`}>{goal.statusLabel}</em>
              </button>
            ))}
          </div>
        </article>

        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Tình trạng mục tiêu</h2>
            <button type="button" className="goals-text-btn" onClick={() => selectedGoal && handlePlanner(selectedGoal.goal_id)}>
              Xem tất cả
            </button>
          </div>
          <div className="goals-status-list">
            {dashboard.statusBuckets.map((item) => (
              <div key={item.label} className="goals-status-item">
                <div className={`goals-status-item__icon text-${item.tone}-600 bg-${item.tone}-50`}>
                  <CheckCircleIcon size={20} />
                </div>
                <div className="goals-status-item__content">
                  <strong className={`text-${item.tone}-700`}>{item.label}</strong>
                  <p>{item.message}</p>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="goals-grid goals-grid--middle">
        <article className="goals-card goals-card--wide">
          <div className="goals-card__head">
            <h2>Kế hoạch đóng góp</h2>
            <p>{selectedGoal ? `Đường đi đóng góp giúp bạn đạt mục tiêu ${selectedGoal.goal_name.toLowerCase()} đúng hạn.` : 'Tạo goal đầu tiên để bắt đầu theo dõi tiến độ.'}</p>
          </div>
          <div className="goals-projection">
            <div className="goals-projection__chart">
              {dashboard.projection.map((item) => (
                <div key={item.label} className="goals-projection__point">
                  <div className="goals-projection__bar">
                    <i style={{ height: `${item.value}%` }} className="bg-teal-500" />
                  </div>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
            <div className="goals-projection__kpis">
              {dashboard.planKpis.map((item) => (
                <div key={item.label} className="goals-kpi">
                  <p>{item.label}</p>
                  <strong>{item.value}</strong>
                  <span>{item.subtext}</span>
                </div>
              ))}
            </div>
          </div>
        </article>
      </section>

      <section className="goals-grid goals-grid--bottom">
        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Cột mốc & bước tiếp theo</h2>
            <button type="button" className="goals-text-btn" onClick={() => selectedGoal && handleCheckIn(selectedGoal)}>
              Xem tất cả
            </button>
          </div>
          <div className="goals-milestones">
            {dashboard.milestones.map((item, idx) => (
              <div key={item.label} className="goals-milestone">
                <div className="goals-milestone__node">{idx + 1}</div>
                <div className="goals-milestone__content">
                  <strong>{item.label}</strong>
                  <span>{item.value}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Kịch bản (What-if)</h2>
          </div>
          <div className="goals-scenario-grid">
            {dashboard.scenarios.map((item) => (
              <button key={item.title} type="button" className="goals-scenario-card" onClick={() => onOpenGuidedInvesting?.('market_context')}>
                <div className="goals-scenario-card__icon"><CompassIcon size={20} className="text-teal-600" /></div>
                <div className="goals-scenario-card__content">
                  <strong>{item.title}</strong>
                  <p>{item.summary}</p>
                </div>
                <ArrowRightIcon size={16} className="text-slate-400" />
              </button>
            ))}
          </div>
        </article>
      </section>

      <section className="goals-grid goals-grid--footer">
        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Insight mục tiêu</h2>
          </div>
          <div className="goals-insight">
            <div className="goals-insight__icon bg-teal-50 text-teal-600"><TargetIcon size={24}/></div>
            <div className="goals-insight__content">
              <strong>{planner?.summary || dashboard.insightTitle}</strong>
              <p>{planner?.feasibility_explanation || dashboard.insightBody}</p>
            </div>
            <button type="button" className="goals-text-btn self-start" onClick={() => selectedGoal && handlePlanner(selectedGoal.goal_id)}>
              Xem chi tiết
            </button>
          </div>
        </article>

        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Bài học đề xuất</h2>
          </div>
          <div className="goals-learning-links">
            {dashboard.learningLinks.map((item) => (
              <button key={item.title} type="button" className="goals-link-card" onClick={() => onOpenCommunity?.('risk-literacy-circle')}>
                <strong>{item.title}</strong>
                <span>{item.duration}</span>
              </button>
            ))}
          </div>
        </article>

        <article className="goals-card">
          <div className="goals-card__head">
            <h2>Hỏi Goal Coach</h2>
          </div>
          <div className="goals-prompt-row">
            {dashboard.prompts.map((item) => (
              <button key={item} type="button" className="goals-prompt" onClick={() => selectedGoal && handlePlanner(selectedGoal.goal_id)}>
                {item}
              </button>
            ))}
          </div>
          {selectedGoal ? (
            <button
              type="button"
              className="goals-btn goals-btn--primary w-full mt-4"
              onClick={() => handleCheckIn(selectedGoal)}
              disabled={checkingIn === selectedGoal.goal_id}
            >
              {checkingIn === selectedGoal.goal_id ? 'Đang check-in...' : 'Check-in nhanh'}
            </button>
          ) : null}
        </article>
      </section>
    </section>
  )
}

function buildGoalsDashboard(goals, selectedGoal, planner) {
  const overview = (goals || []).map((goal) => {
    const progress = goal.target_amount > 0 ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100)) : 0
    const tone = statusTone(goal.reminder_status, progress)
    return {
      ...goal,
      progress,
      tone,
      statusLabel: toneLabel(tone),
      deadlineLabel: formatDate(goal.next_reminder_at || selectedGoal?.deadline || DEFAULT_FORM.deadline),
    }
  })
  const fallbackGoal = selectedGoal || buildFallbackGoal()
  const activeCount = overview.length || 1
  const totalTarget = overview.reduce((sum, goal) => sum + goal.target_amount, 0) || fallbackGoal.target_amount
  const totalCurrent = overview.reduce((sum, goal) => sum + goal.current_amount, 0) || fallbackGoal.current_amount
  const totalContribution = overview.reduce((sum, goal) => sum + goal.monthly_contribution_needed, 0) || fallbackGoal.monthly_contribution_needed
  const totalProgress = totalTarget > 0 ? Math.round((totalCurrent / totalTarget) * 100) : 0
  const selected = selectedGoal || fallbackGoal
  const months = ['Tháng 5', 'Tháng 11', 'Tháng 2 ’26', 'Tháng 8', 'Tháng 2 ’27', 'Tháng 8', 'Tháng 2 ’28', 'Tháng 6']

  return {
    activeCount,
    mainStatus: overview.some((goal) => goal.tone === 'red') ? 'Có mục tiêu cần theo dõi sát hơn' : 'Đang đi đúng hướng cho mục tiêu chính',
    overview: overview.length ? overview : [fallbackGoal],
    stats: [
      { label: 'Mục tiêu đang hoạt động', value: `${activeCount} /4 mục tiêu`, subtext: summaryBreakdown(overview), tone: 'green' },
      { label: 'Đóng góp hàng tháng', value: formatCompactMoney(totalContribution), subtext: 'Tổng cam kết hàng tháng', tone: 'green' },
      { label: 'Tiến độ tổng thể', value: `${totalProgress}%`, subtext: `${formatCompactMoney(totalCurrent)} / ${formatCompactMoney(totalTarget)} đã tích lũy`, tone: totalProgress >= 55 ? 'green' : 'amber' },
      { label: 'Cột mốc sắp tới', value: '5 ngày', subtext: `Đóng góp cho ${selected.goal_name}`, tone: 'amber' },
    ],
    statusBuckets: [
      { label: `On Track (${overview.filter((item) => item.tone === 'green').length})`, message: 'Bạn đang đi đúng kế hoạch. Tiếp tục duy trì thói quen tốt.', tone: 'green' },
      { label: `Watch (${overview.filter((item) => item.tone === 'amber').length})`, message: 'Cần điều chỉnh nhẹ để đạt mục tiêu đúng hạn.', tone: 'amber' },
      { label: `At Risk (${overview.filter((item) => item.tone === 'red').length})`, message: 'Cần hành động ngay để tránh trễ hạn mục tiêu.', tone: 'red' },
    ],
    projection: months.map((label, index) => ({
      label,
      value: Math.min(96, 16 + index * 9 + Math.round(totalProgress / 3)),
    })),
    planKpis: [
      { label: 'Mục tiêu cao nhất', value: formatMoney(maxBy(overview, 'target_amount')?.target_amount || selected.target_amount), subtext: `Kết thúc ${formatDate(selected.deadline)}` },
      { label: 'Đóng góp hàng tháng', value: formatMoney(totalContribution), subtext: `Hiện tại: ${formatMoney(totalContribution)}/tháng` },
      { label: 'Thời gian hoàn thành', value: `${Math.max(1, selected.months_remaining || 31)} tháng`, subtext: `Mục tiêu: ${formatDate(selected.deadline)}` },
      { label: 'Dự kiến hoàn thành', value: formatDate(selected.deadline), subtext: selected.feasibility_band || 'Đúng hạn' },
    ],
    milestones: planner?.next_steps?.length
      ? planner.next_steps.map((item, index) => ({ label: item, value: index === 0 ? 'Ưu tiên' : 'Theo dõi' }))
      : [
          { label: 'Xây dựng Quỹ khẩn cấp 3 tháng chi phí sinh hoạt', value: 'Hoàn thành' },
          { label: 'Đạt 50% mục tiêu chính', value: `${formatCompactMoney(totalCurrent)} / ${formatCompactMoney(totalTarget)}` },
          { label: 'Đóng góp liên tục 12 tháng', value: `${Math.min(12, Math.max(1, Math.round(totalProgress / 8)))} / 12 tháng` },
        ],
    scenarios: [
      { title: 'Tăng đóng góp', summary: `+${formatCompactMoney(Math.round(totalContribution * 0.2))}/tháng để rút ngắn 8 tháng` },
      { title: 'Kéo dài thời gian', summary: `+12 tháng để giảm áp lực mỗi tháng cho ${selected.goal_name.toLowerCase()}` },
      { title: 'Giảm chi tiêu linh hoạt', summary: 'Tối ưu ngân sách để tăng tốc 5 tháng' },
      { title: 'Đóng góp bất ngờ', summary: `Bơm thêm ${formatCompactMoney(Math.round(selected.gap_amount * 0.08))} giúp tăng tốc lớn` },
    ],
    insightTitle: `Mục tiêu "${selected.goal_name}" đang bám tương đối tốt với kế hoạch hiện tại.`,
    insightBody: `Nếu tăng đóng góp thêm ${formatCompactMoney(Math.max(1000000, Math.round(selected.monthly_contribution_needed * 0.18)))} mỗi tháng hoặc giữ nhịp đều hơn, bạn sẽ có thêm vùng đệm trước hạn.`,
    learningLinks: [
      { title: 'Lập quỹ khẩn cấp', duration: '12 phút' },
      { title: 'Lập kế hoạch mua nhà', duration: '18 phút' },
      { title: 'Phân bổ mục tiêu tài chính', duration: '10 phút' },
    ],
    prompts: ['Tôi nên ưu tiên goal nào trước?', 'Mỗi tháng nên để dành bao nhiêu?', 'Nếu thu nhập giảm thì sao?'],
  }
}

function buildFallbackGoal() {
  return {
    goal_id: 'goal-demo',
    goal_name: DEFAULT_FORM.goal_name,
    target_amount: DEFAULT_FORM.target_amount,
    current_amount: DEFAULT_FORM.current_amount,
    monthly_contribution_needed: 5500000,
    reminder_status: 'on_track',
    months_remaining: 31,
    deadline: DEFAULT_FORM.deadline,
    progress: 24,
    tone: 'green',
    statusLabel: 'On track',
    deadlineLabel: formatDate(DEFAULT_FORM.deadline),
    gap_amount: DEFAULT_FORM.target_amount - DEFAULT_FORM.current_amount,
    feasibility_band: 'Đúng hạn',
  }
}

function statusTone(status, progress) {
  if (status === 'at_risk' || progress < 30) return 'red'
  if (status === 'watch' || progress < 55) return 'amber'
  return 'green'
}

function toneLabel(tone) {
  if (tone === 'red') return 'At risk'
  if (tone === 'amber') return 'Watch'
  return 'On track'
}

function summaryBreakdown(items) {
  const green = items.filter((item) => item.tone === 'green').length
  const amber = items.filter((item) => item.tone === 'amber').length
  const red = items.filter((item) => item.tone === 'red').length
  return `${green} on track • ${amber} watch • ${red} at risk`
}

function maxBy(items, key) {
  return [...items].sort((left, right) => (right[key] || 0) - (left[key] || 0))[0]
}

function formatMoney(value) {
  return `${Number(value || 0).toLocaleString('vi-VN')} đ`
}

function formatCompactMoney(value) {
  return `${(Number(value || 0) / 1000000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} triệu`
}

function formatDate(value) {
  if (!value) return 'Đang cập nhật'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('vi-VN')
}
