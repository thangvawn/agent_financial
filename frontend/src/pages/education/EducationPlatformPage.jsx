import './education-platform.css'

const SURFACE_CONFIG = {
  assignments: {
    eyebrow: 'Assignment System',
    title: 'Assignments',
    summary: 'Biến mô phỏng thành bài tập có mục tiêu học tập, dataset, câu hỏi, rubric và feedback.',
    primaryCta: 'Mở Assignment Builder',
    secondaryCta: 'Xem bài nộp',
  },
  financial_statement_simulator: {
    eyebrow: 'MVP Focus',
    title: 'Financial Statement Simulator',
    summary: 'Phân tích chất lượng lợi nhuận, dòng tiền, nợ, thanh khoản và red flags bằng ngôn ngữ sinh viên.',
    primaryCta: 'Chạy mô phỏng',
    secondaryCta: 'Xem rubric học tập',
  },
}

const RUBRIC = [
  ['Revenue and margin analysis', 20, 'Needs trend evidence'],
  ['Cash flow quality', 20, 'Compare CFO with net income'],
  ['Debt and liquidity risk', 20, 'Use D/E and current ratio'],
  ['Red flag reasoning', 20, 'Explain why the flag matters'],
  ['Conclusion with limitation', 20, 'Education and research only'],
]

const METRICS = [
  ['Revenue Growth', '+12.4%', 'Growth is positive, but check whether receivables grew faster than revenue.'],
  ['Gross Margin', '34.8%', 'Margin fell 220 bps, suggesting cost pressure or pricing weakness.'],
  ['CFO / Net Income', '0.62x', 'Profit is not fully converting into cash, so quality of earnings needs review.'],
  ['Debt / Equity', '1.4x', 'Leverage is rising; interest coverage should be checked before concluding.'],
]

export default function EducationPlatformPage({ surface = 'financial_statement_simulator', onBack }) {
  const config = SURFACE_CONFIG[surface] || SURFACE_CONFIG.financial_statement_simulator

  return (
    <section className={`edu-page edu-page--${surface}`} aria-label={config.title}>
      <header className="edu-hero">
        <div>
          <p className="edu-eyebrow">{config.eyebrow}</p>
          <h1>{config.title}</h1>
          <p>{config.summary}</p>
        </div>
        <div className="edu-hero-status" aria-label="Surface status">
          <span>Workspace state</span>
          <strong>{surface === 'financial_statement_simulator' ? 'Simulation running' : 'Ready'}</strong>
          <small>Education-only finance workflow</small>
        </div>
        <div className="edu-hero-actions">
          <button type="button" className="edu-button edu-button--primary">
            {config.primaryCta}
          </button>
          <button type="button" className="edu-button edu-button--secondary">
            {config.secondaryCta}
          </button>
          {onBack ? (
            <button type="button" className="edu-button edu-button--ghost" onClick={onBack}>
              Home
            </button>
          ) : null}
        </div>
      </header>

      <SafetyStrip />

      {surface === 'assignments' ? <AssignmentsSurface /> : null}
      {surface === 'financial_statement_simulator' ? <FinancialStatementSurface /> : null}
    </section>
  )
}

function SafetyStrip() {
  return (
    <section className="edu-safety" aria-label="Safety guardrails">
      <span>Education only</span>
      <span>Paper / research use</span>
      <span>No buy, sell or hold CTA</span>
      <span>Instructor final review</span>
    </section>
  )
}

function AssignmentsSurface() {
  return (
    <div className="edu-grid edu-grid--two">
      <Panel title="Assignment Builder" label="5-step flow">
        <div className="edu-steps">
          {['Learning goal', 'Dataset', 'Simulation template', 'Question set', 'Rubric'].map((step, index) => (
            <div className="edu-step" key={step}>
              <span>{index + 1}</span>
              <strong>{step}</strong>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Quality of Earnings rubric" label="Template">
        <div className="edu-rubric">
          {RUBRIC.map(([name, points, hint]) => (
            <div className="edu-rubric-row" key={name}>
              <strong>{name}</strong>
              <span>{points} pts</span>
              <p>{hint}</p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}

function FinancialStatementSurface() {
  return (
    <div className="edu-grid edu-grid--simulator">
      <Panel title="Simulation Controls" label="Scenario">
        <div className="edu-control-grid">
          <ControlRow label="Revenue growth" value="+12.4%" tone="good" />
          <ControlRow label="Receivables growth" value="+21.0%" tone="warn" />
          <ControlRow label="Debt pressure" value="Rising" tone="neutral" />
          <ControlRow label="Evidence required" value="3 notes" tone="good" />
        </div>
      </Panel>
      <Panel title="Company Snapshot" label="Sample dataset">
        <div className="edu-kpi-grid">
          {METRICS.map(([metric, value, explanation]) => (
            <article className="edu-kpi" key={metric}>
              <span>{metric}</span>
              <strong>{value}</strong>
              <p>{explanation}</p>
              <button type="button">Explain this</button>
            </article>
          ))}
        </div>
      </Panel>
      <Panel title="Red Flag Detection" label="Risk-first">
        <ActionList
          items={[
            'Profit increased while CFO lagged behind net income.',
            'Receivables growth is higher than revenue growth.',
            'Free cash flow remains negative after capex.',
            'Liquidity ratio weakened for two consecutive periods.',
          ]}
        />
      </Panel>
      <Panel title="Student Reflection" label="Required">
        <textarea defaultValue="Kết luận của em cần dựa trên CFO / Net Income, receivables growth và debt pressure..." aria-label="Student reflection" />
      </Panel>
    </div>
  )
}

function ControlRow({ label, value, tone }) {
  return (
    <div className={`edu-control-row edu-control-row--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Panel({ title, label, children }) {
  return (
    <section className="edu-panel">
      <div className="edu-panel-heading">
        <span>{label}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  )
}

function ActionList({ items }) {
  return (
    <ul className="edu-action-list">
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  )
}
