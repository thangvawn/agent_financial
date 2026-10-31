import {useState} from 'react'
import {BookOpen,FileText,Plus,Search} from 'lucide-react'
import {DOCUMENT_KINDS,READING_STATUSES,filterShelf,shelfBook} from '../services/personalLibraryApi'
import './personal-library.css'

function ShelfCard({item,onOpen,library}) {
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [editing,setEditing]=useState(false)
  const [confirmDelete,setConfirmDelete]=useState(false)
  const [title,setTitle]=useState(item.title)
  const [author,setAuthor]=useState(item.author)
  const [kind,setKind]=useState(item.kind)
  async function act(operation) {
    setBusy(true);setError('')
    try{await operation()}catch(cause){setError(cause.message)}finally{setBusy(false)}
  }
  return <article className="pl-card" data-library-id={item.id}>
    <div className="pl-card-heading"><span className="pl-kind"><FileText size={14}/>{DOCUMENT_KINDS[item.kind]}</span><span>{item.origin==='upload'?'PDF đã tải lên':'Từ thư viện'}</span></div>
    <h3>{item.title}</h3><p className="pl-author">{item.author || 'Chưa có tác giả'}</p>
    <div className="pl-card-meta"><span>{item.page_count?`${item.page_count} trang`:'Tài liệu trực tuyến'}</span>{item.size_bytes>0 && <span>{(item.size_bytes/1024/1024).toFixed(1)} MB</span>}</div>
    <label className="pl-status-label">Trạng thái đọc<select aria-label={`Trạng thái đọc: ${item.title}`} value={item.status} disabled={busy} onChange={event=>act(()=>library.update(item.id,{status:event.target.value}))}>{Object.entries(READING_STATUSES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
    {item.last_opened_at?<p className="pl-history">Đọc gần nhất: {new Date(item.last_opened_at).toLocaleString('vi-VN')}<br/>{item.read_count} lượt mở · Vị trí đã lưu: trang {item.current_page}</p>:<p className="pl-history">Chưa mở đọc</p>}
    <div className="pl-card-actions"><button type="button" className="lhc-btn lhc-btn--primary" onClick={()=>onOpen(shelfBook(item))}><BookOpen size={14}/>{item.read_count>0?'Đọc tiếp':'Mở đọc'}</button><button type="button" className="lhc-btn lhc-btn--outline" disabled={busy} onClick={()=>{setEditing(!editing);setConfirmDelete(false);setTitle(item.title);setAuthor(item.author);setKind(item.kind)}}>Sửa</button><button type="button" className="lhc-btn lhc-btn--ghost" disabled={busy} onClick={()=>{setConfirmDelete(true);setEditing(false)}}>Xóa khỏi kệ</button></div>
    {editing && <form className="pl-form pl-card-edit" onSubmit={event=>{event.preventDefault();act(async()=>{await library.update(item.id,{title,author,kind});setEditing(false)})}}>
      <label>Tên tài liệu<input required maxLength={240} value={title} onChange={event=>setTitle(event.target.value)}/></label>
      <label>Tác giả<input maxLength={240} value={author} onChange={event=>setAuthor(event.target.value)}/></label>
      <label>Loại tài liệu<select value={kind} onChange={event=>setKind(event.target.value)}>{Object.entries(DOCUMENT_KINDS).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
      <div className="pl-card-actions"><button className="lhc-btn lhc-btn--primary" disabled={busy}>Lưu thay đổi</button><button type="button" className="lhc-btn lhc-btn--outline" onClick={()=>setEditing(false)} disabled={busy}>Hủy sửa</button></div>
    </form>}
    {confirmDelete && <div className="pl-delete-confirm"><p>{item.origin==='upload'?'Xóa tài liệu sẽ xóa cả file PDF đã tải lên và lịch sử đọc của tài liệu này.':'Gỡ tài liệu và lịch sử đọc khỏi kệ cá nhân. Bản gốc trong thư viện vẫn còn.'}</p><div className="pl-card-actions"><button type="button" className="lhc-btn lhc-btn--outline" disabled={busy} onClick={()=>setConfirmDelete(false)}>Giữ lại</button><button type="button" className="lhc-btn pl-danger" disabled={busy} onClick={()=>act(()=>library.remove(item.id))}>Xác nhận xóa</button></div></div>}
    {error && <p className="pl-error" role="alert">{error}</p>}
  </article>
}

export default function PersonalLibrary({library,onOpenBook,onUpload,onBrowse}) {
  const [status,setStatus]=useState('all')
  const [kind,setKind]=useState('all')
  const [search,setSearch]=useState('')
  const items=filterShelf(library.items,{status,kind,search})
  const tabs={all:'Tất cả',...READING_STATUSES,history:'Lịch sử đọc'}
  const used=library.items.reduce((sum,item)=>sum+item.size_bytes,0)
  return <div className="pl-library">
    <header className="pl-header"><div><p className="pl-eyebrow">THƯ VIỆN CÁ NHÂN</p><h2>Kệ sách của tôi</h2><p>Sách đã lưu, tài liệu của bạn và những lần đọc gần đây.</p></div><button className="lhc-btn lhc-btn--primary" onClick={onUpload}><Plus size={16}/>Thêm tài liệu</button></header>
    <div className="pl-overview"><span><strong>{library.items.length}</strong> tài liệu trên kệ</span><span><strong>{library.items.filter(item=>item.status==='completed').length}</strong> đã đọc</span><span>{(used/1024/1024).toFixed(1)} / 500 MB đã dùng</span></div>
    <nav className="pl-filters" aria-label="Kệ và lịch sử đọc">{Object.entries(tabs).map(([id,label])=><button key={id} type="button" aria-pressed={status===id} className={status===id?'is-active':''} onClick={()=>setStatus(id)}>{label}<span>{id==='all'?library.items.length:library.items.filter(item=>id==='history'?item.read_count>0:item.status===id).length}</span></button>)}</nav>
    <div className="pl-search-row"><label className="pl-search"><Search size={16}/><input aria-label="Tìm trong kệ sách" type="search" placeholder="Tìm tên tài liệu hoặc tác giả" value={search} onChange={event=>setSearch(event.target.value)}/></label><label>Loại tài liệu<select aria-label="Loại tài liệu trên kệ" value={kind} onChange={event=>setKind(event.target.value)}><option value="all">Tất cả loại</option>{Object.entries(DOCUMENT_KINDS).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label></div>
    {library.error && <div className="pl-error" role="alert">{library.error} <button className="lhc-btn lhc-btn--outline" onClick={()=>library.refresh()}>Thử lại</button></div>}
    {library.loading?<p role="status">Đang tải kệ sách…</p>:items.length?<div className="pl-grid">{items.map(item=><ShelfCard key={item.id} item={item} library={library} onOpen={onOpenBook}/>)}</div>:<div className="pl-empty"><BookOpen size={32}/><h3>{status==='history'?'Chưa có lịch sử đọc':'Chưa có tài liệu phù hợp'}</h3><p>{status==='history'?'Mở một tài liệu để bắt đầu. Lịch sử được lưu khi nội dung tải thành công.':'Tải PDF từ máy lên hoặc thêm tài liệu từ thư viện vào kệ.'}</p><button className="lhc-btn lhc-btn--outline" onClick={onBrowse}>Khám phá thư viện</button></div>}
  </div>
}
