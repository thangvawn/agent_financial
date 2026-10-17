import { useState } from 'react'
import QuantaDocsSidebar from './QuantaDocsSidebar'
import QuantaDocsHome from './QuantaDocsHome'
import QuantaLessonReader from './QuantaLessonReader'
import QuantaWikiReader from './QuantaWikiReader'
import QuantaStudioModal from './QuantaStudioModal'
import './quanta-docs.css'

export default function QuantaDocsPage({ onBack }) {
  const [activeMode, setActiveMode] = useState('curriculum') // 'curriculum' | 'wiki'
  const [view, setView] = useState('home') // 'home' | 'lesson' | 'wiki_detail'
  const [selectedLessonSlug, setSelectedLessonSlug] = useState('quanta-overview')
  const [selectedFnName, setSelectedFnName] = useState('sma')
  const [isStudioOpen, setIsStudioOpen] = useState(false)

  function handleSelectLesson(slug) {
    setSelectedLessonSlug(slug)
    setActiveMode('curriculum')
    setView('lesson')
  }

  function handleSelectWiki(fnName) {
    setSelectedFnName(fnName)
    setActiveMode('wiki')
    setView('wiki_detail')
  }

  function handleGoHome() {
    setView('home')
  }

  function handleSwitchToWiki() {
    setActiveMode('wiki')
    setView('home')
  }

  return (
    <div className="qd-page-shell" data-domain="quanta_docs">
      {/* Top Banner Bar */}
      <div className="qd-top-nav-bar">
        <div className="qd-top-brand">
          <span className="qd-brand-badge">Quanta Docs</span>
          <span className="qd-brand-sub">Tài liệu Quanta hoàn chỉnh cho Quant Studio</span>
        </div>
        <div className="qd-top-actions-right">
          <button
            type="button"
            className="qd-btn qd-btn--outline"
            onClick={() => setIsStudioOpen(true)}
          >
            Mở Studio
          </button>
          {onBack && (
            <button
              type="button"
              className="qd-btn qd-btn--back"
              onClick={onBack}
            >
              Về thư viện
            </button>
          )}
        </div>
      </div>

      {/* Main Workspace: Sidebar + Content */}
      <div className="qd-workspace">
        <QuantaDocsSidebar
          activeMode={activeMode}
          onModeChange={setActiveMode}
          activeItem={{ slug: selectedLessonSlug, fnName: selectedFnName }}
          onSelectLesson={handleSelectLesson}
          onSelectWiki={handleSelectWiki}
          onGoHome={handleGoHome}
          isHome={view === 'home'}
        />

        <main className="qd-main-content">
          {view === 'home' && (
            <QuantaDocsHome
              onSelectLesson={handleSelectLesson}
              onSwitchToWiki={handleSwitchToWiki}
              onOpenStudioModal={() => setIsStudioOpen(true)}
            />
          )}

          {view === 'lesson' && (
            <QuantaLessonReader
              lessonSlug={selectedLessonSlug}
              onSelectLesson={handleSelectLesson}
              onGoHome={handleGoHome}
            />
          )}

          {view === 'wiki_detail' && (
            <QuantaWikiReader
              fnName={selectedFnName}
              onSelectFn={handleSelectWiki}
              onGoHome={handleGoHome}
            />
          )}
        </main>
      </div>

      {/* Studio Sandbox Modal */}
      <QuantaStudioModal
        isOpen={isStudioOpen}
        onClose={() => setIsStudioOpen(false)}
      />
    </div>
  )
}
