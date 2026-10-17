import { useEffect, useMemo, useState } from 'react'

import { BookIcon, FileTextIcon, SearchIcon } from '../../../shared/Icons'
import { DEMO_BOOKS, normalizeDbBook } from '../content/courseCatalogData'
import { fetchLearningCatalog } from '../services/learningApi'
import BookTakeawaysModal from './BookTakeawaysModal'

const BOOK_TABS = [
  { id: 'all', label: 'Tất cả' },
  { id: 'vi', label: '🇻🇳 Tiếng Việt' },
  { id: 'classics', label: '⭐ Kinh điển' },
  { id: 'investing', label: '📈 Đầu tư & Cổ phiếu' },
  { id: 'valuation', label: '💎 Định giá' },
]

export default function BookGrid({ onOpenBook }) {
  const [dbBooks, setDbBooks] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTakeawayBook, setSelectedTakeawayBook] = useState(null)
  const [activeFilter, setActiveFilter] = useState('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    let cancelled = false
    fetchLearningCatalog('book', { limit: 150 })
      .then((res) => {
        if (cancelled) return
        if (Array.isArray(res?.items) && res.items.length > 0) {
          const normalized = res.items.map(normalizeDbBook)
          const dbIds = new Set(normalized.map((b) => b.book_id))
          const extras = DEMO_BOOKS.filter((b) => !dbIds.has(b.book_id))
          setDbBooks([...extras, ...normalized])
        } else {
          setDbBooks(DEMO_BOOKS)
        }
      })
      .catch(() => { if (!cancelled) setDbBooks(DEMO_BOOKS) })
      .finally(() => { if (!cancelled) setIsLoading(false) })
    return () => { cancelled = true }
  }, [])

  const filteredBooks = useMemo(() => {
    let list = dbBooks.length > 0 ? dbBooks : DEMO_BOOKS
    if (activeFilter === 'vi') {
      list = list.filter((b) => b.language === 'vi' || /tiếng việt/i.test(b.title))
    } else if (activeFilter === 'classics') {
      list = list.filter((b) => b.book_id?.includes('curated') || b.rating >= 4.7)
    } else if (activeFilter === 'investing') {
      list = list.filter((b) => b.category === 'stocks' || b.category === 'portfolio_theory' || /đầu tư|invest/i.test(b.title))
    } else if (activeFilter === 'valuation') {
      list = list.filter((b) => b.category === 'valuation' || /định giá|valuation/i.test(b.title))
    }

    if (search.trim()) {
      const q = search.toLowerCase().trim()
      list = list.filter((b) => `${b.title} ${b.author} ${b.summary}`.toLowerCase().includes(q))
    }
    return list
  }, [dbBooks, activeFilter, search])

  return (
    <section className="lh-section lh-section--books" aria-labelledby="lh-books-title">
      <div className="lh-section__header">
        <div>
          <h2 id="lh-books-title" className="lh-section__title">
            Tủ sách & Học liệu Tài chính
            <span className="lh-section__count">{filteredBooks.length}</span>
          </h2>
          <p className="lh-section__subtitle">
            Sách chọn lọc, tài liệu PDF công cộng từ Internet Archive và tác phẩm kinh điển
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="lh-books-toolbar" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div className="lhc-filter-pills" role="tablist">
          {BOOK_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`lhc-pill ${activeFilter === tab.id ? 'lhc-pill--active' : ''}`}
              onClick={() => setActiveFilter(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="lhc-search-box" style={{ maxWidth: '280px', marginLeft: 'auto' }}>
          <SearchIcon size={16} className="lhc-search-box__icon" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo tên sách, tác giả..."
            className="lhc-search-box__input"
          />
        </div>
      </div>

      {isLoading && dbBooks.length === 0 ? (
        <div className="lh-empty-state"><p>Đang tải danh mục sách từ cơ sở dữ liệu...</p></div>
      ) : filteredBooks.length === 0 ? (
        <div className="lh-empty-state"><p>Không tìm thấy cuốn sách nào phù hợp với bộ lọc.</p></div>
      ) : (
        <div className="lh-books-grid">
          {filteredBooks.map((book) => (
            <article
              key={book.book_id}
              className="lh-book-card"
              onClick={() => onOpenBook?.(book)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') onOpenBook?.(book) }}
            >
              <div className="lh-book-card__cover" style={{ background: book.cover_color }}>
                {book.cover_image ? (
                  <img src={book.cover_image} alt={book.title} className="lh-book-card__img" loading="lazy" onError={(e) => { e.target.style.display = 'none' }} />
                ) : (
                  <>
                    <div className="lh-book-card__spine" />
                    <BookIcon size={32} className="lh-book-card__icon" />
                  </>
                )}
                <span className="lh-book-card__rating">★ {book.rating}</span>
              </div>

              <div className="lh-book-card__body">
                <div className="lh-book-card__header-line">
                  <span className="lh-book-card__author">{book.author}</span>
                  <span className="lh-book-card__category-badge">
                    {book.language === 'vi' ? 'Tiếng Việt' : 'Tài chính'}
                  </span>
                </div>
                <h3 className="lh-book-card__title">{book.title}</h3>
                <p className="lh-book-card__summary">{book.summary}</p>
                <div className="lh-book-card__meta">
                  <span>📖 {typeof book.pages === 'number' ? `${book.pages} trang` : book.pages}</span>
                  <span>•</span>
                  <span>⏱ ~{book.read_time}</span>
                </div>
                <div className="lh-book-card__actions" onClick={(e) => e.stopPropagation()}>
                  <button type="button" className="lhc-btn lhc-btn--primary" onClick={() => onOpenBook?.(book)}>
                    <BookIcon size={14} /> Đọc sách (Tab Reader)
                  </button>
                  <button type="button" className="lhc-btn lhc-btn--outline" onClick={() => setSelectedTakeawayBook(book)}>
                    Tóm tắt
                  </button>
                  {book.pdf_url ? (
                    <a className="lhc-btn lhc-btn--outline" href={book.pdf_url} target="_blank" rel="noreferrer" title="Tải PDF">
                      <FileTextIcon size={14} /> PDF
                    </a>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <BookTakeawaysModal book={selectedTakeawayBook} onClose={() => setSelectedTakeawayBook(null)} />
    </section>
  )
}
