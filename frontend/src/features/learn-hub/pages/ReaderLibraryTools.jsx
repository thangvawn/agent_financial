import {useId,useState} from 'react'
import {READING_STATUSES} from '../services/personalLibraryApi'
import {loadBookDocument} from '../services/bookAvailability'
import {resolveBookSource} from './bookSource'
import './personal-library.css'
import {Bookmark,ChevronDown,Download} from 'lucide-react'

export default function ReaderLibraryTools({item,book,busy,error,onRetry,onUpdate}) {
  const [expanded,setExpanded]=useState(false)
  const fieldsId=useId()
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
  const totalPages=item?.page_count || 0
  const savedPage=item?.current_page || 1
  const progress=totalPages?Math.min(100,Math.round(savedPage/totalPages*100)):0
  return <div className={`pl-reading-tools${expanded?' is-expanded':''}`} onKeyDown={event=>{
    if(event.key==='Escape' && expanded){setExpanded(false);event.currentTarget.querySelector('.br-reading-toggle')?.focus()}
  }}>
    <button type="button" className="br-reading-toggle br-btn" aria-label="Vị trí đọc" aria-expanded={expanded} aria-controls={fieldsId} onClick={()=>setExpanded(value=>!value)}><Bookmark size={14}/><span>Trang {savedPage}{totalPages?` / ${totalPages}`:''}</span><ChevronDown size={13}/></button>
    <div id={fieldsId} className="br-reading-fields">
    <label>Trạng thái đọc<select aria-label="Trạng thái đọc trong kệ" value={item?.status || 'want_to_read'} disabled={!item || busy || saving} onChange={event=>save({status:event.target.value})}>{Object.entries(READING_STATUSES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
    <form onSubmit={event=>{event.preventDefault();save({current_page:Number(page)})}}>
      <label>Trang đang đọc<input aria-label="Trang đang đọc" type="number" min="1" max={item?.page_count || 10000} required value={page} onChange={event=>setPage(event.target.value)} disabled={!item || saving}/>{item?.page_count?`/ ${item.page_count}`:''}</label>
      <button className="br-btn br-btn--ghost" title="Nhập và lưu trang để đọc tiếp ở lần mở sau" disabled={!item || busy || saving}><Bookmark size={14}/>Lưu vị trí</button>
    </form>
    {resolveBookSource(book).isPrivate && <button type="button" className="br-btn br-btn--ghost" onClick={download} disabled={saving}><Download size={14}/>Tải PDF</button>}
    {totalPages>0 && <div className="br-reading-progress" title={`Vị trí đã lưu: trang ${savedPage}/${totalPages}`}><div role="progressbar" aria-label="Vị trí đã lưu" aria-valuemin={0} aria-valuemax={totalPages} aria-valuenow={savedPage}><span style={{width:`${progress}%`}}/></div><span>{progress}%</span></div>}
    <small role="status" className={busy || message?'br-reading-feedback':'br-reading-help'}>{busy?'Đang lưu lịch sử…':message || (item?'Lưu trang để đọc tiếp lần sau.':'Lịch sử sẽ được lưu khi nội dung mở thành công.')}</small>
    </div>
    {(error || failure) && <p className="pl-error" role="alert">{failure || error} {error && <button className="br-btn br-btn--ghost" onClick={onRetry}>Lưu lại lịch sử</button>}</p>}
  </div>
}
