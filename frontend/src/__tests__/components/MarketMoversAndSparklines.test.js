import { describe, it, after } from 'node:test'
import assert from 'node:assert'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

describe('Market index cards and sparklines', () => {
  after(async () => {
    await closeViteServer()
  })

  it('renders IndexSparklineCard with exact numbers, breadth colors and SVG sparkline', async () => {
    const mod = await loadComponent('./src/features/market-portfolio/components/IndexSparklineCard.jsx')
    const IndexSparklineCard = mod.IndexSparklineCard || mod

    const mockItem = {
      symbol: 'VNINDEX',
      price: 1720.98,
      change: -14.11,
      change_pct: -0.81,
      turnover_billion: 10645.09,
      volume_million: 470.35,
      breadth: { up: 154, ceil: 4, flat: 60, down: 148, floor: 6 },
      history: [{ date: '2026-10-01', close: 1735 }, { date: '2026-10-02', close: 1720.98 }]
    }

    const html = renderToString(React.createElement(IndexSparklineCard, { item: mockItem }))
    assert.ok(html.includes('VNINDEX'), 'Must render index symbol')
    assert.ok(html.includes('-0,81'), 'Must render change percentage')
    assert.ok(html.includes('1.720,98'), 'Must render formatted price')
    assert.ok(html.includes('-14,11'), 'Must render point change')
    assert.ok(html.replaceAll('<!-- -->', '').includes('470,35 Triệu CP'), 'Must render volume')
    assert.ok(html.replaceAll('<!-- -->', '').includes('10.645,09 Tỷ'), 'Must render turnover')
    assert.ok(html.includes('154'), 'Must render up breadth')
    assert.ok(html.includes('(<!-- -->4<!-- -->)'), 'Must render ceil count in purple')
    assert.ok(html.includes('60'), 'Must render flat count in yellow')
    assert.ok(html.includes('148'), 'Must render down count in red')
    assert.ok(html.includes('(<!-- -->6<!-- -->)'), 'Must render floor count in cyan')
    assert.ok(html.includes('<svg'), 'Must render pure SVG sparkline')
    assert.ok(html.includes('price-sparkline__reference'), 'Must render the period reference')
  })

  it('renders IndexCardsBar with 4 distinct index cards', async () => {
    const mod = await loadComponent('./src/features/market-portfolio/components/IndexCardsBar.jsx')
    const IndexCardsBar = mod.IndexCardsBar || mod

    const html = renderToString(React.createElement(IndexCardsBar, {
      indexItems: [
        { symbol: 'VNINDEX', price: 1720.98, change: -14.11, change_pct: -0.81 },
        { symbol: 'VN30', price: 1859.79, change: -13.20, change_pct: -0.71 },
        { symbol: 'HNX30', price: 272.31, change: 1.05, change_pct: 0.39 },
        { symbol: 'UPCOM', price: 124.53, change: 0.12, change_pct: 0.10 }
      ]
    }))

    assert.ok(html.includes('VNINDEX'), 'Missing VNINDEX card')
    assert.ok(html.includes('VN30'), 'Missing VN30 card')
    assert.ok(html.includes('HNX30'), 'Missing HNX30 card')
    assert.ok(html.includes('UPCOM'), 'Missing UPCOM card')
  })

})
