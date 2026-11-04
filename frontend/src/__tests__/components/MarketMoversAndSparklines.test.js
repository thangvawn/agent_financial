import { describe, it, after } from 'node:test'
import assert from 'node:assert'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

describe('Financial Subagents: Market Movers & 4 Index Sparklines Tests', () => {
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

  it('renders StudentStockFilterBar with 1-click Preset Packs and Dropdowns', async () => {
    const mod = await loadComponent('./src/features/market-portfolio/components/StudentStockFilterBar.jsx')
    const StudentStockFilterBar = mod.StudentStockFilterBar || mod

    const html = renderToString(React.createElement(StudentStockFilterBar, {
      activePreset: 'breakout',
      selectedSector: 'Ngân hàng',
      selectedExchange: 'HOSE',
      matchCount: 15
    }))

    assert.ok(html.includes('Bộ Lọc Sinh Viên'), 'Must render Student Screener title')
    assert.ok(html.includes('Breakout có xác nhận'), 'Must render Breakout preset')
    assert.ok(html.includes('Giá tăng quá xa nền'), 'Must render Overbought warning preset')
    assert.ok(html.includes('Cổ tức cao'), 'Must render High Dividend preset')
    assert.ok(html.includes('Tìm thấy'), 'Must render match counter title')
    assert.ok(html.includes('15'), 'Must render match counter count')
    assert.ok(html.includes('Đặt lại'), 'Must render Reset button when filtered')
  })

  it('renders ForeignFlowButterfly with symmetric Buy/Sell wings', async () => {
    const mod = await loadComponent('./src/features/market-portfolio/components/ForeignFlowButterfly.jsx')
    const ForeignFlowButterfly = mod.ForeignFlowButterfly || mod

    const html = renderToString(React.createElement(ForeignFlowButterfly, {
      items: [
        { symbol: 'FPT', foreign_buy_val: 200e9, foreign_sell_val: 20e9 },
        { symbol: 'VHM', foreign_buy_val: 10e9, foreign_sell_val: 150e9 }
      ]
    }))

    assert.ok(html.includes('Giao Dịch Khối Ngoại (Cánh Bướm)'), 'Must render Butterfly card title')
    assert.ok(html.includes('Top Mua Ròng'), 'Must render Buy Wing')
    assert.ok(html.includes('Top Bán Ròng'), 'Must render Sell Wing')
  })

  it('renders VnIndexImpactWidget with positive and negative drivers', async () => {
    const mod = await loadComponent('./src/features/market-portfolio/components/VnIndexImpactWidget.jsx')
    const VnIndexImpactWidget = mod.VnIndexImpactWidget || mod

    const html = renderToString(React.createElement(VnIndexImpactWidget, {
      items: [
        { symbol: 'VCB', change_pct: 2.5, market_cap: 500000 },
        { symbol: 'VIC', change_pct: -3.0, market_cap: 350000 }
      ]
    }))

    assert.ok(html.includes('Tác Động Chỉ Số VN-Index'), 'Must render Index Impact title')
    assert.ok(html.includes('Top Kéo Điểm'), 'Must render Positive leaders')
    assert.ok(html.includes('Top Đè Điểm'), 'Must render Negative laggards')
  })
})
