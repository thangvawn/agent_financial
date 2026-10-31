import test, {after} from 'node:test'
import assert from 'node:assert/strict'
import {loadComponent, closeViteServer, React, renderToString} from '../test-helpers.js'
import {safeBookUrl, resolveBookSource} from '../../features/learn-hub/pages/bookSource.js'
import {catalogDocument,filterShelf,shelfBook,validateUpload} from '../../features/learn-hub/services/personalLibraryApi.js'

after(closeViteServer)
const privateUrl='/api/v1/public/learning/library/items/0123456789abcdef0123456789abcdef/file.pdf'
test('library exposes local PDF upload',async()=>{
  const Library=await loadComponent('./src/features/learn-hub/pages/DocumentLibrary.jsx')
  assert.match(renderToString(React.createElement(Library)),/Thêm tài liệu/)
})
test('Learn Hub has a dedicated personal shelf',async()=>{
  const Controls=await loadComponent('./src/features/learn-hub/pages/LearningTopControls.jsx')
  assert.match(renderToString(React.createElement(Controls,{search:''})),/Kệ sách của tôi/)
})
test('only exact private PDF endpoint is accepted and it is never an unauthenticated source link',()=>{
  assert.equal(safeBookUrl(privateUrl),privateUrl)
  const source=resolveBookSource({url:privateUrl})
  assert.equal(source.kind,'pdf')
  assert.equal(source.isPrivate,true)
  assert.equal(source.openUrl,'')
  assert.equal(source.viewUrl,privateUrl)
  for(const url of ['/api/v1/public/auth/me','/api/v1/public/learning/library/items/../file.pdf',privateUrl+'?session_id=secret']) assert.equal(safeBookUrl(url),'')
})
test('arxiv full-text PDFs without extension open in the reader',()=>{
  const source=resolveBookSource({pdf_url:'https://arxiv.org/pdf/2401.12345'})
  assert.equal(source.kind,'pdf')
  assert.equal(source.canCheck,true)
})
test('personal shelf filters statuses, kinds, titles and orders recently opened items',()=>{
  const rows=[{id:'a',title:'Tài chính',author:'An',kind:'book',status:'completed',read_count:2,last_opened_at:'2026-10-29'},
    {id:'b',title:'Paper',author:'Bình',kind:'paper',status:'reading',read_count:1,last_opened_at:'2026-10-31'},
    {id:'c',title:'New',author:'',kind:'document',status:'want_to_read',read_count:0,last_opened_at:null}]
  assert.deepEqual(filterShelf(rows,{status:'history'}).map(row=>row.id),['b','a'])
  assert.deepEqual(filterShelf(rows,{status:'completed',kind:'book',search:' TÀI CHÍNH '}).map(row=>row.id),['a'])
  assert.deepEqual(filterShelf(rows,{kind:'paper'}).map(row=>row.id),['b'])
  assert.equal(filterShelf(rows,{search:'missing'}).length,0)
  assert.equal(filterShelf(rows).length,3)
})
test('uploaded documents and catalog snapshots retain identity and reading position',()=>{
  const snapshot=catalogDocument({book_id:'original',title:'Book',pages:50,url:'/learning-assets/books/book.pdf'})
  assert.equal(snapshot.source_id,'original')
  assert.equal(snapshot.page_count,50)
  const item={id:'private',title:'Own',file_url:privateUrl,kind:'paper',current_page:3,page_count:8}
  assert.equal(shelfBook(item).url,privateUrl)
  assert.equal(shelfBook(item).libraryItem.current_page,3)
  assert.throws(()=>catalogDocument({url:privateUrl}))
  assert.throws(()=>catalogDocument({url:'javascript:alert(1)'}))
  assert.equal(catalogDocument({pdf_url:'https://arxiv.org/pdf/1234.56789',type:'paper',pages:'N/A'}).kind,'paper')
})
test('upload validation explains unsupported, empty and oversized files',()=>{
  assert.match(validateUpload(null),/Chọn/)
  assert.match(validateUpload({name:'book.docx',size:10}),/PDF/)
  assert.match(validateUpload({name:'book.pdf',size:0}),/trống/)
  assert.match(validateUpload({name:'book.pdf',size:40*1024*1024+1}),/40 MB/)
  assert.equal(validateUpload({name:'PAPER.PDF',size:40*1024*1024}),'')
})
