import { CheckCircleIcon } from '../../../shared/Icons'

export default function BookTakeawaysModal({ book, onClose }) {
  if (!book) return null

  return (
    <div className="lh-modal-backdrop" onClick={onClose}>
      <div className="lh-modal" onClick={(e) => e.stopPropagation()}>
        <div className="lh-modal__header">
          <div>
            <span className="lh-modal__kicker">Tóm tắt ý chính</span>
            <h3 className="lh-modal__title">{book.title}</h3>
            <p className="lh-modal__sub">{book.author}</p>
          </div>
          <button
            type="button"
            className="lh-modal__close-btn"
            onClick={onClose}
            aria-label="Đóng"
          >
            <span aria-hidden="true" style={{ fontSize: '16px', lineHeight: 1 }}>✕</span>
          </button>
        </div>
        <div className="lh-modal__body">
          <p className="lh-modal__summary">{book.summary}</p>
          <h4 className="lh-modal__takeaways-title">3 Điểm cốt lõi rút ra</h4>
          <ul className="lh-modal__takeaways-list">
            {(book.key_takeaways || []).map((t, idx) => (
              <li key={idx}>
                <CheckCircleIcon size={16} className="lh-modal__check-icon" />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
