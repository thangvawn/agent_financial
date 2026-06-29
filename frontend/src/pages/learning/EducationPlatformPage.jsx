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
  const steps = [
    { name: 'Learning goal', status: 'completed', desc: 'Define key learning outcomes' },
    { name: 'Dataset', status: 'completed', desc: 'Select financial statements' },
    { name: 'Simulation template', status: 'current', desc: 'Configure anomalies and red flags' },
    { name: 'Question set', status: 'upcoming', desc: 'Draft analytical questions' },
    { name: 'Rubric', status: 'upcoming', desc: 'Set grading criteria' },
  ];

  return (
    <div className="edu-grid edu-grid--assignments">
      <Panel title="Assignment Builder" label="Configuration">
        <div className="edu-builder-stepper">
          {steps.map((step, index) => (
            <div className={`edu-stepper-item edu-stepper-item--${step.status}`} key={step.name}>
              <div className="edu-stepper-indicator">
                {step.status === 'completed' ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>
              <div className="edu-stepper-content">
                <strong>{step.name}</strong>
                <p>{step.desc}</p>
                {step.status === 'current' && (
                  <button type="button" className="edu-button edu-button--primary edu-button--small" style={{marginTop: '10px'}}>Configure</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Panel>
      
      <Panel title="Quality of Earnings rubric" label="Evaluation criteria">
        <div className="edu-table-container">
          <table className="edu-data-table">
            <thead>
              <tr>
                <th>Criteria</th>
                <th className="edu-text-right">Points</th>
                <th>Guidance Hint</th>
                <th className="edu-text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {RUBRIC.map(([name, points, hint]) => (
                <tr key={name}>
                  <td><strong>{name}</strong></td>
                  <td className="edu-text-right"><span className="edu-badge">{points} pts</span></td>
                  <td><span className="edu-text-muted">{hint}</span></td>
                  <td className="edu-text-right">
                    <button type="button" className="edu-icon-button" aria-label="Edit rubric">
                       <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="edu-panel-footer">
          <button type="button" className="edu-button edu-button--ghost edu-button--icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '6px'}}><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Add criterion
          </button>
          <div className="edu-total-points">Total: 100 pts</div>
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
