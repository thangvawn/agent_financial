import {bookSourceKey,mergeBookCatalog,cachedBookCheck} from '../services/bookAvailability'
import {useLibrarySourceChecks} from '../hooks/useBookAvailability'
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
  const [sourceFilter, setSourceFilter] = useState('all')
  const [page, setPage] = useState(0)
  const [scan, setScan] = useState({all:false,startedAt:0})
  const [catalogNotice, setCatalogNotice] = useState('')
  const [displayChecks, setDisplayChecks] = useState({})

  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetchLearningCatalog('book', { limit: 120 }).catch(() => ({ items: [], warning:true })),
      fetchLearningCatalog('paper', { limit: 120 }).catch(() => ({ items: [], warning:true })),
    ]).then(([resBooks, resPapers]) => {
      if (cancelled) return
      const rawBooks = Array.isArray(resBooks?.items) && resBooks.items.length > 0
        ? resBooks.items.map(normalizeDbBook).filter(Boolean)
        : []
      const combinedBooks = mergeBookCatalog([...rawBooks, ...DEMO_BOOKS])
      if(resBooks.warning || resPapers.warning) setCatalogNotice('Chưa tải được đầy đủ catalog. Các tài liệu có sẵn vẫn được hiển thị và kiểm tra nguồn.')
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
    if(sourceFilter!=='all') pool=pool.filter(item=>item.type==='book' && (displayChecks[bookSourceKey(item)]?.status || cachedBookCheck(bookSourceKey(item))?.status || 'unchecked')===sourceFilter)
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
  }, [books, papers, docType, activeFolderId, search, sourceFilter, displayChecks])

  const filterScope=`${docType}:${activeFolderId}:${search}:${sourceFilter}`
  const [lastFilterScope,setLastFilterScope]=useState(filterScope)
  if(lastFilterScope!==filterScope){setLastFilterScope(filterScope);setPage(0)}
  const pageCount=Math.max(1,Math.ceil(filteredItems.length/12))
  const currentPage=Math.min(page,pageCount-1)
  const visibleItems=useMemo(()=>filteredItems.slice(currentPage*12,currentPage*12+12),[filteredItems,currentPage])
  const targets=scan.all ? books : visibleItems.filter(item=>item.type==='book')
  const completed=books.filter(book=>Date.parse(displayChecks[bookSourceKey(book)]?.checked_at || '')>=scan.startedAt).length
  const scanning=scan.all && completed<books.length
  const checks=useLibrarySourceChecks(targets,{enabled:!scan.all || scanning,force:scan.all,runKey:scan.startedAt})
  // Derive the filterable snapshot without re-starting a batch when results arrive.
  if(checks!==displayChecks)setDisplayChecks(checks)
  const checked=books.filter(book=>checks[bookSourceKey(book)] || cachedBookCheck(bookSourceKey(book))).length
  const readable=books.filter(book=>(checks[bookSourceKey(book)] || cachedBookCheck(bookSourceKey(book)))?.status==='ready').length

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
            Tìm học liệu theo chủ đề và xem trạng thái nguồn trước khi đọc.
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
            aria-label="Tìm sách và tài liệu"
            placeholder="Tìm theo tên sách, tác giả, abstract..."
            className="lhc-search-box__input"
          />
        </div>
      </div>

      <div className="lh-source-toolbar">
        <div><strong>{readable} sách đọc được</strong><span> · Đã kiểm tra {checked}/{books.length} nguồn sách</span><p>Tự kiểm tra sách trên trang đang xem. Các trạng thái chỉ phản ánh lần kiểm tra gần nhất.</p></div>
        <label>Trạng thái sách <select value={sourceFilter} onChange={event=>setSourceFilter(event.target.value)} aria-label="Lọc trạng thái nguồn sách">
          <option value="all">Tất cả</option><option value="ready">Đã kiểm tra · đọc được</option><option value="missing">Không còn tại nguồn</option><option value="restricted">Hạn chế truy cập</option><option value="unavailable">Tạm chưa kết nối</option><option value="invalid">Nguồn không hợp lệ</option><option value="load_failed">Chưa mở được tài liệu</option><option value="external">Xem tại nguồn</option><option value="too_large">Trên 40 MB · mở tại nguồn</option><option value="unchecked">Chưa kiểm tra</option>
        </select></label>
        <button type="button" className="lhc-btn lhc-btn--outline" onClick={()=>setScan(scanning?{all:false,startedAt:0}:{all:true,startedAt:Date.now()})}>{scanning?`Dừng kiểm tra (${completed}/${books.length})`:'Kiểm tra lại toàn bộ sách'}</button>
      </div>
      {catalogNotice && <p role="status">{catalogNotice}</p>}
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
                onClick={() => { setSearch(''); setActiveFolderId('all'); setDocType('all'); setSourceFilter('all') }}
                style={{ marginTop: '0.75rem' }}
              >
                Đặt lại tất cả bộ lọc
              </button>
            </div>
          ) : (
            <div className={docType === 'paper' ? 'lh-papers-grid' : 'lh-books-grid'}>
              {visibleItems.map((item) => {
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
                    availability={checks[bookSourceKey(item)] || cachedBookCheck(bookSourceKey(item))}
                    onOpenBook={onOpenBook}
                    onShowTakeaways={setSelectedTakeawayBook}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      {pageCount>1 && <nav className="lh-book-pagination" aria-label="Trang tài liệu"><button className="lhc-btn lhc-btn--outline" disabled={currentPage===0} onClick={()=>setPage(currentPage-1)}>Trang trước</button><span>Trang {currentPage+1}/{pageCount}</span><button className="lhc-btn lhc-btn--outline" disabled={currentPage===pageCount-1} onClick={()=>setPage(currentPage+1)}>Trang sau</button></nav>}
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
