import { useEffect, useMemo, useState } from 'react'
import { BookOpen, FileText, Layers, Search, Sparkles } from 'lucide-react'

import { DEMO_BOOKS, normalizeDbBook } from '../content/courseCatalogData'
import { DOCUMENT_FOLDERS, DOCUMENT_TYPES, matchesFolder, normalizeDbPaper } from '../content/paperCatalogData'
import { fetchLearningCatalog } from '../services/learningApi'
import BookCardItem from './BookCardItem'
import BookTakeawaysModal from './BookTakeawaysModal'
import DocumentFolderNav from './DocumentFolderNav'
import PaperCard from './PaperCard'
import PaperDetailModal from './PaperDetailModal'
import './document-library.css'

export default function DocumentLibrary({ onOpenBook }) {
  const [books, setBooks] = useState([])
  const [papers, setPapers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [docType, setDocType] = useState('all')
  const [activeFolderId, setActiveFolderId] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedTakeawayBook, setSelectedTakeawayBook] = useState(null)
  const [selectedPaper, setSelectedPaper] = useState(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetchLearningCatalog('book', { limit: 120 }).catch(() => ({ items: [] })),
      fetchLearningCatalog('paper', { limit: 120 }).catch(() => ({ items: [] })),
    ]).then(([resBooks, resPapers]) => {
      if (cancelled) return
      const rawBooks = Array.isArray(resBooks?.items) && resBooks.items.length > 0
        ? resBooks.items.map(normalizeDbBook).filter(Boolean)
        : []
      const dbBookIds = new Set(rawBooks.map((b) => b.book_id))
      const combinedBooks = [...rawBooks, ...DEMO_BOOKS.filter((b) => !dbBookIds.has(b.book_id))]
      setBooks(combinedBooks.map((b) => ({ ...b, type: 'book' })))

      const rawPapers = Array.isArray(resPapers?.items) && resPapers.items.length > 0
        ? resPapers.items.map(normalizeDbPaper).filter(Boolean)
        : []
      setPapers(rawPapers)
      setIsLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const folderCounts = useMemo(() => {
    const pool = docType === 'book' ? books : docType === 'paper' ? papers : [...books, ...papers]
    const counts = { all: pool.length }
    for (const f of DOCUMENT_FOLDERS) {
      if (f.id !== 'all') {
        counts[f.id] = pool.filter((it) => matchesFolder(it, f.id)).length
      }
    }
    return counts
  }, [books, papers, docType])

  const filteredItems = useMemo(() => {
    let pool = docType === 'book' ? books : docType === 'paper' ? papers : [...books, ...papers]
    if (activeFolderId !== 'all') {
      pool = pool.filter((it) => matchesFolder(it, activeFolderId))
    }
    if (search.trim()) {
      const q = search.toLowerCase().trim()
      pool = pool.filter((it) =>
        `${it.title || ''} ${it.author || ''} ${it.summary || ''} ${it.abstract || ''}`.toLowerCase().includes(q)
      )
    }
    return pool
  }, [books, papers, docType, activeFolderId, search])

  const currentFolder = DOCUMENT_FOLDERS.find((f) => f.id === activeFolderId) || DOCUMENT_FOLDERS[0]

  return (
    <div className="lh-doc-library">
      {/* Header with high-level metrics */}
      <div className="lh-doc-library__header">
        <div>
          <h2 className="lh-section__title" style={{ margin: 0 }}>
            Thư viện Tri thức & Nghiên cứu Tài chính
            <span className="lh-section__count">{filteredItems.length}</span>
          </h2>
          <p className="lh-section__subtitle" style={{ marginTop: '0.25rem' }}>
            Phân loại rõ ràng giữa Sách kinh điển và Paper nghiên cứu định lượng theo từng folder chuyên đề
          </p>
        </div>
        <div className="lh-doc-library__stats">
          <span className="lh-doc-stat-pill">
            <BookOpen size={14} /> Sách: <strong>{books.length}</strong>
          </span>
          <span className="lh-doc-stat-pill">
            <FileText size={14} /> Paper: <strong>{papers.length}</strong>
          </span>
          <span className="lh-doc-stat-pill">
            <Sparkles size={14} /> Thư mục: <strong>{DOCUMENT_FOLDERS.length - 1}</strong>
          </span>
        </div>
      </div>

      {/* Controls Bar: Type switcher + Search box */}
      <div className="lh-doc-controls-bar">
        <div className="lh-doc-type-tabs" role="tablist" aria-label="Loại học liệu">
          {DOCUMENT_TYPES.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={docType === t.id}
              className={`lh-doc-type-tab ${docType === t.id ? 'is-active' : ''}`}
              onClick={() => setDocType(t.id)}
            >
              {t.id === 'all' && <Layers size={14} />}
              {t.id === 'book' && <BookOpen size={14} />}
              {t.id === 'paper' && <FileText size={14} />}
              <span>{t.label}</span>
            </button>
          ))}
        </div>

        <div className="lhc-search-box" style={{ maxWidth: '320px', marginLeft: 'auto' }}>
          <Search size={15} className="lhc-search-box__icon" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo tên sách, tác giả, abstract..."
            className="lhc-search-box__input"
          />
        </div>
      </div>

      {/* Main Workspace: Sidebar folder nav + Content grid */}
      <div className="lh-doc-workspace">
        <DocumentFolderNav
          folders={DOCUMENT_FOLDERS}
          activeFolderId={activeFolderId}
          onSelectFolder={setActiveFolderId}
          counts={folderCounts}
        />

        <div className="lh-doc-content-area">
          {isLoading && books.length === 0 && papers.length === 0 ? (
            <div className="lh-empty-state"><p>Đang đồng bộ dữ liệu thư viện...</p></div>
          ) : filteredItems.length === 0 ? (
            <div className="lh-empty-state">
              <p>Không tìm thấy tài liệu nào trong thư mục <strong>"{currentFolder.label}"</strong> phù hợp.</p>
              <button
                type="button"
                className="lhc-btn lhc-btn--outline"
                onClick={() => { setSearch(''); setActiveFolderId('all'); setDocType('all') }}
                style={{ marginTop: '0.75rem' }}
              >
                Đặt lại tất cả bộ lọc
              </button>
            </div>
          ) : (
            <div className={docType === 'paper' ? 'lh-papers-grid' : 'lh-books-grid'}>
              {filteredItems.map((item) => {
                if (item.type === 'paper') {
                  return (
                    <PaperCard
                      key={item.paper_id}
                      paper={item}
                      onViewDetail={setSelectedPaper}
                    />
                  )
                }
                return (
                  <BookCardItem
                    key={item.book_id}
                    book={item}
                    onOpenBook={onOpenBook}
                    onShowTakeaways={setSelectedTakeawayBook}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <BookTakeawaysModal
        book={selectedTakeawayBook}
        onClose={() => setSelectedTakeawayBook(null)}
      />
      <PaperDetailModal
        paper={selectedPaper}
        onClose={() => setSelectedPaper(null)}
      />
    </div>
  )
}
