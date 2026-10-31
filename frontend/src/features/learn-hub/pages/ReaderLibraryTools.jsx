import {useState} from 'react'
import {READING_STATUSES} from '../services/personalLibraryApi'
import {loadBookDocument} from '../services/bookAvailability'
import {resolveBookSource} from './bookSource'
import './personal-library.css'

export default function ReaderLibraryTools({item,book,busy,error,onRetry,onUpdate}) {
  const [page,setPage]=useState(book.libraryItem?.current_page || 1)
  const [saving,setSaving]=useState(false)
  const [message,setMessage]=useState('')
  const [failure,setFailure]=useState('')
  async function save(patch) {
    setSaving(true);setFailure('');setMessage('')
    try{await onUpdate(item.id,patch);setMessage('Đã lưu vào kệ sách.')}
    catch(cause){setFailure(cause.message)}finally{setSaving(false)}
  }
  async function download() {
    setSaving(true);setFailure('')
    try {
      const source=resolveBookSource(book)
      const {blob}=await loadBookDocument(source)
      const url=URL.createObjectURL(blob)
      const anchor=document.createElement('a');anchor.href=url;anchor.download=`${book.title.replace(/[/\\]/g,'-')}.pdf`
      document.body.append(anchor);anchor.click();anchor.remove()
      window.setTimeout(()=>URL.revokeObjectURL(url),30000)
    }catch(cause){setFailure(cause.message)}finally{setSaving(false)}
  }
  return <div className="pl-reading-tools">
    <label>Trạng thái đọc<select aria-label="Trạng thái đọc trong kệ" value={item?.status || 'want_to_read'} disabled={!item || busy || saving} onChange={event=>save({status:event.target.value})}>{Object.entries(READING_STATUSES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
    <form onSubmit={event=>{event.preventDefault();save({current_page:Number(page)})}}>
      <label>Trang đang đọc<input aria-label="Trang đang đọc" type="number" min="1" max={item?.page_count || 10000} required value={page} onChange={event=>setPage(event.target.value)} disabled={!item || saving}/>{item?.page_count?`/ ${item.page_count}`:''}</label>
      <button className="br-btn br-btn--ghost" disabled={!item || busy || saving}>Lưu vị trí</button>
    </form>
    {resolveBookSource(book).isPrivate && <button type="button" className="br-btn br-btn--ghost" onClick={download} disabled={saving}>Tải PDF</button>}
    <small role="status">{busy?'Đang lưu lịch sử…':message || (item?'Nhập và lưu trang để tiếp tục ở lần đọc sau.':'Lịch sử sẽ được lưu khi nội dung mở thành công.')}</small>
    {(error || failure) && <p className="pl-error" role="alert">{failure || error} {error && <button className="br-btn br-btn--ghost" onClick={onRetry}>Lưu lại lịch sử</button>}</p>}
  </div>
}
