import test, { describe } from 'node:test'
import assert from 'node:assert/strict'

import { resolveBookSource, toReadableBook } from '../../features/learn-hub/pages/bookSource.js'
import { DEMO_BOOKS } from '../../features/learn-hub/content/demoBooks.js'

describe('Book Reader & Document Ingestion Contract', () => {
  test('resolveBookSource correctly classifies PDF, HTML, and Local Assets', () => {
    const localSample = DEMO_BOOKS.find((b) => b.book_id === 'b-local-sample')
    assert.ok(localSample, 'Local sample book should exist in DEMO_BOOKS')
    const localSource = resolveBookSource(localSample)
    assert.equal(localSource.kind, 'pdf')
    assert.equal(localSource.isLocalAsset, true)

    const grahamBook = DEMO_BOOKS.find((b) => b.book_id === 'b-intelligent-investor')
    assert.ok(grahamBook, 'The Intelligent Investor should exist in DEMO_BOOKS')
    const grahamSource = resolveBookSource(grahamBook)
    assert.equal(grahamSource.kind, 'pdf')
    assert.equal(grahamSource.isLocalAsset, true)

    const wealthBook = DEMO_BOOKS.find((b) => b.book_id === 'b-wealth-of-nations')
    assert.ok(wealthBook, 'Wealth of Nations should exist in DEMO_BOOKS')
    const wealthSource = resolveBookSource(wealthBook)
    assert.equal(wealthSource.kind, 'html')
    assert.equal(wealthSource.isRemote, true)
    assert.equal(wealthSource.archiveId, null)
    assert.ok(wealthSource.viewUrl.startsWith('/api/v1/public/learning/reader/stream?url='))
    assert.equal(wealthSource.openUrl, 'https://www.gutenberg.org/cache/epub/3300/pg3300-images.html')

    const bogleBook = DEMO_BOOKS.find((b) => b.book_id === 'b-common-sense-investing')
    assert.ok(bogleBook, 'Common Sense Investing should exist in DEMO_BOOKS')
    const bogleSource = resolveBookSource(bogleBook)
    assert.equal(bogleSource.kind, 'html')
    assert.equal(bogleSource.isLocalAsset, true)
  })

  test('toReadableBook attaches normalized source, isPdf, isHtml and isText properties', () => {
    const rawGraham = {
      book_id: 'b-intelligent-investor',
      title: 'Nhà Đầu Tư Thông Minh',
      pdf_url: 'https://archive.org/download/the-intelligent-investor/book.pdf',
    }

    const readable = toReadableBook(rawGraham)
    assert.equal(readable.isPdf, false, 'Archive sources require metadata verification first')
    assert.equal(readable.isHtml, false)
    assert.equal(readable.isText, false)
    assert.ok(readable.source, 'source object must be populated')
    assert.equal(readable.source.kind, 'archive')
  })

})
