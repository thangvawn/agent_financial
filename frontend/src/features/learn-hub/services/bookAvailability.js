import {resolveBookSource,isPrivateLibraryUrl} from '../pages/bookSource.js'
import {authenticatedFetch} from '../../auth/services/sessionClient.js'

export const BOOK_STATUS_LABELS = {
  load_failed:'Chưa mở được tài liệu', unchecked:'Chưa kiểm tra', checking:'Đang kiểm tra', ready:'Đọc được', missing:'Không còn tại nguồn',
  restricted:'Hạn chế truy cập', unavailable:'Tạm chưa kết nối', invalid:'Nguồn không hợp lệ',
  external:'Xem tại nguồn', too_large:'Mở tại nguồn · trên 40 MB',
}
export const MAX_BOOK_BYTES=40*1024*1024
const cache=new Map()
export const bookSourceKey=book=>resolveBookSource(book).sourceUrl || `missing:${book.book_id || book.asset_id || book.title}`
export function cachedBookCheck(key) {
  const entry=cache.get(key)
  return entry && entry.expires>Date.now() ? entry.result : null
}
export function clearBookCheck(key) {cache.delete(key)}
export function matchesBookFormat(book, format, availability) {
  if (format === 'all') return true
  const source = resolveBookSource(book)
  const isSupplement = ['notes', 'sample'].includes(source.contentRole)
  if (format === 'notes') return isSupplement
  if (format !== 'pdf' || isSupplement) return false
  const kind = availability?.status === 'ready' ? availability.kind : source.kind
  return kind === 'pdf'
}
function bookPriority(book) {
  const source = resolveBookSource(book)
  if (source.contentRole === 'sample') return 5
  if (source.contentRole === 'notes') return 4
  if (source.kind === 'pdf') return source.isLocalAsset ? 0 : 1
  return source.kind === 'archive' ? 2 : 3
}
export function mergeBookCatalog(books) {
  const seen=new Set()
  return books.filter(Boolean).filter(book=>{
    const key=bookSourceKey(book)
    if (seen.has(key)) return false
    seen.add(key);return true
  }).sort((a,b)=>bookPriority(a)-bookPriority(b))
}
function signalWithTimeout(signal,ms) {
  return signal ? AbortSignal.any([signal,AbortSignal.timeout(ms)]) : AbortSignal.timeout(ms)
}
async function prefixOf(response,limit=4096) {
  const reader=response.body?.getReader()
  if (!reader) return new Uint8Array()
  const parts=[];let total=0
  try {
    while(total<limit) {
      const {done,value}=await reader.read();if(done)break
      const part=value.subarray(0,limit-total);parts.push(part);total+=part.length
    }
  } finally {await reader.cancel()}
  const bytes=new Uint8Array(total);let offset=0
  for(const part of parts){bytes.set(part,offset);offset+=part.length}
  return bytes
}
function httpFailure(status) {
  if(status===404 || status===410) return {status:'missing',message:'Tài liệu không còn tồn tại tại liên kết này.'}
  if([401,403,451].includes(status))return {status:'restricted',message:'Nguồn đang hạn chế truy cập. Vui lòng xem điều kiện tại nguồn.'}
  return {status:'unavailable',message:'Chưa kết nối được tài liệu. Bạn có thể thử lại sau.'}
}
export function validateBookPrefix(bytes,kind,contentType='') {
  const text=new TextDecoder().decode(bytes)
  if(kind==='pdf') return text.trimStart().startsWith('%PDF-')
  if(/<div[^>]+id=["']root["']/i.test(text))return false
  if(kind==='html') return /(?:text\/html|application\/xhtml\+xml)/i.test(contentType) && /<(?:!doctype|html|head|body)/i.test(text)
  if(kind==='text')return /text\/plain/i.test(contentType) && !/^\s*<(?:!doctype|html)/i.test(text)
  return false
}
export async function checkBookSource(book,{signal,force=false,fetchImpl=fetch}={}) {
  const source=resolveBookSource(book), key=bookSourceKey(book)
  if(!source.isPrivate && !force && cachedBookCheck(key))return cachedBookCheck(key)
  let result
  try {
    if(!source.sourceUrl)result={status:'missing',message:'Chưa có liên kết tài liệu gốc.'}
    else if(!source.canCheck)result={status:'external',message:'Tài liệu này được đọc hoặc tải tại website nguồn.'}
    else if(source.isLocalAsset || source.isPrivate) {
      const request=source.isPrivate ? authenticatedFetch : fetchImpl
      const response=await request(source.sourceUrl,{headers:{Range:'bytes=0-4095'},signal:signalWithTimeout(signal,15000),cache:'no-cache'})
      if(!response.ok)result=httpFailure(response.status)
      else {
        const rawSize=response.headers.get('content-range')?.split('/').at(-1) || response.headers.get('content-length')
        const bytes=await prefixOf(response)
        result=Number(rawSize)>MAX_BOOK_BYTES ? {status:'too_large',message:'Tài liệu vượt giới hạn 40 MB. Vui lòng mở tại nguồn.'}
          :validateBookPrefix(bytes,source.kind,response.headers.get('content-type') || '')
            ?{status:'ready',kind:source.kind,viewUrl:source.viewUrl,sourceUrl:source.sourceUrl}
            :{status:'invalid',message:'Liên kết chưa trả về đúng nội dung tài liệu.'}
      }
    } else {
      const response=await fetchImpl(`/api/v1/public/learning/reader/check?url=${encodeURIComponent(source.sourceUrl)}`,{signal:signalWithTimeout(signal,30000)})
      if(!response.ok)result=httpFailure(response.status)
      else {
        const payload=await response.json()
        const validReady=payload.status!=='ready' || (['pdf','html','text'].includes(payload.kind) && payload.view_url?.startsWith('/api/v1/public/learning/reader/stream?url='))
        result=BOOK_STATUS_LABELS[payload.status] && validReady ? {...payload,viewUrl:payload.view_url,sourceUrl:payload.resolved_url || source.sourceUrl} : {status:'invalid',message:'Nguồn trả về thông tin chưa hợp lệ.'}
      }
    }
  } catch(error) {
    if(signal?.aborted)throw error
    result={status:'unavailable',message:'Chưa kết nối được nguồn. Bạn vẫn có thể sử dụng sổ ghi chú.'}
  }
  result={...source,...result,openUrl:source.openUrl,checked_at:result.checked_at || new Date().toISOString()}
  if(!source.isPrivate)cache.set(key,{result,expires:Date.now()+(result.status==='ready'?300000:60000)})
  if(cache.size>500)cache.delete(cache.keys().next().value)
  return result
}
export function rememberBookLoadFailure(source,error) {
  const key=bookSourceKey({url:source.openUrl || source.sourceUrl})
  const failure=Number.isInteger(error.status) ? httpFailure(error.status) : {status:'load_failed',message:error.message}
  const result={...source,...failure,checked_at:new Date().toISOString()}
  cache.set(key,{result,expires:Date.now()+60000})
}
export async function loadBookDocument(source,{signal,fetchImpl=fetch}={}) {
  const request=isPrivateLibraryUrl(source.viewUrl) ? authenticatedFetch : fetchImpl
  const response=await request(source.viewUrl,{signal:signalWithTimeout(signal,90000)})
  if(!response.ok)throw Object.assign(new Error(httpFailure(response.status).message),{status:response.status})
  const size=Number(response.headers.get('content-length'))
  if(size>MAX_BOOK_BYTES)throw new Error('Tài liệu vượt giới hạn 40 MB. Vui lòng mở tại nguồn.')
  const reader=response.body?.getReader()
  if(!reader)throw new Error('Nguồn chưa trả về nội dung tài liệu.')
  const parts=[];let total=0
  try {
    while(true) {
      const {done,value}=await reader.read();if(done)break
      total+=value.length
      if(total>MAX_BOOK_BYTES)throw new Error('Tài liệu vượt giới hạn 40 MB. Vui lòng mở tại nguồn.')
      parts.push(value)
    }
  } finally {await reader.cancel()}
  const blob=new Blob(parts,{type:source.kind==='pdf'?'application/pdf':source.kind==='html'?'text/html':'text/plain'})
  if(!validateBookPrefix(new Uint8Array(await blob.slice(0,4096).arrayBuffer()),source.kind,response.headers.get('content-type') || ''))throw new Error('Nguồn chưa trả về đúng nội dung tài liệu. Hãy thử lại hoặc mở tài liệu tại nguồn.')
  if(source.kind==='pdf') {
    if(!(await blob.slice(-2048).text()).includes('%%EOF'))throw new Error('File PDF tải về chưa đầy đủ hoặc bị hỏng. Vui lòng thử lại.')
    return {blob}
  }
  return {text:await blob.text()}
}
