import test,{after} from 'node:test'
import assert from 'node:assert/strict'
import {loadComponent,closeViteServer,React,renderToString} from '../test-helpers.js'
after(closeViteServer)

test('reader exposes simultaneous reading and writing as a selected layout',async()=>{
  const {ReaderPanelSwitch}=await loadComponent('./src/features/learn-hub/pages/ReaderChrome.jsx')
  const html=renderToString(React.createElement(ReaderPanelSwitch,{panel:'split',onChange:()=>{}}))
  assert.match(html,/aria-selected="true"[^>]*>.*?Song song/s)
  assert.match(html,/Song song/)
})
test('depth effect can be explicitly switched off through an accessible toggle',async()=>{
  const {ReaderTopBar}=await loadComponent('./src/features/learn-hub/pages/ReaderChrome.jsx')
  const html=renderToString(React.createElement(ReaderTopBar,{title:'Book',depthEnabled:true,onToggleDepth:()=>{}}))
  assert.match(html,/aria-pressed="true"/)
  assert.match(html,/Hiệu ứng 3D/)
})
test('splitter reports its current, minimum and maximum position to keyboard users',async()=>{
  const previous=globalThis.window
  globalThis.window={localStorage:{getItem:()=> '60'}}
  try {
    const {ReaderSplitPane}=await loadComponent('./src/features/learn-hub/pages/ReaderSplitPane.jsx')
    const html=renderToString(React.createElement(ReaderSplitPane,{panel:'split',book:'PDF',notes:'Notes'}))
    assert.match(html,/aria-valuenow="60"/)
    assert.match(html,/aria-valuemin=/)
    assert.match(html,/aria-valuemax=/)
  }finally{if(previous===undefined)delete globalThis.window;else globalThis.window=previous}
})
test('drawing toolbar announces which tool is active',async()=>{
  const {NoteToolbar}=await loadComponent('./src/features/learn-hub/pages/ReaderChrome.jsx')
  const html=renderToString(React.createElement(NoteToolbar,{editorMode:'draw',drawColor:'#123456',drawSize:2}))
  assert.match(html,/aria-pressed="true"[^>]*>.*?Vẽ/s)
})
