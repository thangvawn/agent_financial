import { useState } from 'react'

import { BookIcon, FileTextIcon, PlayIcon } from '../../../shared/Icons'
import { DEMO_BOOKS } from '../content/courseCatalogData'

export default function BookGrid({ onOpenBook }) {
  const [selectedTakeawayBook, setSelectedTakeawayBook] = useState(null)

  return (
    <section className="lh-section lh-section--books" aria-labelledby="lh-books-title">
      <div className="lh-section__header">
        <div>
          <h2 id="lh-books-title" className="lh-section__title">
            Tủ sách & Học liệu Tài chính
            <span className="lh-section__count">{DEMO_BOOKS.length}</span>
          </h2>
          <p className="lh-section__subtitle">Sách chọn lọc, tóm tắt ý chính và hỗ trợ đọc trực tiếp qua tab Reader Workspace</p>
        </div>
      </div>

      <div className="lh-books-grid">
        {DEMO_BOOKS.map((book) => (
          <article
            key={book.book_id}
            className="lh-book-card"
            onClick={() => onOpenBook?.(book)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter') onOpenBook?.(book) }}
          >
            {/* Left side: Book Cover Image */}
            <div className="lh-book-card__cover" style={{ background: book.cover_color }}>
              {book.cover_image ? (
                <img src={book.cover_image} alt={book.title} className="lh-book-card__img" loading="lazy" />
              ) : (
                <>
                  <div className="lh-book-card__spine" />
                  <BookIcon size={32} className="lh-book-card__icon" />
                </>
              )}
              <span className="lh-book-card__rating">★ {book.rating}</span>
            </div>

            {/* Right side: Book Info & Actions */}
            <div className="lh-book-card__body">
              <div className="lh-book-card__header-line">
                <span className="lh-book-card__author">{book.author}</span>
                <span className="lh-book-card__category-badge">{book.category === 'finance' ? 'Tài chính' : book.category === 'investing' ? 'Đầu tư' : 'Phân tích'}</span>
              </div>
              <h3 className="lh-book-card__title">{book.title}</h3>
              <p className="lh-book-card__sub">{book.original_title}</p>
              <p className="lh-book-card__summary">{book.summary}</p>

              <div className="lh-book-card__meta">
                <span>📖 {book.pages} trang</span>
                <span>•</span>
                <span>⏱ ~{book.read_time}</span>
              </div>

              <div className="lh-book-card__actions" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="lhc-btn lhc-btn--primary"
                  onClick={() => onOpenBook?.(book)}
                >
                  <BookIcon size={14} /> Đọc sách (Mở Tab Reader)
                </button>
                <button
                  type="button"
                  className="lhc-btn lhc-btn--outline"
                  onClick={() => setSelectedTakeawayBook(book)}
                >
                  Tóm tắt
                </button>
                {book.pdf_url ? (
                  <a
                    className="lhc-btn lhc-btn--outline"
                    href={book.pdf_url}
                    target="_blank"
                    rel="noreferrer"
                    title="Tải PDF"
                  >
                    <FileTextIcon size={14} /> PDF
                  </a>
                ) : null}
              </div>
            </div>
          </article>
        ))}
      </div>

      {/* Key takeaways modal */}
      {selectedTakeawayBook ? (
        <div className="lh-modal-backdrop" onClick={() => setSelectedTakeawayBook(null)}>
          <div className="lh-modal" onClick={(e) => e.stopPropagation()}>
            <div className="lh-modal__header">
              <div>
                <span className="lh-modal__kicker">Tóm tắt ý chính</span>
                <h3 className="lh-modal__title">{selectedTakeawayBook.title}</h3>
                <p className="lh-modal__sub">{selectedTakeawayBook.author}</p>
              </div>
              <button
                type="button"
                className="lh-modal__close"
                onClick={() => setSelectedTakeawayBook(null)}
              >
                ✕
              </button>
            </div>
            <div className="lh-modal__body">
              <h4>3 Bài học đắt giá nhất:</h4>
              <ul className="lh-modal__takeaways">
                {selectedTakeawayBook.key_takeaways.map((item, idx) => (
                  <li key={idx}>
                    <span className="lh-modal__takeaway-num">{idx + 1}</span>
                    <p>{item}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="lh-modal__footer">
              <button
                type="button"
                className="lhc-btn lhc-btn--primary"
                onClick={() => {
                  const b = selectedTakeawayBook
                  setSelectedTakeawayBook(null)
                  onOpenBook?.(b)
                }}
              >
                Đọc sách ngay (Mở Tab Reader)
              </button>
              <button
                type="button"
                className="lhc-btn lhc-btn--outline"
                onClick={() => setSelectedTakeawayBook(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
