import { Calendar, ExternalLink, FileText, Sparkles, User } from 'lucide-react'
import AddToShelfButton from './AddToShelfButton'
import {safeBookUrl} from './bookSource'

export default function PaperCard({ paper, onViewDetail, onOpenBook, library }) {
  const isArxiv = paper.source === 'arxiv'
  const isFed = paper.source?.includes('fed')
  const isNber = paper.source === 'nber'

  const badgeClass = isArxiv
    ? 'lh-paper-badge--arxiv'
    : isFed
      ? 'lh-paper-badge--fed'
      : isNber
        ? 'lh-paper-badge--nber'
        : 'lh-paper-badge--default'

  return (
    <article className="lh-paper-card">
      <div className="lh-paper-card__header">
        <div className="lh-paper-card__badges">
          <span className={`lh-paper-badge ${badgeClass}`}>{paper.source_label}</span>
          {paper.category ? (
            <span className="lh-paper-badge lh-paper-badge--cat">{paper.category}</span>
          ) : null}
        </div>
        <div className="lh-paper-card__date" title="Ngày công bố">
          <Calendar size={12} />
          <span>{paper.date}</span>
        </div>
      </div>

      <h3 className="lh-paper-card__title" title={paper.title}>
        {paper.title}
      </h3>

      <div className="lh-paper-card__authors">
        <User size={13} className="lh-paper-card__author-icon" />
        <span className="lh-paper-card__author-text">{paper.author}</span>
      </div>

      <p className="lh-paper-card__abstract">
        {paper.abstract || paper.summary}
      </p>

      {paper.topics && paper.topics.length > 0 ? (
        <div className="lh-paper-card__topics">
          {paper.topics.slice(0, 3).map((topic) => (
            <span key={topic} className="lh-paper-topic-tag">
              #{topic}
            </span>
          ))}
        </div>
      ) : null}

      <div className="lh-paper-card__actions">
        <button
          type="button"
          className="lhc-btn lhc-btn--primary"
          onClick={() => onViewDetail?.(paper)}
        >
          <Sparkles size={13} />
          <span>Tóm tắt & Chi tiết</span>
        </button>

        {safeBookUrl(paper.pdf_url) ? (
          <button type="button" onClick={()=>onOpenBook?.(paper)}
            className="lhc-btn lhc-btn--outline"
            title="Mở toàn văn PDF"
          >
            <FileText size={13} />
            <span>PDF</span>
          </button>
        ) : null}

        {safeBookUrl(paper.url) ? (
          <a
            className="lhc-btn lhc-btn--ghost"
            href={safeBookUrl(paper.url)}
            target="_blank"
            rel="noreferrer"
            title="Đến trang xuất bản chính thức"
          >
            <ExternalLink size={13} />
          </a>
        ) : null}
        <AddToShelfButton book={paper} library={library}/>
      </div>
    </article>
  )
}
