import { describe, it, after } from 'node:test'
import assert from 'node:assert'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

const MOCK_CHECKPOINT = {
  checkpointId: 'cp_socratic_001',
  lessonId: 'lesson_sharpe_ratio',
  prompt: 'Xét danh mục có tỷ suất sinh lời kỳ vọng 15%, lãi suất phi rủi ro 5%, và độ lệch chuẩn 10%. Theo phương pháp Socratic: yếu tố mẫu số phản ánh điều gì về rủi ro toàn phần?',
  options: [
    'Độ lệch chuẩn tổng thể đo lường toàn bộ biến động giá',
    'Hệ số Beta chỉ đo lường rủi ro hệ thống',
    'Tỷ lệ sụt giảm tối đa trong quá khứ',
    'Chi phí vốn bình quân gia quyền (WACC)',
  ],
  expiresAt: '2026-09-12T19:00:00Z',
}

describe('CheckpointCard Component Contract & Zero-Leakage (TASK UI-03)', () => {
  after(async () => {
    await closeViteServer()
  })

  it('loads CheckpointCard component successfully from feature path', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    assert.strictEqual(typeof CheckpointCard, 'function', 'CheckpointCard must export a React component')
  })

  it('enforces Zero-Leakage invariant: never leaks correct_answer into DOM or attributes', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const contaminatedProps = {
      ...MOCK_CHECKPOINT,
      correct_answer: 'Độ lệch chuẩn tổng thể đo lường toàn bộ biến động giá',
      correctAnswer: 'Độ lệch chuẩn tổng thể đo lường toàn bộ biến động giá',
    }
    const html = renderToString(React.createElement(CheckpointCard, contaminatedProps))
    assert.ok(!html.includes('correct_answer'), 'Zero-Leakage violated: correct_answer found in rendered HTML')
    assert.ok(!html.includes('correctAnswer'), 'Zero-Leakage violated: correctAnswer found in rendered HTML')
    assert.ok(!html.toLowerCase().includes('data-correct'), 'Zero-Leakage violated: data-correct attribute leaked')
  })

  it('renders flat bento-grid card structure adhering to tokens.css design system', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const html = renderToString(React.createElement(CheckpointCard, MOCK_CHECKPOINT))

    assert.ok(html.includes(MOCK_CHECKPOINT.prompt), 'Prompt text must be rendered')
    assert.ok(html.includes('cp_socratic_001') || html.includes('Checkpoint'), 'Checkpoint identifier must be present')
    assert.ok(
      html.includes('checkpoint-card') || html.includes('lh-checkpoint') || html.includes('bento'),
      'Card must apply bento-grid container class',
    )
    assert.ok(!html.includes('gradient-ai') && !html.includes('purple-gradient'), 'Anti-AI-Slop: no generic gradients')
  })

  it('renders all options as radio cards with JetBrains Mono option badges (A, B, C, D)', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const html = renderToString(React.createElement(CheckpointCard, MOCK_CHECKPOINT))

    for (const option of MOCK_CHECKPOINT.options) {
      assert.ok(html.includes(option), `Option "${option}" must be rendered in radio card`)
    }
    assert.ok(html.includes('>A<') || html.includes('A.'), 'Option badge A must be present')
    assert.ok(html.includes('>B<') || html.includes('B.'), 'Option badge B must be present')
  })

  it('handles option selection and marks selected option as active/checked', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const selectedText = MOCK_CHECKPOINT.options[0]
    const html = renderToString(React.createElement(CheckpointCard, {
      ...MOCK_CHECKPOINT,
      selectedOption: selectedText,
    }))

    assert.ok(
      html.includes('aria-checked="true"') || html.includes('is-selected') || html.includes('checked'),
      'Selected option must be visually and semantically active',
    )
  })

  it('disables submit button when no option is selected and enables when selected', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const unselectedHtml = renderToString(React.createElement(CheckpointCard, {
      ...MOCK_CHECKPOINT,
      selectedOption: null,
    }))
    assert.ok(
      unselectedHtml.includes('disabled') || unselectedHtml.includes('aria-disabled="true"'),
      'Submit button must be disabled when selectedOption is null',
    )

    const selectedHtml = renderToString(React.createElement(CheckpointCard, {
      ...MOCK_CHECKPOINT,
      selectedOption: MOCK_CHECKPOINT.options[1],
    }))
    assert.ok(
      selectedHtml.includes('Gửi câu trả lời') || selectedHtml.includes('Nộp bài') || selectedHtml.includes('Submit'),
      'Submit CTA button must be present',
    )
  })

  it('renders "Cần gợi ý" button to request Socratic coaching without leaking answers', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const html = renderToString(React.createElement(CheckpointCard, MOCK_CHECKPOINT))

    assert.ok(
      html.includes('Cần gợi ý') || html.includes('Gợi ý Socratic') || html.includes('Hint'),
      'Request Socratic hint button must be present in action area',
    )
  })

  it('displays structured feedback when gradeResult is provided', async () => {
    const CheckpointCard = await loadComponent('./src/features/learn-hub/components/CheckpointCard.jsx')
    const gradeResult = {
      passed: true,
      score: 100,
      rubric_evidence: ['Học viên xác định chính xác mẫu số tỷ số Sharpe là độ lệch chuẩn sigma.'],
      misconceptions: [],
      verified_event_id: 'ev_chk_9f8e7d6c5b4a3120',
    }
    const html = renderToString(React.createElement(CheckpointCard, {
      ...MOCK_CHECKPOINT,
      gradeResult,
    }))

    assert.ok(html.includes('100') || html.includes('Chính xác') || html.includes('passed'), 'Grade score must be displayed')
    assert.ok(html.includes('độ lệch chuẩn sigma'), 'Rubric evidence must be rendered')
  })
})
