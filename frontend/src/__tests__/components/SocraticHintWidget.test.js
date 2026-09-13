import { describe, it, after } from 'node:test'
import assert from 'node:assert'
import { loadComponent, closeViteServer, React, renderToString } from '../test-helpers.js'

const MOCK_HINT_DATA = {
  checkpointId: 'cp_socratic_001',
  lessonId: 'lesson_sharpe_ratio',
  socraticCoaching: {
    focus_concept: 'Total Risk vs Systematic Risk',
    hint: 'Hãy nhớ lại công thức gốc của William Sharpe: Mẫu số sử dụng độ lệch chuẩn sigma, đại diện cho rủi ro phân tán hay rủi ro toàn phần?',
  },
  steps: [
    {
      level: 1,
      title: 'Nguyên lý cốt lõi',
      content: 'Tỷ số Sharpe đo lường phần bù rủi ro trên mỗi đơn vị rủi ro toàn phần của danh mục.',
    },
    {
      level: 2,
      title: 'Mối quan hệ biến số',
      content: 'Mẫu số là độ lệch chuẩn sigma (đo rủi ro tổng thể), khác biệt căn bản với hệ số Beta của CAPM.',
    },
    {
      level: 3,
      title: 'Câu hỏi định hướng',
      content: 'Nếu một danh mục chịu rủi ro phi hệ thống, đại lượng nào phản ánh trọn vẹn rủi ro đó?',
    },
  ],
}

describe('SocraticHintWidget Component Contract & Progressive Disclosure (TASK UI-04)', () => {
  after(async () => {
    await closeViteServer()
  })

  it('loads SocraticHintWidget component successfully from feature path', async () => {
    const SocraticHintWidget = await loadComponent('./src/features/learn-hub/components/SocraticHintWidget.jsx')
    assert.strictEqual(typeof SocraticHintWidget, 'function', 'SocraticHintWidget must export a React component')
  })

  it('enforces Zero-Leakage: strictly forbids correct_answer in rendered hint output', async () => {
    const SocraticHintWidget = await loadComponent('./src/features/learn-hub/components/SocraticHintWidget.jsx')
    const contaminatedProps = {
      ...MOCK_HINT_DATA,
      correct_answer: 'Độ lệch chuẩn tổng thể đo lường toàn bộ biến động giá',
      correctAnswer: 'Option A',
    }
    const html = renderToString(React.createElement(SocraticHintWidget, contaminatedProps))

    assert.ok(!html.includes('correct_answer'), 'Zero-Leakage violated: correct_answer leaked in Socratic widget')
    assert.ok(!html.includes('correctAnswer'), 'Zero-Leakage violated: correctAnswer leaked in Socratic widget')
    assert.ok(!html.toLowerCase().includes('đáp án đúng là'), 'Direct answer spoon-feeding prohibited')
  })

  it('implements progressive disclosure: renders Level 1 hint and collapses Level 2 initially', async () => {
    const SocraticHintWidget = await loadComponent('./src/features/learn-hub/components/SocraticHintWidget.jsx')
    const html = renderToString(React.createElement(SocraticHintWidget, {
      ...MOCK_HINT_DATA,
      currentLevel: 1,
    }))

    // Level 1 should be visible
    assert.ok(
      html.includes('Total Risk vs Systematic Risk') || html.includes('Nguyên lý cốt lõi'),
      'Level 1 focus concept / title must be rendered',
    )
    // Level 2 content should not be revealed in initial state
    assert.ok(
      !html.includes('khác biệt căn bản với hệ số Beta của CAPM') || html.includes('is-collapsed') || html.includes('locked'),
      'Level 2 detail must be progressively guarded',
    )
  })

  it('reveals Level 2 hint when currentLevel is progressed to 2', async () => {
    const SocraticHintWidget = await loadComponent('./src/features/learn-hub/components/SocraticHintWidget.jsx')
    const html = renderToString(React.createElement(SocraticHintWidget, {
      ...MOCK_HINT_DATA,
      currentLevel: 2,
    }))

    assert.ok(
      html.includes('Mối quan hệ biến số') || html.includes('độ lệch chuẩn sigma'),
      'Level 2 stage must be revealed when progressive disclosure reaches level 2',
    )
  })

  it('provides unlock button to step forward through pedagogical hints', async () => {
    const SocraticHintWidget = await loadComponent('./src/features/learn-hub/components/SocraticHintWidget.jsx')
    const html = renderToString(React.createElement(SocraticHintWidget, {
      ...MOCK_HINT_DATA,
      currentLevel: 1,
    }))

    assert.ok(
      html.includes('gợi ý tiếp theo') || html.includes('Gợi ý bước') || html.includes('Mức 2') || html.includes('Next Hint'),
      'Action button to reveal next progressive hint must be available',
    )
  })

  it('adheres to Fintech-minimal design system with tokens.css variables and mono badges', async () => {
    const SocraticHintWidget = await loadComponent('./src/features/learn-hub/components/SocraticHintWidget.jsx')
    const html = renderToString(React.createElement(SocraticHintWidget, MOCK_HINT_DATA))

    assert.ok(
      html.includes('socratic-hint') || html.includes('lh-socratic') || html.includes('hint-widget'),
      'Widget must have semantic container class',
    )
    assert.ok(
      html.includes('stepper') || html.includes('accordion') || html.includes('step'),
      'Progressive structure must be organized as stepper or accordion',
    )
    assert.ok(!html.includes('linear-gradient(135deg, #a855f7'), 'Anti-AI-Slop: generic gradient prohibited')
  })
})
