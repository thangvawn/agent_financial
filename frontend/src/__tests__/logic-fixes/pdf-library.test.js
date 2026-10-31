import test, {after} from 'node:test'
import assert from 'node:assert/strict'
import {mergeBookCatalog} from '../../features/learn-hub/services/bookAvailability.js'
import * as availability from '../../features/learn-hub/services/bookAvailability.js'
import {loadComponent,closeViteServer,React,renderToString} from '../test-helpers.js'
after(closeViteServer)
const pdf={book_id:'full',title:'Full textbook',url:'/learning-assets/books/full.pdf'}
const notes={book_id:'notes',title:'Study notes',url:'/learning-assets/books/book-notes.html'}
const sample={book_id:'sample',title:'Sample',url:'/learning-assets/books/northstar-sample-reader.pdf'}
test('the book library opens in full PDF mode',async()=>{
 const Library=await loadComponent('./src/features/learn-hub/pages/DocumentLibrary.jsx')
 const html=renderToString(React.createElement(Library))
 assert.match(html,/<option value="pdf" selected="">PDF toàn văn<\/option>/)
})
test('real books sort ahead of local notes and sample PDFs',()=>{
 const [first]=mergeBookCatalog([notes,sample,pdf])
 assert.equal(first.book_id,'full')
})
test('PDF filter excludes notes, samples, HTML and unverified Archive entries',()=>{
 assert.equal(availability.matchesBookFormat(pdf,'pdf'),true)
 assert.equal(availability.matchesBookFormat(notes,'pdf'),false)
 assert.equal(availability.matchesBookFormat(sample,'pdf'),false)
 const archive={url:'https://archive.org/details/book'}
 assert.equal(availability.matchesBookFormat(archive,'pdf'),false)
 assert.equal(availability.matchesBookFormat(archive,'pdf',{status:'ready',kind:'pdf'}),true)
 assert.equal(availability.matchesBookFormat(archive,'pdf',{status:'ready',kind:'text'}),false)
 assert.equal(availability.matchesBookFormat(notes,'notes'),true)
 assert.equal(availability.matchesBookFormat(pdf,'notes'),false)
 assert.equal(availability.matchesBookFormat(notes,'all'),true)
})
test('ready full PDF offers reading and downloading the actual PDF',async()=>{
 const Card=await loadComponent('./src/features/learn-hub/pages/BookCardItem.jsx')
 const html=renderToString(React.createElement(Card,{book:pdf,availability:{status:'ready',kind:'pdf',viewUrl:pdf.url}}))
 assert.match(html,/Đọc PDF/);assert.match(html,/Tải PDF/)
 assert.match(html,/download=/)
})
