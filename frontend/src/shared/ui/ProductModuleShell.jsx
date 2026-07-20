/**
 * Shared chrome for product modules (not Home).
 * tone: "lab" (learning workspace) | "pro" (practice workspace)
 */
import FinancialLearningContext from './FinancialLearningContext'

function handleTabKeyDown(event, index, tabs, onTabChange) {
  const offsets = { ArrowLeft: -1, ArrowRight: 1 }
  let nextIndex = index
  if (event.key in offsets) nextIndex = (index + offsets[event.key] + tabs.length) % tabs.length
  else if (event.key === 'Home') nextIndex = 0
  else if (event.key === 'End') nextIndex = tabs.length - 1
  else return

  event.preventDefault()
  onTabChange?.(tabs[nextIndex].id)
  const nextTab = event.currentTarget.parentElement?.children[nextIndex]
  if (nextTab instanceof HTMLElement) nextTab.focus()
}

export default function ProductModuleShell({
  domain,
  eyebrow,
  title,
  subtitle,
  tone = 'lab',
  tabs = [],
  activeTab,
  onTabChange,
  actions = null,
  learning,
  children,
}) {
  const titleId = `${domain}-page-title`

  return (
    <section
      className={`pm-shell pm-shell--${tone}`}
      data-domain={domain}
      aria-labelledby={titleId}
    >
      <header className="pm-shell__header">
        <div className="pm-shell__intro">
          {eyebrow ? <p className="pm-shell__eyebrow">{eyebrow}</p> : null}
          <h1 id={titleId} className="pm-shell__title">{title}</h1>
          {subtitle ? <p className="pm-shell__subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="pm-shell__actions">{actions}</div> : null}
      </header>
      {learning ? <FinancialLearningContext {...learning} /> : null}
      {tabs.length > 0 ? (
        <div className="pm-shell__tabs" aria-label={`Nội dung ${title}`} role="tablist">
          {tabs.map((tab, index) => (
            <button
              key={tab.id}
              id={`${domain}-tab-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`${domain}-tab-panel`}
              tabIndex={activeTab === tab.id ? 0 : -1}
              className={activeTab === tab.id ? 'is-active' : undefined}
              onClick={() => onTabChange?.(tab.id)}
              onKeyDown={(event) => handleTabKeyDown(event, index, tabs, onTabChange)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      ) : null}
      <div
        id={`${domain}-tab-panel`}
        className="pm-shell__body"
        role={tabs.length > 0 ? 'tabpanel' : undefined}
        aria-labelledby={tabs.length > 0 ? `${domain}-tab-${activeTab}` : undefined}
        tabIndex={tabs.length > 0 ? 0 : undefined}
      >
        {children}
      </div>
    </section>
  )
}
