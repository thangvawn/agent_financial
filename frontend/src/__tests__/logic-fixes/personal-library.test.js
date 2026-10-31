import test, {after} from 'node:test'
import assert from 'node:assert/strict'
import {loadComponent, closeViteServer, React, renderToString} from '../test-helpers.js'
import {safeBookUrl, resolveBookSource} from '../../features/learn-hub/pages/bookSource.js'

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
