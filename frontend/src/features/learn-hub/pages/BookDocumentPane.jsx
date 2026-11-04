import {resolveBookSource} from './bookSource'
import {PdfBookPane,DocumentFilePane} from './PdfBookPane'
import {useBookAvailability} from '../hooks/useBookAvailability'
import {BOOK_STATUS_LABELS} from '../services/bookAvailability'

export function BookDocumentPane({book,onReady,initialPage=1}) {
  return book ? <BookDocumentContent key={book.book_id || book.asset_id || book.url} book={book} onReady={onReady} initialPage={initialPage} /> : null
}
function BookDocumentContent({book,onReady,initialPage}) {
  const source=resolveBookSource(book)
  const {state,retry}=useBookAvailability(book)
  return <div className="br-doc-container">
    <div className="br-doc-body">
      {state.status==='checking' ? <div className="br-source-state" role="status"><h3>Đang kiểm tra nguồn tài liệu…</h3><p>Đang xác định bản đọc hiện còn truy cập được.</p></div>
        :state.status==='ready' ? (state.kind==='pdf' ? <PdfBookPane source={state} title={book.title} onReady={onReady} initialPage={initialPage}/> : <DocumentFilePane source={state} title={book.title} onReady={onReady}/>)
          :<div className="br-source-state" role="status"><h3>{BOOK_STATUS_LABELS[state.status]}</h3><p>{state.message}</p><p className="br-doc__meta">Bạn vẫn có thể sử dụng sổ ghi chú.</p><div className="br-source-actions"><button className="br-btn br-btn--ghost" onClick={retry}>Kiểm tra lại nguồn</button>{source.openUrl && <a className="br-btn br-btn--ghost" href={source.openUrl} target="_blank" rel="noreferrer">Xem trang nguồn</a>}</div></div>}
    </div>
  </div>
}
