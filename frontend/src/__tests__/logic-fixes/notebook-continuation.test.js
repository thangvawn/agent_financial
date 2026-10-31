import test from 'node:test'
import assert from 'node:assert/strict'
import * as model from '../../features/learn-hub/pages/bookReaderModel.js'

test('long notes paginate without losing whitespace or Vietnamese/emoji text',()=>{
  assert.equal(typeof model.paginateNotebookText,'function')
  const text='Kinh tế 🌱\n\nCơ hội và lựa chọn.  Dòng cuối\n'
  const chunks=model.paginateNotebookText(text,value=>Array.from(value).length<=16)
  assert.ok(chunks.length>1)
  assert.equal(chunks.join(''),text)
  assert.ok(chunks.every(value=>Array.from(value).length<=16))
  assert.ok(chunks.every(value=>!/[\uD800-\uDBFF]$|^[\uDC00-\uDFFF]/u.test(value)))
})
test('short text stays intact and an unmeasurable paper cannot loop or drop text',()=>{
  assert.equal(typeof model.paginateNotebookText,'function')
  assert.deepEqual(model.paginateNotebookText('ngắn',()=>true),['ngắn'])
  assert.deepEqual(model.paginateNotebookText('giữ nguyên',()=>false),['giữ nguyên'])
})
test('overflow inserts pages without overwriting later notes, ink or images',()=>{
  assert.equal(typeof model.continueNotebookText,'function')
  const first=model.createNotebookPage({id:'first',noteText:'old',drawingDataUrl:'data:image/png;base64,ink'})
  const later=model.createNotebookPage({id:'later',noteText:'Không ghi đè',images:['data:image/png;base64,img']})
  const original=[first,later]
  const result=model.continueNotebookText(original,'first',['mới\n','tiếp'])
  assert.equal(result.pages.length,3)
  assert.equal(result.pages[0].drawingDataUrl,first.drawingDataUrl)
  assert.equal(result.pages[1].noteText,'tiếp')
  assert.strictEqual(result.pages[2],later)
  assert.equal(original[0].noteText,'old')
  assert.equal(result.pageIds[1],result.pages[1].id)
})
test('overflow reuses an empty continuation page but preserves pages containing ink',()=>{
  assert.equal(typeof model.continueNotebookText,'function')
  const first=model.createNotebookPage({id:'one'})
  const empty=model.createNotebookPage({id:'blank',title:'Ý tưởng tiếp theo'})
  const ink=model.createNotebookPage({id:'ink',drawingDataUrl:'data:image/png;base64,ink'})
  const result=model.continueNotebookText([first,empty,ink],'one',['A','B','C'])
  assert.equal(result.pages.length,4)
  assert.equal(result.pages[1].id,'blank')
  assert.equal(result.pages[1].title,'Ý tưởng tiếp theo')
  assert.equal(result.pages[2].noteText,'C')
  assert.strictEqual(result.pages[3],ink)
})
test('caret maps to the continued page using UTF-16 textarea offsets',()=>{
  assert.equal(typeof model.locateNotebookCaret,'function')
  assert.deepEqual(model.locateNotebookCaret(['ab🌱','cde'],6),{index:1,offset:2})
  assert.deepEqual(model.locateNotebookCaret(['ab🌱','cde'],4),{index:1,offset:0})
  assert.deepEqual(model.locateNotebookCaret(['ab🌱','cde'],1),{index:0,offset:1})
})
