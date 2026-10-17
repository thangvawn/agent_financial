import { BookIcon, FileTextIcon } from '../../../shared/Icons'

export default function BookCardItem({ book, onOpenBook, onShowTakeaways }) {
  return (
    <article
      className="lh-book-card"
      onClick={() => onOpenBook?.(book)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onOpenBook?.(book) }}
    >
      <div className="lh-book-card__cover" style={{ background: book.cover_color }}>
        {book.cover_image ? (
          <img
            src={book.cover_image}
            alt={book.title}
            className="lh-book-card__img"
            loading="lazy"
            onError={(e) => { e.target.style.display = 'none' }}
          />
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
          <button
            type="button"
            className="lhc-btn lhc-btn--primary"
            onClick={() => onOpenBook?.(book)}
          >
            <BookIcon size={14} /> Đọc sách (Tab Reader)
          </button>
          <button
            type="button"
            className="lhc-btn lhc-btn--outline"
            onClick={() => onShowTakeaways?.(book)}
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
  )
}
