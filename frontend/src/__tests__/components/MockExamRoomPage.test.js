import { describe, it, after } from 'node:test'
import assert from 'node:assert'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

describe('Mock exam room contract', () => {
  after(async () => {
    await closeViteServer()
  })

  it('renders an actionable lobby without requiring browser storage', async () => {
    const MockExamRoomPage = await loadComponent('./src/features/learn-hub/pages/MockExamRoomPage.jsx')
    const html = renderToString(React.createElement(MockExamRoomPage, { onBack: () => {} }))

    assert.ok(html.includes('CFA Level I'), 'CFA exam title must be visible in the lobby')
    assert.ok(html.includes('Bắt đầu phòng thi'), 'Lobby must expose the start action')
    assert.ok(html.includes('90') && html.includes('135'), 'Lobby must expose full-session question count and duration')
    assert.ok(html.includes('Thi thử') && html.includes('Luyện tập'), 'Lobby must expose separate exam and practice modes')
    assert.match(html, /Xem đáp án và giải thích ngay sau mỗi câu/i, 'Practice mode must describe immediate feedback')
    assert.ok(html.includes('BLUEPRINT') && html.includes('2027'), 'Lobby must identify the public blueprint year')
    assert.ok(html.includes('không được CFA Institute hay AlphaMock bảo trợ'), 'Lobby must disclose the first-party practice content')
    assert.ok(!html.includes('Đáp án:'), 'Answer explanations must remain hidden before submission')
  })

  it('keeps every question answer key valid and every domain reviewable', async () => {
    const { MOCK_EXAM } = await import('../../features/learn-hub/content/mockExamData.js')

    assert.strictEqual(MOCK_EXAM.questions.length, MOCK_EXAM.questionCount)
    assert.ok(MOCK_EXAM.timeLimitSeconds > 0)
    assert.strictEqual(MOCK_EXAM.benchmarkScore, 70)
    assert.strictEqual(MOCK_EXAM.levelLabel, 'Level I')
    assert.strictEqual(MOCK_EXAM.topicWeights.length, 10)
    assert.ok(MOCK_EXAM.officialFormat.includes('180'))
    assert.ok(MOCK_EXAM.scaledFormat.includes('90 giây'))
    assert.strictEqual(MOCK_EXAM.sessionQuestionCount, 90)
    assert.strictEqual(MOCK_EXAM.totalExamQuestionCount, 180)
    const questionDomains = new Set(MOCK_EXAM.questions.map((question) => question.domain))
    const blueprintDomains = new Set(MOCK_EXAM.topicWeights.map((topic) => topic.domain))
    assert.strictEqual(questionDomains.size, 10)
    assert.deepStrictEqual([...questionDomains].sort(), [...blueprintDomains].sort())
    for (const question of MOCK_EXAM.questions) {
      assert.ok(question.domain, `Question ${question.id} must have a competency domain`)
      assert.ok(question.options.some((option) => option.id === question.correctOptionId), `Question ${question.id} has an invalid answer key`)
      assert.strictEqual(question.options.length, 3, `Question ${question.id} must follow the CFA A/B/C choice format`)
      assert.ok(question.explanation && question.takeaway, `Question ${question.id} needs post-submit learning feedback`)
    }
  })
})
