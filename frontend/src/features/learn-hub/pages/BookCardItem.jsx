import {BookIcon} from '../../../shared/Icons'
import {resolveBookSource,safeBookUrl} from './bookSource'
import {BOOK_STATUS_LABELS} from '../services/bookAvailability'

export default function BookCardItem({book,onOpenBook,onShowTakeaways,availability}) {
  const source=resolveBookSource(book)
  const originUrl=safeBookUrl(book.source_url) || source.openUrl
  const status=availability?.status || 'unchecked'
  const isPdf=(availability?.kind || source.kind)==='pdf'
  const pdfUrl=availability?.status==='ready' && isPdf ? availability.viewUrl || source.viewUrl : ''
  const role=source.contentRole==='notes'?'Bài ghi chú':source.contentRole==='sample'?'Tài liệu mẫu':isPdf?'PDF · Toàn văn':'Sách / học liệu'
  const label=status==='ready' ? (source.contentRole==='notes'?'Đọc ghi chú':isPdf?'Đọc PDF':'Đọc tài liệu') : ['unchecked','checking'].includes(status)?'Kiểm tra & đọc':'Kiểm tra nguồn'
  return <article className="lh-book-card" data-book-id={book.book_id}>
    <div className="lh-book-card__cover" style={{background:book.cover_color}}>
      <BookIcon size={32} className="lh-book-card__icon"/>
      {book.cover_image && <img src={book.cover_image} alt="" className="lh-book-card__img" loading="lazy" referrerPolicy="no-referrer" onError={event=>{event.currentTarget.style.display='none'}}/>}
      <span className="lh-book-card__rating">{role}</span>
    </div>
    <div className="lh-book-card__body">
      <div className="lh-book-card__header-line"><span className="lh-book-card__author">{book.author}</span><span className="lh-book-card__category-badge">{book.language==='vi'?'Tiếng Việt':book.language==='en'?'Tiếng Anh':''}</span></div>
      <h3 className="lh-book-card__title"><button type="button" onClick={()=>onOpenBook?.(book)}>{book.title}</button></h3>
      <span className={`book-source-badge book-source-badge--${status}`}>{BOOK_STATUS_LABELS[status]}</span>
      <p className="lh-book-card__summary">{book.summary}</p>
      {availability?.message && status!=='ready' && <p className="book-source-message">{availability.message}</p>}
      <div className="lh-book-card__meta">{source.contentRole!=='notes' && book.pages && <span>{typeof book.pages==='number'?`${book.pages} trang`:book.pages}</span>}{source.contentRole!=='notes' && book.read_time && <span>~{book.read_time}</span>}{availability?.checked_at && <span>Kiểm tra {new Date(availability.checked_at).toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'})}</span>}</div>
      <div className="lh-book-card__actions">
        <button type="button" className="lhc-btn lhc-btn--primary" onClick={()=>onOpenBook?.(book)}><BookIcon size={14}/>{label}</button>
        {pdfUrl && <a className="lhc-btn lhc-btn--outline" href={pdfUrl} download={book.file_name || 'sach.pdf'}>Tải PDF</a>}
        <button type="button" className="lhc-btn lhc-btn--outline" onClick={()=>onShowTakeaways?.(book)}>Tóm tắt</button>
        {originUrl && <a className="lhc-btn lhc-btn--outline" href={originUrl} target="_blank" rel="noreferrer">Nguồn</a>}
      </div>
    </div>
  </article>
}
