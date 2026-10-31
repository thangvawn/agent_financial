import test from 'node:test'
import assert from 'node:assert/strict'
import {resolveBookSource, toReadableBook} from '../../features/learn-hub/pages/bookSource.js'
import {normalizeDbBook} from '../../features/learn-hub/content/courseCatalogData.js'

test('catalog preserves real HTML/EPUB types instead of inventing PDF metadata',()=>{
 const html=normalizeDbBook({book_id:'web',title:'Open textbook',url:'https://www.gutenberg.org/ebooks/123',download_url:'https://www.gutenberg.org/files/123/123-h.htm'})
 assert.equal(toReadableBook(html).source.kind,'html')
 assert.equal(html.pdf_url,'')
 const epub=normalizeDbBook({book_id:'epub',download_url:'https://www.gutenberg.org/ebooks/123.epub3.images'})
 assert.notEqual(toReadableBook(epub).source.kind,'pdf')
})
test('Archive entries resolve the item instead of assuming identifier.pdf exists',()=>{
 const source=resolveBookSource({url:'https://archive.org/details/known-book',download_url:'https://archive.org/download/known-book/known-book.pdf'})
 assert.equal(source.kind,'archive')
 assert.equal(source.openUrl,'https://archive.org/details/known-book')
 assert.equal(source.sourceUrl,'https://archive.org/details/known-book')
})
test('reader rejects unsafe schemes and protocol-relative or arbitrary local routes',()=>{
 for(const url of ['javascript:alert(1)','data:text/html,bad','//evil.test/book.pdf','/api/admin/export','https://archive.org.evil.test/book.pdf']) {
  const source=resolveBookSource({url})
  assert.equal(source.viewUrl,'',url)
 }
})
test('a filename hint cannot override the actual selected URL extension',()=>{
 const source=resolveBookSource({url:'https://www.gutenberg.org/ebooks/123',download_url:'https://www.gutenberg.org/files/123/123-h.htm',file_name:'mistaken.pdf'})
 assert.equal(source.kind,'html')
})
test('local study notes are distinguished from full books',()=>{
 const source=resolveBookSource({url:'/learning-assets/books/psychology-of-money-notes.html'})
 assert.equal(source.contentRole,'notes')
 assert.equal(source.kind,'html')
})
