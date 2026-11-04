const PROXY_HOSTS = ['archive.org','gutenberg.org','arxiv.org','openlibrary.org','wikipedia.org','wikimedia.org','cloudfront.net','gutenberg.net.au']
export const isPrivateLibraryUrl = value => typeof value === 'string' && /^\/api\/v1\/public\/learning\/library\/items\/[a-f0-9]{32}\/file\.pdf$/.test(value)
export function safeBookUrl(value) {
  if (typeof value !== 'string' || !value.trim() || value.trim().startsWith('//')) return ''
  try {
    const raw=value.trim(), url=new URL(raw,'https://northstar.local')
    if (url.username || url.password || !['http:','https:'].includes(url.protocol)) return ''
    if (isPrivateLibraryUrl(raw)) return raw
    if (raw.startsWith('/')) return url.pathname.startsWith('/learning-assets/books/') && !decodeURIComponent(url.pathname).includes('..') ? url.pathname+url.search : ''
    return url.href
  } catch {return ''}
}
function typeOfUrl(url) {
  const parsed=new URL(url,'https://northstar.local')
  const path=parsed.pathname.toLowerCase()
  if (['arxiv.org','www.arxiv.org','export.arxiv.org'].includes(parsed.hostname) && path.startsWith('/pdf/')) return 'pdf'
  if (/\.pdf$/.test(path)) return 'pdf'
  if (/\.html?(?:$|\.)/.test(path)) return 'html'
  if (/\.txt$/.test(path)) return 'text'
  if (/\.epub(?:\d|\.|$)/.test(path)) return 'epub'
  return 'link'
}
export function resolveBookSource(book = {}) {
  const candidates=[book.pdf_url,book.download_url,book.url].map(safeBookUrl).filter(Boolean)
  const primary=candidates.find(url=>['pdf','html','text'].includes(typeOfUrl(url))) || candidates[0] || ''
  if (!primary) return {kind:'link',sourceUrl:'',viewUrl:'',openUrl:'',contentRole:'reference',isRemote:false,isLocalAsset:false}
  const parsed=new URL(primary,'https://northstar.local')
  const isPrivate=isPrivateLibraryUrl(primary)
  const isLocalAsset=primary.startsWith('/learning-assets/books/')
  const allowed=isPrivate || isLocalAsset || PROXY_HOSTS.some(host=>parsed.hostname===host || parsed.hostname.endsWith(`.${host}`))
  const archiveMatch=['archive.org','www.archive.org'].includes(parsed.hostname) && parsed.pathname.match(/^\/(?:details|download|embed)\/([a-zA-Z0-9_.-]+)(?:\/|$)/)
  const archiveId=archiveMatch ? archiveMatch[1] : null
  const sourceUrl=archiveId ? `https://archive.org/details/${archiveId}` : primary
  const kind=archiveId ? 'archive' : typeOfUrl(primary)
  const contentRole=book.content_role || (/-notes\.(?:html?|txt|pdf)$/i.test(parsed.pathname) ? 'notes' : /sample-reader/.test(parsed.pathname) ? 'sample' : 'fulltext')
  const viewUrl=allowed && ['pdf','html','text'].includes(kind) ? (isLocalAsset || isPrivate ? sourceUrl : `/api/v1/public/learning/reader/stream?url=${encodeURIComponent(sourceUrl)}`) : ''
  return {kind,sourceUrl,archiveId,contentRole,viewUrl,openUrl:isPrivate?'':sourceUrl,isRemote:!isLocalAsset && !isPrivate,isLocalAsset,isPrivate,canCheck:allowed && ['archive','pdf','html','text'].includes(kind)}
}
export function toReadableBook(item = {}) {
  const source=resolveBookSource(item)
  return {...item,asset_id:item.asset_id || item.book_id || source.sourceUrl,title:item.title || 'Tài liệu',source,
    isPdf:source.kind==='pdf',isHtml:source.kind==='html',isText:source.kind==='text'}
}
