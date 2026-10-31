import test, {after} from 'node:test'
import assert from 'node:assert/strict'
import {loadComponent,closeViteServer,React,renderToString} from '../test-helpers.js'
after(closeViteServer)
test('PDF pane does not trust an iframe load as proof of a valid document',async()=>{
 const {PdfBookPane}=await loadComponent('./src/features/learn-hub/pages/PdfBookPane.jsx')
 const html=renderToString(React.createElement(PdfBookPane,{source:{sourceUrl:'/learning-assets/books/missing.pdf',viewUrl:'/learning-assets/books/missing.pdf',isLocalAsset:true},title:'Missing'}))
 assert.ok(!html.includes('<iframe'),'Fetch and validate the response before creating a PDF iframe')
})
test('study-note HTML is not advertised as the original full book',async()=>{
 const {BookDocumentPane}=await loadComponent('./src/features/learn-hub/pages/BookDocumentPane.jsx')
 const html=renderToString(React.createElement(BookDocumentPane,{book:{book_id:'notes',title:'Study notes',url:'/learning-assets/books/psychology-of-money-notes.html'}}))
 assert.ok(!html.includes('Nguyên bản'))
 assert.ok(!html.includes('Toàn văn'))
})
test('study notes never link unsafe source schemes',async()=>{
 const {BookStudyNotes}=await loadComponent('./src/features/learn-hub/pages/BookStudyNotes.jsx')
 const html=renderToString(React.createElement(BookStudyNotes,{book:{title:'Unsafe',url:'javascript:alert(1)'},notes:{}}))
 assert.ok(!html.includes('<a '))
})
