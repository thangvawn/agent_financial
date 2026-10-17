import { describe, it, after } from 'node:test'
import assert from 'node:assert/strict'

import { closeViteServer, loadComponent, React, renderToString } from '../test-helpers.js'

describe('BCTC raw data challenge', () => {
  after(async () => {
    await closeViteServer()
  })

  it('starts from reported inputs and keeps the reference answer hidden', async () => {
    const RawDataChallenge = await loadComponent('./src/features/bctc/pages/RawDataChallenge.jsx')
    const html = renderToString(React.createElement(RawDataChallenge, {
      company: {
        raw_inputs: [
          { field: 'gross_profit', label: 'Lợi nhuận gộp', value: 380, unit: 'VND' },
          { field: 'revenue', label: 'Doanh thu thuần', value: 1000, unit: 'VND' },
        ],
        calculated_fields: [{
          field: 'gross_margin_pct',
          label: 'Biên lợi nhuận gộp',
          formula: 'gross_profit / revenue × 100',
          dependencies: ['gross_profit', 'revenue'],
          value: 38,
          unit: '%',
          status: 'calculated',
        }],
      },
    }))

    assert.match(html, /RAW DATA CHALLENGE/i)
    assert.match(html, /Doanh thu thuần/i)
    assert.match(html, /gross_profit \/ revenue/i)
    assert.doesNotMatch(html, /Đáp án tham chiếu:\s*38/i)
  })
})
