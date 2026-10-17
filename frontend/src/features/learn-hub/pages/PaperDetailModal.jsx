import { Calendar, ExternalLink, FileText, User, X } from 'lucide-react'

export default function PaperDetailModal({ paper, onClose }) {
  if (!paper) return null

  return (
    <div className="lh-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="lh-modal-dialog lh-modal-dialog--paper"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="paper-modal-title"
      >
        <div className="lh-modal-header">
          <div className="lh-paper-card__badges">
            <span className="lh-paper-badge lh-paper-badge--arxiv">{paper.source_label}</span>
            {paper.category ? (
              <span className="lh-paper-badge lh-paper-badge--cat">{paper.category}</span>
            ) : null}
          </div>
          <button
            type="button"
            className="lh-modal-close-btn"
            onClick={onClose}
            aria-label="Đóng"
          >
            <X size={18} />
          </button>
        </div>

        <div className="lh-modal-body">
          <h2 id="paper-modal-title" className="lh-paper-modal__title">
            {paper.title}
          </h2>

          <div className="lh-paper-modal__meta-grid">
            <div className="lh-paper-modal__meta-item">
              <User size={14} className="lh-paper-modal__icon" />
              <div>
                <strong>Tác giả:</strong>
                <p>{paper.author}</p>
              </div>
            </div>

            <div className="lh-paper-modal__meta-item">
              <Calendar size={14} className="lh-paper-modal__icon" />
              <div>
                <strong>Ngày công bố:</strong>
                <p>{paper.date}</p>
              </div>
            </div>
          </div>

          <div className="lh-paper-modal__section">
            <h4 className="lh-paper-modal__section-title">Tóm tắt nghiên cứu (Abstract)</h4>
            <div className="lh-paper-modal__abstract-box">
              <p>{paper.abstract || 'Không có tóm tắt chi tiết cho bài báo này.'}</p>
            </div>
          </div>

          {paper.topics && paper.topics.length > 0 ? (
            <div className="lh-paper-modal__topics">
              <strong>Chủ đề liên quan:</strong>
              <div className="lh-paper-modal__tag-list">
                {paper.topics.map((t) => (
                  <span key={t} className="lh-paper-topic-tag">
                    #{t}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <div className="lh-modal-footer">
          {paper.pdf_url ? (
            <a
              className="lhc-btn lhc-btn--primary"
              href={paper.pdf_url}
              target="_blank"
              rel="noreferrer"
            >
              <FileText size={15} />
              <span>Mở toàn văn PDF</span>
            </a>
          ) : null}

          {paper.url ? (
            <a
              className="lhc-btn lhc-btn--outline"
              href={paper.url}
              target="_blank"
              rel="noreferrer"
            >
              <ExternalLink size={15} />
              <span>Trang xuất bản gốc</span>
            </a>
          ) : null}

          <button
            type="button"
            className="lhc-btn lhc-btn--ghost"
            onClick={onClose}
            style={{ marginLeft: 'auto' }}
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  )
}
