import {authenticatedFetch} from '../../auth/services/sessionClient.js'
import {resolveBookSource} from '../pages/bookSource.js'

const BASE='/api/v1/public/learning/library'
export const READING_STATUSES={want_to_read:'Muốn đọc',reading:'Đang đọc',completed:'Đã đọc'}
export const DOCUMENT_KINDS={book:'Sách',paper:'Paper',document:'Tài liệu'}

async function request(path,sessionId,options={}) {
  const response=await authenticatedFetch(BASE+path,options,sessionId)
  if(response.status===204)return null
  const body=await response.json().catch(()=>null)
  if(!response.ok)throw new Error(typeof body?.detail==='string'?body.detail:response.status===401?'Vui lòng đăng nhập để dùng kệ sách cá nhân.':'Chưa lưu được tài liệu. Vui lòng thử lại.')
  return body
}
const jsonOptions=(method,body)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
export const fetchPersonalLibrary=(sessionId,signal)=>request('',sessionId,{signal})
export const saveCatalogDocument=(sessionId,document)=>request('/items',sessionId,jsonOptions('POST',document))
export const fetchLibraryItem=(sessionId,id)=>request(`/items/${encodeURIComponent(id)}`,sessionId)
export const updateLibraryItem=(sessionId,id,patch)=>request(`/items/${encodeURIComponent(id)}`,sessionId,jsonOptions('PATCH',patch))
export const openLibraryItem=(sessionId,id,eventId)=>request(`/items/${encodeURIComponent(id)}/open`,sessionId,jsonOptions('POST',{event_id:eventId}))
export const deleteLibraryItem=(sessionId,id)=>request(`/items/${encodeURIComponent(id)}`,sessionId,{method:'DELETE'})
export function uploadLibraryDocument(sessionId,file,metadata) {
  const form=new FormData()
  form.set('file',file)
  for(const [key,value] of Object.entries(metadata))form.set(key,value)
  return request('/uploads',sessionId,{method:'POST',body:form})
}
export function catalogDocument(book) {
  const source=resolveBookSource(book)
  if(!source.sourceUrl || source.isPrivate)throw new Error('Tài liệu chưa có nguồn hợp lệ để thêm vào kệ.')
  const pages=Number(book.pages)
  return {title:(book.title || 'Tài liệu').slice(0,240),author:(book.author || '').slice(0,240),
    kind:book.type==='paper'?'paper':'book',source_url:source.sourceUrl,content_role:source.contentRole,
    source_id:String(book.asset_id || book.book_id || book.paper_id || '').slice(0,240),
    page_count:Number.isInteger(pages) && pages>0 && pages<=10000?pages:null}
}
export function shelfBook(item) {
  return {book_id:item.source_id || item.id,asset_id:item.source_id || item.id,library_id:item.id,
    libraryItem:item,title:item.title,author:item.author,type:item.kind,pages:item.page_count,
    url:item.file_url || item.source_url,content_role:item.content_role,cover_color:'#e6ece6'}
}
export function filterShelf(items,{status='all',kind='all',search=''}={}) {
  const query=search.toLocaleLowerCase('vi').trim()
  return items.filter(item=>(status==='all' || (status==='history'?item.read_count>0:item.status===status))
    && (kind==='all' || item.kind===kind)
    && `${item.title} ${item.author}`.toLocaleLowerCase('vi').includes(query))
    .sort((a,b)=>String(status==='history'?b.last_opened_at:b.updated_at).localeCompare(String(status==='history'?a.last_opened_at:a.updated_at)))
}
export function validateUpload(file) {
  if(!file)return 'Chọn một file PDF từ máy của bạn.'
  if(!/\.pdf$/i.test(file.name))return 'Chỉ hỗ trợ file PDF.'
  if(file.size===0)return 'File đang trống. Hãy chọn một PDF hợp lệ.'
  if(file.size>40*1024*1024)return 'Mỗi PDF tối đa 40 MB.'
  return ''
}
