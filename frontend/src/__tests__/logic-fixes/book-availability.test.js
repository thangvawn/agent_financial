import test from 'node:test'
import assert from 'node:assert/strict'
import {checkBookSource,loadBookDocument,mergeBookCatalog,MAX_BOOK_BYTES,clearBookCheck,bookSourceKey} from '../../features/learn-hub/services/bookAvailability.js'
const local=name=>({url:`/learning-assets/books/${name}`})
const pdf='%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF'
const reply=(body,status=200,type='application/pdf')=>async()=>new Response(body,{status,headers:{'content-type':type}})
for(const [status,expected] of [[404,'missing'],[410,'missing'],[403,'restricted'],[503,'unavailable']])test(`Local source HTTP ${status} is ${expected}`,async()=>{
 assert.equal((await checkBookSource(local(`${status}.pdf`),{fetchImpl:reply('',status)})).status,expected)
})
test('checks signatures, rejects SPA fallback, labels HTML notes accurately',async()=>{
 assert.equal((await checkBookSource(local('valid.pdf'),{fetchImpl:reply(pdf)})).status,'ready')
 assert.equal((await checkBookSource(local('spa.pdf'),{fetchImpl:reply('<html><div id="root"></div></html>',200,'text/html')})).status,'invalid')
 const html=await checkBookSource(local('sample-notes.html'),{fetchImpl:reply('<!doctype html><html>Notes</html>',200,'text/html')})
 assert.equal(html.status,'ready');assert.equal(html.contentRole,'notes')
 assert.equal((await checkBookSource(local('spa.html'),{fetchImpl:reply('<html><div id="root"></div></html>',200,'text/html')})).status,'invalid')
})
test('caches checks and explicit retry refreshes a repaired source',async()=>{
 const book=local('repair.pdf');let calls=0
 const fetchImpl=async()=>{calls++;return new Response(calls===1?'':pdf,{status:calls===1?404:200})}
 assert.equal((await checkBookSource(book,{fetchImpl})).status,'missing')
 assert.equal((await checkBookSource(book,{fetchImpl})).status,'missing');assert.equal(calls,1)
 assert.equal((await checkBookSource(book,{fetchImpl,force:true})).status,'ready');assert.equal(calls,2)
 clearBookCheck(bookSourceKey(book))
 assert.equal((await checkBookSource(book,{fetchImpl})).status,'ready');assert.equal(calls,3)
})
test('source catalog deduplicates Archive aliases and prioritizes local books',()=>{
 const list=mergeBookCatalog([{book_id:'a',url:'https://archive.org/details/test'},{book_id:'b',download_url:'https://archive.org/download/test/test.pdf'},local('a.pdf')])
 assert.equal(list.length,2);assert.equal(list[0].url,'/learning-assets/books/a.pdf')
})
test('remote check preserves restricted state and rejects invalid ready payload',async()=>{
 const book={url:'https://archive.org/details/qa'}
 const call=payload=>checkBookSource(book,{force:true,fetchImpl:reply(JSON.stringify(payload),200,'application/json')})
 assert.equal((await call({status:'restricted'})).status,'restricted')
 assert.equal((await call({status:'ready',kind:'pdf',view_url:'https://evil.test/a.pdf'})).status,'invalid')
 const good=await call({status:'ready',kind:'pdf',view_url:'/api/v1/public/learning/reader/stream?url=https%3A%2F%2Farchive.org%2Fa.pdf'})
 assert.equal(good.status,'ready');assert.equal(good.openUrl,'https://archive.org/details/qa')
 assert.equal((await checkBookSource({url:'https://external.test/book.pdf'})).status,'external')
 assert.equal((await checkBookSource({book_id:'empty'})).status,'missing')
})
test('network failures are retryable and cancellation is not cached',async()=>{
 const book=local('abort.pdf'),controller=new AbortController();controller.abort()
 await assert.rejects(checkBookSource(book,{signal:controller.signal,fetchImpl:async()=>{throw new Error('aborted')}}))
 assert.equal((await checkBookSource(book,{fetchImpl:async()=>{throw new Error('network')}})).status,'unavailable')
})
test('reader validates complete file before presenting it',async()=>{
 const source={kind:'pdf',viewUrl:'/test.pdf'}
 assert.equal(await (await loadBookDocument(source,{fetchImpl:reply(pdf)})).blob.text(),pdf)
 await assert.rejects(loadBookDocument(source,{fetchImpl:reply('%PDF-1.4\ntruncated')}),/đầy đủ/)
 await assert.rejects(loadBookDocument(source,{fetchImpl:reply('<html>404</html>')}),/đúng nội dung/)
 await assert.rejects(loadBookDocument(source,{fetchImpl:reply('',404)}),/không còn tồn tại/)
 assert.equal((await loadBookDocument({kind:'html',viewUrl:'/notes.html'},{fetchImpl:reply('<html>Notes</html>',200,'text/html')})).text,'<html>Notes</html>')
 assert.equal((await loadBookDocument({kind:'text',viewUrl:'/notes.txt'},{fetchImpl:reply('Book text',200,'text/plain')})).text,'Book text')
})
test('rejects oversized source before reading entire body',async()=>{
 const fetchImpl=async()=>new Response(pdf,{headers:{'content-type':'application/pdf','content-length':String(MAX_BOOK_BYTES+1)}})
 assert.equal((await checkBookSource(local('huge.pdf'),{fetchImpl})).status,'too_large')
 await assert.rejects(loadBookDocument({kind:'pdf',viewUrl:'/huge.pdf'},{fetchImpl}),/40 MB/)
})
test('failed full download updates the catalog cache instead of retaining ready',async()=>{
 const service=await import('../../features/learn-hub/services/bookAvailability.js')
 const book=local('late-deleted.pdf')
 const source=await checkBookSource(book,{fetchImpl:reply(pdf)})
 assert.equal(source.status,'ready')
 service.rememberBookLoadFailure(source,Object.assign(new Error('Deleted'),{status:404}))
 assert.equal((await checkBookSource(book,{fetchImpl:reply(pdf)})).status,'missing')
})
