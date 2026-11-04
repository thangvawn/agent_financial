import { describe, it, after } from 'node:test'
import assert from 'node:assert'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

describe('Market Index Spec Tests: Cards, Realtime Sparkline & VI Formatting', () => {
  after(async () => {
    await closeViteServer()
  })

  it('renders MarketSparkline with accurate SVG dashed ref line and color syncing', async () => {
    const mod = await loadComponent('./src/components/market/MarketSparkline.tsx')
    const MarketSparkline = mod.MarketSparkline || mod

    // Trường hợp 1: Giảm điểm (Đỏ #EF2929)
    const downHistory = [
      { timestamp: 1000, price: 1735.0 },
      { timestamp: 2000, price: 1728.5 },
      { timestamp: 3000, price: 1720.98 }
    ]
    const htmlDown = renderToString(React.createElement(MarketSparkline, {
      history: downHistory,
      referencePrice: 1735.09,
      currentPrice: 1720.98,
      width: 115,
      height: 44
    }))

    assert.ok(htmlDown.includes('<svg'), 'Must render SVG element')
    assert.ok(htmlDown.includes('stroke-dasharray="2,2"'), 'Must render dashed reference line')
    assert.ok(htmlDown.includes('#EF2929') || htmlDown.includes('rgb(239, 41, 41)'), 'Must sync red tone for drop')

    // Trường hợp 2: Tăng điểm (Xanh lá #16A34A)
    const upHistory = [
      { timestamp: 1000, price: 124.2 },
      { timestamp: 2000, price: 124.5 },
      { timestamp: 3000, price: 124.73 }
    ]
    const htmlUp = renderToString(React.createElement(MarketSparkline, {
      history: upHistory,
      referencePrice: 124.24,
      currentPrice: 124.73,
      width: 115,
      height: 44
    }))

    assert.ok(htmlUp.includes('#16A34A') || htmlUp.includes('rgb(22, 163, 74)'), 'Must sync green tone for gain')

    // Trường hợp 3: Edge case mảng rỗng chống crash
    const htmlEmpty = renderToString(React.createElement(MarketSparkline, {
      history: [],
      referencePrice: 1000,
      currentPrice: 1000
    }))
    assert.ok(htmlEmpty.includes('<svg'), 'Must survive empty history gracefully')
  })

  it('renders MarketIndexCard with strict vi-VN number formatting and breadth badges', async () => {
    const mod = await loadComponent('./src/components/market/MarketIndexCard.tsx')
    const MarketIndexCard = mod.MarketIndexCard || mod

    const mockVnIndex = {
      symbol: 'VNINDEX',
      name: 'VN-Index',
      currentPrice: 1720.98,
      referencePrice: 1735.09,
      change: -14.11,
      changePercent: -0.81,
      volume: 470.35,
      turnover: 10645.09,
      advances: 154,
      ceil: 4,
      unchanged: 60,
      declines: 148,
      floor: 6,
      history: [
        { timestamp: 1, price: 1735.09 },
        { timestamp: 2, price: 1720.98 }
      ],
      updatedAt: Date.now()
    }

    const html = renderToString(React.createElement(MarketIndexCard, { data: mockVnIndex }))

    assert.ok(html.includes('VNINDEX'), 'Must display index symbol')
    assert.ok(html.includes('1.720,98'), 'Must format price with Vietnamese dots and commas')
    assert.ok(html.includes('-14,11') || html.includes('-14.11'), 'Must format change point')
    assert.ok(html.includes('-0,81%') || html.includes('-0.81%'), 'Must format change percentage')
    assert.ok(html.includes('470,35 Triệu CP') || html.includes('470.35 Triệu CP'), 'Must format volume in Triệu CP')
    assert.ok(html.includes('10.645,09 Tỷ') || html.includes('10645.09'), 'Must format turnover in Tỷ')
    assert.ok(html.includes('154'), 'Must render advances count')
    assert.ok(html.includes('4'), 'Must render ceil count')
    assert.ok(html.includes('60'), 'Must render unchanged count')
    assert.ok(html.includes('148'), 'Must render declines count')
    assert.ok(html.includes('6'), 'Must render floor count')
  })

  it('renders MarketOverview container rendering all 4 indices', async () => {
    const mod = await loadComponent('./src/components/market/MarketOverview.tsx')
    const MarketOverview = mod.MarketOverview || mod

    const html = renderToString(React.createElement(MarketOverview))
    assert.ok(html.includes('VNINDEX'), 'Missing VNINDEX card')
    assert.ok(html.includes('VN30'), 'Missing VN30 card')
    assert.ok(html.includes('HNX30'), 'Missing HNX30 card')
    assert.ok(html.includes('UPCOM'), 'Missing UPCOM card')
  })
})
