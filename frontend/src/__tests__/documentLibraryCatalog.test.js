import { describe, it } from 'node:test'
import assert from 'node:assert/strict'

import {
  DOCUMENT_FOLDERS,
  DOCUMENT_TYPES,
  matchesFolder,
  normalizeDbPaper,
} from '../features/learn-hub/content/paperCatalogData.js'

describe('Document Library & Thematic Folders Contract', () => {
  it('defines distinct document types for separating books and research papers', () => {
    const ids = DOCUMENT_TYPES.map((t) => t.id)
    assert.deepEqual(ids, ['all', 'book', 'paper'])
  })

  it('defines comprehensive thematic folders with descriptions and icons', () => {
    assert.ok(DOCUMENT_FOLDERS.length >= 10, 'Must have at least 10 folders')
    const allFolder = DOCUMENT_FOLDERS.find((f) => f.id === 'all')
    assert.ok(allFolder, 'All folder must exist')

    const macroFolder = DOCUMENT_FOLDERS.find((f) => f.id === 'macro_crisis')
    assert.ok(macroFolder, 'Macro & Crisis folder must exist')
    assert.match(macroFolder.label, /vĩ mô/i)

    const quantFolder = DOCUMENT_FOLDERS.find((f) => f.id === 'quant_risk')
    assert.ok(quantFolder, 'Quant & Risk folder must exist')
  })

  it('normalizes research paper from DB correctly with source label and authors', () => {
    const raw = {
      paper_id: 'paper_test_123',
      source: 'arxiv',
      title: 'Wasserstein Distributionally Robust Portfolio Optimization',
      authors: ['Alice Smith', 'Bob Jones'],
      abstract: 'We present a distributionally robust framework for multi-asset portfolios.',
      published_at: '2026-10-08T12:00:00Z',
      topics: ['quantitative_finance', 'risk_management'],
      category: 'q-fin.PM',
      url: 'https://arxiv.org/abs/2610.12345',
      pdf_url: 'https://arxiv.org/pdf/2610.12345.pdf',
    }

    const normalized = normalizeDbPaper(raw)
    assert.equal(normalized.type, 'paper')
    assert.equal(normalized.paper_id, 'paper_test_123')
    assert.equal(normalized.source_label, 'arXiv (q-fin)')
    assert.equal(normalized.author, 'Alice Smith, Bob Jones')
    assert.equal(normalized.pdf_url, 'https://arxiv.org/pdf/2610.12345.pdf')
  })

  it('correctly matches items into corresponding thematic folders', () => {
    const quantPaper = {
      title: 'Factor Models and Covariance Estimation',
      topics: ['quantitative_finance'],
      summary: 'Statistical factor models for risk parity portfolios',
    }
    assert.equal(matchesFolder(quantPaper, 'all'), true)
    assert.equal(matchesFolder(quantPaper, 'quant_risk'), true)
    assert.equal(matchesFolder(quantPaper, 'behavioral'), false)

    const macroBook = {
      title: 'Big Debt Crises',
      topics: ['macroeconomics', 'inflation'],
      summary: 'A template for understanding debt cycles',
    }
    assert.equal(matchesFolder(macroBook, 'macro_crisis'), true)
    assert.equal(matchesFolder(macroBook, 'bctc_valuation'), false)
  })
})
