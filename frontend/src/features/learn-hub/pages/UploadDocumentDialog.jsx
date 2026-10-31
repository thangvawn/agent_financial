import {useEffect,useRef,useState} from 'react'
import {Upload, X} from 'lucide-react'
import {DOCUMENT_KINDS,validateUpload} from '../services/personalLibraryApi'
import './personal-library.css'

export default function UploadDocumentDialog({onClose,onUpload,onAdded}) {
  const dialog=useRef(null)
  const [file,setFile]=useState(null)
  const [title,setTitle]=useState('')
  const [author,setAuthor]=useState('')
  const [kind,setKind]=useState('book')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  useEffect(()=>{const node=dialog.current;node.showModal();return()=>node.close()},[])
  async function submit(event) {
    event.preventDefault()
    const invalid=validateUpload(file)
    if(invalid){setError(invalid);return}
    if(!title.trim()){setError('Nhập tên tài liệu.');return}
    setBusy(true);setError('')
    try {const item=await onUpload(file,{title:title.trim(),author:author.trim(),kind});onAdded(item);onClose()}
    catch(cause){setError(cause.message);setBusy(false)}
  }
  return <dialog ref={dialog} className="pl-dialog" aria-labelledby="upload-document-title" onCancel={event=>{event.preventDefault();if(!busy)onClose()}}>
    <form onSubmit={submit} className="pl-form">
      <div className="pl-dialog-heading"><h2 id="upload-document-title">Thêm tài liệu từ máy</h2><button type="button" className="pl-icon-button" aria-label="Đóng thêm tài liệu" onClick={onClose} disabled={busy}><X size={20}/></button></div>
      <p>PDF của bạn được lưu riêng trong kệ sách và có thể đọc lại khi đăng nhập.</p>
      <label className="pl-file-field"><Upload size={24}/><strong>Chọn PDF</strong><span>Tối đa 40 MB mỗi file · Sách, paper hoặc tài liệu</span>
        <input type="file" accept=".pdf,application/pdf" aria-label="File PDF" disabled={busy} onChange={event=>{
          const selected=event.target.files?.[0] || null;setFile(selected);setError('')
          if(selected && !title)setTitle(selected.name.replace(/\.pdf$/i,'').replace(/[_-]/g,' ').slice(0,240))
        }}/>
      </label>
      {file && <p className="pl-file-name">{file.name} · {(file.size/1024/1024).toFixed(2)} MB</p>}
      <label>Tên tài liệu<input autoComplete="off" value={title} maxLength={240} required disabled={busy} onChange={event=>setTitle(event.target.value)}/></label>
      <div className="pl-form-row">
        <label>Tác giả<input value={author} maxLength={240} disabled={busy} onChange={event=>setAuthor(event.target.value)} placeholder="Không bắt buộc"/></label>
        <label>Loại tài liệu<select aria-label="Loại tài liệu" value={kind} disabled={busy} onChange={event=>setKind(event.target.value)}>{Object.entries(DOCUMENT_KINDS).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
      </div>
      {error && <p role="alert" className="pl-error">{error}</p>}
      <div className="pl-dialog-actions"><button type="button" className="lhc-btn lhc-btn--outline" onClick={onClose} disabled={busy}>Hủy</button><button className="lhc-btn lhc-btn--primary" disabled={busy}>{busy?'Đang tải & kiểm tra PDF…':'Tải lên kệ sách'}</button></div>
    </form>
  </dialog>
}
