import { BookOpen, ShieldAlert, Target } from 'lucide-react'

const ITEMS = [
  { key: 'objective', label: 'Bạn sẽ hiểu', icon: <BookOpen aria-hidden="true" size={20} strokeWidth={1.8} /> },
  { key: 'practice', label: 'Bạn sẽ thực hành', icon: <Target aria-hidden="true" size={20} strokeWidth={1.8} /> },
  { key: 'riskNote', label: 'Lưu ý tài chính', icon: <ShieldAlert aria-hidden="true" size={20} strokeWidth={1.8} />, caution: true },
]

export default function FinancialLearningContext({ objective, practice, riskNote }) {
  const content = { objective, practice, riskNote }

  return (
    <aside className="edu-context" aria-label="Định hướng học tập">
      {ITEMS.map(({ key, label, icon, caution }) => (
        <div
          key={key}
          className={`edu-context__item${caution ? ' edu-context__item--caution' : ''}`}
          role={caution ? 'note' : undefined}
        >
          {icon}
          <div>
            <strong>{label}</strong>
            {content[key] ? <p>{content[key]}</p> : null}
          </div>
        </div>
      ))}
    </aside>
  )
}
