import { useState } from 'react'
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Home,
  Library,
  Sparkles,
} from 'lucide-react'
import { QUANTA_SECTIONS } from '../content/quantaCurriculumData'
import { WIKI_FUNCTION_GROUPS, WIKI_NAMESPACES } from '../content/quantaWikiData'

export default function QuantaDocsSidebar({
  activeMode,
  onModeChange,
  activeItem,
  onSelectLesson,
  onSelectWiki,
  onGoHome,
  isHome,
}) {
  const [openSections, setOpenSections] = useState({
    'v2-foundation': true,
    'v2-indicators': true,
    'v2-render': false,
    'v2-act-risk': false,
    'v2-advanced-ai': false,
    'v2-recipes': false,
  })

  function toggleSection(secId) {
    setOpenSections((prev) => ({ ...prev, [secId]: !prev[secId] }))
  }

  return (
    <aside className="qd-sidebar" aria-label="Quanta Docs Navigation">
      {/* Mode Switcher: Giáo trình vs Wiki */}
      <div className="qd-mode-switcher" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeMode === 'curriculum'}
          className={`qd-mode-btn ${activeMode === 'curriculum' ? 'is-active' : ''}`}
          onClick={() => onModeChange('curriculum')}
        >
          <BookOpen size={14} />
          <span>Giáo trình</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeMode === 'wiki'}
          className={`qd-mode-btn ${activeMode === 'wiki' ? 'is-active' : ''}`}
          onClick={() => onModeChange('wiki')}
        >
          <Library size={14} />
          <span>Wiki</span>
        </button>
      </div>

      {/* Home link */}
      <div className="qd-nav-home">
        <button
          type="button"
          className={`qd-home-btn ${isHome ? 'is-active' : ''}`}
          onClick={onGoHome}
        >
          <Home size={15} />
          <span>Home</span>
        </button>
      </div>

      {/* Navigation List */}
      <div className="qd-nav-scroll thin-scrollbar">
        {activeMode === 'curriculum' ? (
          <nav className="qd-curriculum-nav">
            {QUANTA_SECTIONS.map((sec) => {
              const isOpen = Boolean(openSections[sec.id])
              return (
                <div key={sec.id} className="qd-section-group">
                  <button
                    type="button"
                    className="qd-section-header"
                    onClick={() => toggleSection(sec.id)}
                  >
                    <Sparkles size={14} className="qd-sec-icon" />
                    <span className="qd-sec-title">{sec.title}</span>
                    {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>

                  {isOpen && (
                    <ul className="qd-lesson-list">
                      {sec.lessons.map((lesson) => {
                        const isCurrent = activeItem?.slug === lesson.slug && !isHome
                        return (
                          <li key={lesson.slug}>
                            <button
                              type="button"
                              className={`qd-lesson-item ${isCurrent ? 'is-active' : ''}`}
                              onClick={() => onSelectLesson(lesson.slug)}
                            >
                              <span className="qd-lesson-title">{lesson.title}</span>
                              <span className="qd-lesson-time">{lesson.estimated_min}m</span>
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </div>
              )
            })}
          </nav>
        ) : (
          <nav className="qd-wiki-nav">
            <div className="qd-wiki-header-label">Hàm Built-in (59)</div>
            {WIKI_FUNCTION_GROUPS.map((grp) => (
              <div key={grp.id} className="qd-wiki-group">
                <div className="qd-wiki-group-title">
                  <span>{grp.title}</span>
                  <span className="qd-badge-pill">{grp.count}</span>
                </div>
                <div className="qd-wiki-pill-grid">
                  {grp.items.map((fnName) => {
                    const isCurrent = activeItem?.fnName === fnName && !isHome
                    return (
                      <button
                        key={fnName}
                        type="button"
                        className={`qd-fn-tag ${isCurrent ? 'is-active' : ''}`}
                        onClick={() => onSelectWiki(fnName)}
                      >
                        {fnName}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}

            <div className="qd-wiki-header-label" style={{ marginTop: '1rem' }}>Smart Namespaces</div>
            <div className="qd-wiki-pill-grid">
              {WIKI_NAMESPACES.map((ns) => (
                <button
                  key={ns.name}
                  type="button"
                  className="qd-fn-tag qd-fn-tag--ns"
                  onClick={() => onSelectWiki(ns.name)}
                >
                  {ns.name}
                </button>
              ))}
            </div>
          </nav>
        )}
      </div>
    </aside>
  )
}
