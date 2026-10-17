import test from 'node:test'
import assert from 'node:assert/strict'

import { QUANTA_SECTIONS, TUTORIAL_FAST_TRACK } from '../features/learn-hub/content/quantaCurriculumData.js'
import { getQuantaLessonDetail } from '../features/learn-hub/content/quantaContentService.js'
import { WIKI_FUNCTION_GROUPS, WIKI_FUNCTIONS, WIKI_NAMESPACES } from '../features/learn-hub/content/quantaWikiData.js'

test('Quanta Docs Curriculum Contract', async (t) => {
  await t.test('has 6 core sections matching official curriculum', () => {
    assert.equal(QUANTA_SECTIONS.length, 6)
    const sectionIds = QUANTA_SECTIONS.map((s) => s.id)
    assert.deepEqual(sectionIds, [
      'v2-foundation',
      'v2-indicators',
      'v2-render',
      'v2-act-risk',
      'v2-advanced-ai',
      'v2-recipes',
    ])
  })

  await t.test('has exactly 5 fast-track tutorial lessons', () => {
    assert.equal(TUTORIAL_FAST_TRACK.length, 5)
    assert.equal(TUTORIAL_FAST_TRACK[0].slug, 'quanta-overview')
    assert.equal(TUTORIAL_FAST_TRACK[1].slug, 'chien-luoc-dau-tien')
  })

  await t.test('loads rich lesson details with checklist and demo code', () => {
    const lesson = getQuantaLessonDetail('chien-luoc-dau-tien')
    assert.ok(lesson)
    assert.equal(lesson.title, 'Chiến lược đầu tiên (EMA Cross)')
    assert.ok(lesson.demo_code.includes('strategy "Tide Reclaim Pulse"'))
    assert.ok(lesson.body.length > 50)
  })
})

test('Quanta Docs 59 Built-in Functions & Wiki Contract', async (t) => {
  await t.test('contains exactly 12 function categories totaling 59 functions', () => {
    assert.equal(WIKI_FUNCTION_GROUPS.length, 12)
    const totalFns = WIKI_FUNCTION_GROUPS.reduce((acc, g) => acc + g.items.length, 0)
    assert.equal(totalFns, 59)
  })

  await t.test('defines smart namespaces for VN trading', () => {
    assert.equal(WIKI_NAMESPACES.length, 5)
    const nsNames = WIKI_NAMESPACES.map((n) => n.name)
    assert.ok(nsNames.includes('market.*'))
    assert.ok(nsNames.includes('position.*'))
    assert.ok(nsNames.includes('account.*'))
  })

  await t.test('all functions have valid signatures and examples', () => {
    assert.ok(WIKI_FUNCTIONS.sma)
    assert.ok(WIKI_FUNCTIONS.sma.sig.includes('sma'))
    assert.ok(WIKI_FUNCTIONS.rsi)
    assert.ok(WIKI_FUNCTIONS.crossover)
    assert.ok(WIKI_FUNCTIONS.position_size)
  })
})
