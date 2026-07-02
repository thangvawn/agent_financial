import { motion } from 'framer-motion'

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
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col gap-6 p-6 md:p-8 min-h-[100dvh] bg-slate-50 dark:bg-zinc-950 text-slate-900 dark:text-zinc-100 font-sans"
      aria-label={config.title}
    >
      <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 p-6 rounded-3xl bg-gradient-to-br from-zinc-900 to-emerald-950 text-white shadow-lg border border-zinc-800">
        <div className="flex-1">
          <p className="text-xs font-bold text-teal-400 uppercase tracking-widest mb-1">{config.eyebrow}</p>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">{config.title}</h1>
          <p className="text-xs md:text-sm text-zinc-300 mt-2 leading-relaxed max-w-xl">{config.summary}</p>
        </div>
        <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1 min-w-[240px]">
          <span className="text-[10px] text-zinc-400 font-semibold uppercase tracking-wider">Workspace state</span>
          <strong className="text-sm text-teal-400">{surface === 'financial_statement_simulator' ? 'Simulation running' : 'Ready'}</strong>
          <small className="text-[10px] text-zinc-400">Education-only finance workflow</small>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="px-4 py-2.5 rounded-full text-xs font-semibold bg-teal-500 hover:bg-teal-600 text-white transition-colors cursor-pointer active:scale-95 shadow-lg shadow-teal-500/10">
            {config.primaryCta}
          </button>
          <button type="button" className="px-4 py-2.5 rounded-full text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/20 text-white transition-colors cursor-pointer active:scale-95">
            {config.secondaryCta}
          </button>
          {onBack && (
            <button type="button" className="px-4 py-2.5 rounded-full text-xs font-semibold bg-white/5 hover:bg-white/10 border border-white/20 text-white transition-colors cursor-pointer active:scale-95" onClick={onBack}>
              Home
            </button>
          )}
        </div>
      </header>

      <SafetyStrip />

      {surface === 'assignments' ? <AssignmentsSurface /> : null}
      {surface === 'financial_statement_simulator' ? <FinancialStatementSurface /> : null}
    </motion.section>
  )
}

function SafetyStrip() {
  return (
    <section className="flex flex-wrap gap-2.5 p-3.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm" aria-label="Safety guardrails">
      {['Education only', 'Paper / research use', 'No buy, sell or hold CTA', 'Instructor final review'].map((item) => (
        <span key={item} className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-amber-900/20 uppercase tracking-wider">
          {item}
        </span>
      ))}
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
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Panel title="Assignment Builder" label="Configuration">
        <div className="flex flex-col gap-5 mt-4">
          {steps.map((step, index) => (
            <div className="flex gap-4 items-start" key={step.name}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                step.status === 'completed' ? 'bg-teal-500 text-white' :
                step.status === 'current' ? 'bg-teal-50 dark:bg-teal-950/30 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-900/30' :
                'bg-slate-100 dark:bg-zinc-800 text-slate-400 dark:text-zinc-500'
              }`}>
                {step.status === 'completed' ? (
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <strong className="block text-sm font-semibold text-slate-900 dark:text-white">{step.name}</strong>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5 leading-relaxed">{step.desc}</p>
                {step.status === 'current' && (
                  <button type="button" className="px-3.5 py-1.5 mt-2 rounded-lg text-xs font-bold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer active:scale-95 transition-colors">
                    Configure
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Panel>
      
      <Panel title="Quality of Earnings rubric" label="Evaluation criteria">
        <div className="w-100 overflow-x-auto border border-slate-200 dark:border-zinc-800 rounded-xl bg-slate-50/50 dark:bg-zinc-950/20">
          <table className="w-full text-left border-collapse text-xs md:text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-zinc-800">
                <th className="p-3 font-semibold text-slate-655 dark:text-zinc-400">Criteria</th>
                <th className="p-3 font-semibold text-slate-655 dark:text-zinc-400 text-right">Points</th>
                <th className="p-3 font-semibold text-slate-655 dark:text-zinc-400">Guidance Hint</th>
                <th className="p-3 font-semibold text-slate-655 dark:text-zinc-400 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {RUBRIC.map(([name, points, hint]) => (
                <tr key={name} className="border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors">
                  <td className="p-3"><strong className="font-semibold text-slate-900 dark:text-white">{name}</strong></td>
                  <td className="p-3 text-right"><span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 border border-teal-100 dark:border-teal-900/20">{points} pts</span></td>
                  <td className="p-3"><span className="text-slate-500 dark:text-zinc-400 text-xs">{hint}</span></td>
                  <td className="p-3 text-right">
                    <button type="button" className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white cursor-pointer hover:bg-slate-100 dark:hover:bg-zinc-800" aria-label="Edit rubric">
                       <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                         <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                         <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                       </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex justify-between items-center mt-4">
          <button type="button" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 dark:border-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-850 cursor-pointer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add criterion
          </button>
          <div className="text-xs font-bold text-slate-900 dark:text-white">Total: 100 pts</div>
        </div>
      </Panel>
    </div>
  )
}

function FinancialStatementSurface() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Panel title="Simulation Controls" label="Scenario">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
          <ControlRow label="Revenue growth" value="+12.4%" tone="good" />
          <ControlRow label="Receivables growth" value="+21.0%" tone="warn" />
          <ControlRow label="Debt pressure" value="Rising" tone="neutral" />
          <ControlRow label="Evidence required" value="3 notes" tone="good" />
        </div>
      </Panel>
      <Panel title="Company Snapshot" label="Sample dataset">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
          {METRICS.map(([metric, value, explanation]) => (
            <article className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-200 dark:border-zinc-800 flex flex-col gap-1.5" key={metric}>
              <span className="text-xs text-slate-500 dark:text-zinc-400 font-semibold">{metric}</span>
              <strong className="text-lg font-extrabold text-slate-900 dark:text-white">{value}</strong>
              <p className="text-xs text-slate-500 dark:text-zinc-400 leading-relaxed">{explanation}</p>
              <button type="button" className="text-xs font-bold text-teal-600 dark:text-teal-400 hover:underline text-left mt-auto cursor-pointer">Explain this</button>
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
        <textarea
          className="w-full min-h-[120px] p-3 rounded-xl border border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950/20 text-slate-800 dark:text-zinc-200 text-xs md:text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
          defaultValue="Kết luận của em cần dựa trên CFO / Net Income, receivables growth và debt pressure..."
          aria-label="Student reflection"
        />
      </Panel>
    </div>
  )
}

function ControlRow({ label, value, tone }) {
  const toneClasses = {
    good: 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-250 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-400',
    warn: 'bg-amber-50 dark:bg-amber-950/20 border-amber-250 dark:border-amber-900/30 text-amber-800 dark:text-amber-400',
    neutral: 'bg-slate-50 dark:bg-zinc-850 border-slate-200 dark:border-zinc-800 text-slate-700 dark:text-zinc-300',
  }
  return (
    <div className={`p-4 rounded-xl border flex items-center justify-between gap-4 font-semibold text-xs md:text-sm ${toneClasses[tone] || toneClasses.neutral}`}>
      <span>{label}</span>
      <strong className="font-extrabold">{value}</strong>
    </div>
  )
}

function Panel({ title, label, children }) {
  return (
    <section className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      <div>
        <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-bold uppercase tracking-wider">{label}</span>
        <h2 className="text-base font-bold text-slate-900 dark:text-white mt-0.5">{title}</h2>
      </div>
      {children}
    </section>
  )
}

function ActionList({ items }) {
  return (
    <ul className="flex flex-col gap-2.5">
      {items.map((item) => (
        <li key={item} className="flex gap-2 items-start text-xs md:text-sm text-slate-650 dark:text-zinc-350">
          <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          {item}
        </li>
      ))}
    </ul>
  )
}
