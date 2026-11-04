import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'
after(closeViteServer)
test('foreign flow preserves net direction and never invents missing data', async () => {
 const {ForeignFlowButterfly} = await loadComponent('./src/features/market-portfolio/components/ForeignFlowButterfly.jsx')
 const render = items => renderToString(React.createElement(ForeignFlowButterfly,{items}))
 const html = render([{symbol:'AAA',foreign_net_val_billion:5},{symbol:'BBB',foreign_net_val_billion:-3}])
 const wings = html.split('sell-wing')
 assert.ok(wings[0].includes('AAA'))
 assert.ok(!wings[0].includes('BBB'))
 assert.ok(wings[1].includes('BBB'))
 assert.ok(!wings[1].includes('AAA'))
 const empty = render([])
 assert.ok(!empty.includes('184.5'))
 assert.ok(empty.includes('Chưa có dữ liệu'))
})
