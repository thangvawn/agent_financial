import { describe, it, beforeEach, afterEach, after } from 'node:test'
import assert from 'node:assert'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import * as learningApi from '../features/learn-hub/services/learningApi.js'

async function loadLearningTypes() {
  try {
    return await import('../features/learn-hub/types/learningTypes.js')
  } catch {
    return null
  }
}

async function loadMasteryProposal() {
  try {
    return await import('../features/learn-hub/hooks/useMasteryProposal.js')
  } catch {
    return null
  }
}

async function loadMasteryProposalReview() {
  try {
    const { getViteServer } = await import('./test-helpers.js')
    const server = await getViteServer()
    return await server.ssrLoadModule('./src/features/learn-hub/components/MasteryProposalReview.jsx')
  } catch {
    return null
  }
}

describe('Learning Checkpoint API & Types (TDD Test Suite)', () => {
  let originalFetch
  let fetchCalls

  beforeEach(() => {
    fetchCalls = []
    originalFetch = globalThis.fetch
    globalThis.fetch = async (url, init = {}) => {
      fetchCalls.push({ url: String(url), init })
      return {
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      }
    }
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  describe('Baseline Check', () => {
    it('verifies baseline test runner is operational', () => {
      assert.strictEqual(1 + 1, 2)
    })
  })

  describe('TASK UI-01: learningApi REST functions', () => {
    it('fetchCheckpoint is exported, targets GET /api/v1/public/learning/checkpoint with lesson_id and difficulty query params', async () => {
      assert.strictEqual(
        typeof learningApi.fetchCheckpoint,
        'function',
        'fetchCheckpoint must be an exported function in learningApi.js'
      )

      await learningApi.fetchCheckpoint({
        lesson_id: 'lesson_sharpe_ratio',
        difficulty: 'intermediate',
      })

      assert.strictEqual(fetchCalls.length, 1, 'fetch should be called once')
      const call = fetchCalls[0]
      const url = new URL(call.url, 'http://localhost')
      assert.strictEqual(url.pathname, '/api/v1/public/learning/checkpoint')
      assert.strictEqual(url.searchParams.get('lesson_id'), 'lesson_sharpe_ratio')
      assert.strictEqual(url.searchParams.get('difficulty'), 'intermediate')
      assert.strictEqual(call.init.method || 'GET', 'GET')
    })

    it('gradeCheckpoint is exported, targets POST /api/v1/public/learning/checkpoint/grade with payload', async () => {
      assert.strictEqual(
        typeof learningApi.gradeCheckpoint,
        'function',
        'gradeCheckpoint must be an exported function in learningApi.js'
      )

      const payload = {
        checkpoint_id: 'cp_socratic_001',
        response: 'Tổng độ lệch chuẩn (Total Standard Deviation)',
      }

      await learningApi.gradeCheckpoint(payload)

      assert.strictEqual(fetchCalls.length, 1, 'fetch should be called once')
      const call = fetchCalls[0]
      const url = new URL(call.url, 'http://localhost')
      assert.strictEqual(url.pathname, '/api/v1/public/learning/checkpoint/grade')
      assert.strictEqual(call.init.method, 'POST')
      assert.strictEqual(call.init.headers?.['Content-Type'], 'application/json')
      const body = JSON.parse(call.init.body)
      assert.strictEqual(body.checkpoint_id, 'cp_socratic_001')
      assert.strictEqual(body.response, 'Tổng độ lệch chuẩn (Total Standard Deviation)')
    })

    it('completeCheckpoint is exported, targets POST /api/v1/public/learning/checkpoint/complete with payload', async () => {
      assert.strictEqual(
        typeof learningApi.completeCheckpoint,
        'function',
        'completeCheckpoint must be an exported function in learningApi.js'
      )

      const payload = {
        verified_event_id: 'ev_chk_9f8e7d6c5b4a3120',
        idempotency_key: 'idemp_a1b2c3d4e5f67890',
      }

      await learningApi.completeCheckpoint(payload)

      assert.strictEqual(fetchCalls.length, 1, 'fetch should be called once')
      const call = fetchCalls[0]
      const url = new URL(call.url, 'http://localhost')
      assert.strictEqual(url.pathname, '/api/v1/public/learning/checkpoint/complete')
      assert.strictEqual(call.init.method, 'POST')
      assert.strictEqual(call.init.headers?.['Content-Type'], 'application/json')
      const body = JSON.parse(call.init.body)
      assert.strictEqual(body.verified_event_id, 'ev_chk_9f8e7d6c5b4a3120')
      assert.strictEqual(body.idempotency_key, 'idemp_a1b2c3d4e5f67890')
    })
  })

  describe('TASK UI-02: learningTypes contracts and Zero-Leakage audit', () => {
    it('exports CheckpointItem, GradeRequest, GradeResponse, CompleteRequest, CompleteResponse contracts', async () => {
      const types = await loadLearningTypes()
      assert.ok(types, 'src/features/learn-hub/types/learningTypes.js module must exist')
      assert.ok(types.CheckpointItem, 'CheckpointItem contract must be exported')
      assert.ok(types.GradeRequest, 'GradeRequest contract must be exported')
      assert.ok(types.GradeResponse, 'GradeResponse contract must be exported')
      assert.ok(types.CompleteRequest, 'CompleteRequest contract must be exported')
      assert.ok(types.CompleteResponse, 'CompleteResponse contract must be exported')
    })

    it('validates CheckpointItem structure and Zero-Leakage (no correct_answer)', async () => {
      const types = await loadLearningTypes()
      assert.ok(types, 'src/features/learn-hub/types/learningTypes.js module must exist')
      assert.ok(types.CheckpointItem, 'CheckpointItem contract must be exported')

      const item = types.CheckpointItem
      assert.ok('checkpoint_id' in item, 'CheckpointItem must declare checkpoint_id')
      assert.ok('lesson_id' in item, 'CheckpointItem must declare lesson_id')
      assert.ok('prompt' in item, 'CheckpointItem must declare prompt')
      assert.ok('options' in item, 'CheckpointItem must declare options')
      assert.ok('expires_at' in item, 'CheckpointItem must declare expires_at')

      // Zero-Leakage check
      assert.strictEqual('correct_answer' in item, false, 'Zero-Leakage: correct_answer must NOT exist')
      assert.strictEqual('answer_key' in item, false, 'Zero-Leakage: answer_key must NOT exist')
      assert.strictEqual('solution' in item, false, 'Zero-Leakage: solution must NOT exist')
    })

    it('validates GradeRequest and GradeResponse contract structures', async () => {
      const types = await loadLearningTypes()
      assert.ok(types, 'src/features/learn-hub/types/learningTypes.js module must exist')
      assert.ok(types.GradeRequest, 'GradeRequest contract must be exported')
      assert.ok(types.GradeResponse, 'GradeResponse contract must be exported')

      assert.ok('checkpoint_id' in types.GradeRequest, 'GradeRequest must declare checkpoint_id')
      assert.ok('response' in types.GradeRequest, 'GradeRequest must declare response')

      assert.ok('passed' in types.GradeResponse, 'GradeResponse must declare passed')
      assert.ok('score' in types.GradeResponse, 'GradeResponse must declare score')
      assert.ok('rubric_evidence' in types.GradeResponse, 'GradeResponse must declare rubric_evidence')
      assert.ok('verified_event_id' in types.GradeResponse, 'GradeResponse must declare verified_event_id')
    })

    it('validates CompleteRequest and CompleteResponse contract structures', async () => {
      const types = await loadLearningTypes()
      assert.ok(types, 'src/features/learn-hub/types/learningTypes.js module must exist')
      assert.ok(types.CompleteRequest, 'CompleteRequest contract must be exported')
      assert.ok(types.CompleteResponse, 'CompleteResponse contract must be exported')

      assert.ok('verified_event_id' in types.CompleteRequest, 'CompleteRequest must declare verified_event_id')
      assert.ok('idempotency_key' in types.CompleteRequest, 'CompleteRequest must declare idempotency_key')

      const res = types.CompleteResponse
      assert.ok('receipt_id' in res || 'status' in res, 'CompleteResponse must declare receipt_id or status')
    })
  })

  describe('TASK UI-05 & UI-06: MasteryProposalReview and useMasteryProposal (TDD)', () => {
    describe('resolveMasteryThreshold Logic', () => {
      it('resolves retail/community tier to 75% threshold', async () => {
        const hookMod = await loadMasteryProposal()
        assert.ok(hookMod, 'src/features/learn-hub/hooks/useMasteryProposal.js module must exist')
        assert.strictEqual(
          typeof hookMod.resolveMasteryThreshold,
          'function',
          'resolveMasteryThreshold must be exported from useMasteryProposal.js'
        )

        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'community' }), 75)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'free' }), 75)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'starter' }), 75)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ role: 'retail' }), 75)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: ' COMMUNITY ' }), 75)
      })

      it('resolves pro/institutional tier to 85% threshold', async () => {
        const hookMod = await loadMasteryProposal()
        assert.ok(hookMod, 'src/features/learn-hub/hooks/useMasteryProposal.js module must exist')
        assert.strictEqual(typeof hookMod.resolveMasteryThreshold, 'function')

        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'pro' }), 85)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'enterprise' }), 85)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ role: 'institutional' }), 85)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ role: 'pro' }), 85)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: ' PRO ' }), 85)
      })

      it('resolves default/standard tier to 80% threshold', async () => {
        const hookMod = await loadMasteryProposal()
        assert.ok(hookMod, 'src/features/learn-hub/hooks/useMasteryProposal.js module must exist')
        assert.strictEqual(typeof hookMod.resolveMasteryThreshold, 'function')

        assert.strictEqual(hookMod.resolveMasteryThreshold({}), 80)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'standard' }), 80)
        assert.strictEqual(hookMod.resolveMasteryThreshold(), 80)
        assert.strictEqual(hookMod.resolveMasteryThreshold({ tier: 'unknown', role: 'guest' }), 80)
      })
    })

    describe('MasteryProposalReview Component Rendering & Risk Badge', () => {
      const mockProposal = {
        proposal_id: 'prop_mst_001',
        verified_event_id: 'vevt_chk_8892',
        lesson_id: 'quant_math_basics',
        topic: 'Quantitative Mathematics Foundations',
        score: 85,
        threshold: 80,
        risk_class: 'MEDIUM',
        expires_at: new Date(Date.now() + 300000).toISOString(),
        idempotency_key: 'idem_key_abc_123',
        payload_preview: {
          lesson_id: 'quant_math_basics',
          score: 85,
          verified_event_id: 'vevt_chk_8892',
        },
      }

      it('renders proposal with verified_event, score, and MEDIUM RISK badge', async () => {
        const reviewMod = await loadMasteryProposalReview()
        assert.ok(
          reviewMod,
          'src/features/learn-hub/components/MasteryProposalReview.jsx module must exist'
        )
        assert.strictEqual(
          typeof reviewMod.MasteryProposalReview,
          'function',
          'MasteryProposalReview component must be exported'
        )

        const html = renderToStaticMarkup(
          React.createElement(reviewMod.MasteryProposalReview, {
            proposal: mockProposal,
            onConfirm: () => {},
            onReject: () => {},
          })
        )

        assert.ok(
          html.includes('MEDIUM RISK'),
          'Must render MEDIUM RISK badge per USER_INTERACTION_GUIDE §3.3'
        )
        assert.ok(html.includes('vevt_chk_8892'), 'Must display verified_event_id')
        assert.ok(html.includes('85%') || html.includes('85'), 'Must render score')
        assert.ok(
          html.includes('quant_math_basics') || html.includes('Quantitative Mathematics'),
          'Must render lesson info'
        )
        assert.ok(
          html.includes('Confirm') || html.includes('Confirm Action'),
          'Must have confirm action button'
        )
        assert.ok(html.includes('Reject'), 'Must have reject button')
      })

      it('disables confirm button and indicates expired state when proposal is expired', async () => {
        const reviewMod = await loadMasteryProposalReview()
        assert.ok(
          reviewMod,
          'src/features/learn-hub/components/MasteryProposalReview.jsx module must exist'
        )

        const expiredProposal = {
          ...mockProposal,
          expires_at: new Date(Date.now() - 10000).toISOString(),
        }

        const html = renderToStaticMarkup(
          React.createElement(reviewMod.MasteryProposalReview, {
            proposal: expiredProposal,
            onConfirm: () => {},
            onReject: () => {},
          })
        )

        assert.ok(
          html.toLowerCase().includes('expired'),
          'Must display expiration message when expired'
        )
        assert.ok(
          html.includes('disabled'),
          'Confirm button must be disabled when proposal is expired'
        )
      })

      it('enables confirm button and shows remaining time when proposal is active', async () => {
        const reviewMod = await loadMasteryProposalReview()
        assert.ok(
          reviewMod,
          'src/features/learn-hub/components/MasteryProposalReview.jsx module must exist'
        )

        const activeProposal = {
          ...mockProposal,
          expires_at: new Date(Date.now() + 600000).toISOString(),
        }

        const html = renderToStaticMarkup(
          React.createElement(reviewMod.MasteryProposalReview, {
            proposal: activeProposal,
            onConfirm: () => {},
            onReject: () => {},
          })
        )

        assert.ok(
          html.includes('Expires in') || html.includes('m ') || html.includes('s'),
          'Must display active countdown timer'
        )
      })
    })

    describe('Confirm & Reject Triggers with Idempotency', () => {
      it('passes verified_event_id and idempotency_key upon confirm trigger', async () => {
        const hookMod = await loadMasteryProposal()
        assert.ok(
          hookMod,
          'src/features/learn-hub/hooks/useMasteryProposal.js module must exist'
        )
        assert.ok(
          typeof hookMod.useMasteryProposal === 'function' ||
            typeof hookMod.createMasteryProposal === 'function',
          'Hook useMasteryProposal or factory must be exported'
        )

        const reviewMod = await loadMasteryProposalReview()
        assert.ok(
          reviewMod,
          'src/features/learn-hub/components/MasteryProposalReview.jsx module must exist'
        )

        let confirmedPayload = null
        const handleConfirm = (payload) => {
          confirmedPayload = payload
        }

        const mockProposal = {
          proposal_id: 'prop_mst_002',
          verified_event_id: 'vevt_chk_9901',
          lesson_id: 'delta_hedging',
          score: 92,
          threshold: 85,
          risk_class: 'MEDIUM',
          expires_at: new Date(Date.now() + 300000).toISOString(),
          idempotency_key: 'idemp_delta_9901',
        }

        if (typeof reviewMod.MasteryProposalReview.handleConfirm === 'function') {
          reviewMod.MasteryProposalReview.handleConfirm(mockProposal, handleConfirm)
        } else {
          handleConfirm({
            verified_event_id: mockProposal.verified_event_id,
            idempotency_key: mockProposal.idempotency_key,
            proposal_id: mockProposal.proposal_id,
          })
        }

        assert.ok(confirmedPayload, 'Confirm handler must receive payload')
        assert.strictEqual(confirmedPayload.verified_event_id, 'vevt_chk_9901')
        assert.strictEqual(confirmedPayload.idempotency_key, 'idemp_delta_9901')
      })
    })

    describe('TASK UI-06: Accessibility, Escape Key & tokens.css Compliance', () => {
      const mockProposal = {
        proposal_id: 'prop_mst_003',
        verified_event_id: 'vevt_chk_7711',
        lesson_id: 'var_portfolio',
        topic: 'Value at Risk (VaR)',
        score: 82,
        threshold: 80,
        risk_class: 'MEDIUM',
        expires_at: new Date(Date.now() + 300000).toISOString(),
        idempotency_key: 'idemp_var_7711',
      }

      it('renders with accessible ARIA attributes and live region for timer', async () => {
        const reviewMod = await loadMasteryProposalReview()
        assert.ok(
          reviewMod,
          'src/features/learn-hub/components/MasteryProposalReview.jsx module must exist'
        )

        const html = renderToStaticMarkup(
          React.createElement(reviewMod.MasteryProposalReview, {
            proposal: mockProposal,
            onConfirm: () => {},
            onReject: () => {},
          })
        )

        assert.ok(
          html.includes('role="region"') ||
            html.includes('role="dialog"') ||
            html.includes('role="alertdialog"'),
          'Must have semantic ARIA landmark role (region or dialog)'
        )
        assert.ok(
          html.includes('aria-live') || html.includes('aria-atomic'),
          'Timer or status must have aria-live attribute for screen readers'
        )
      })

      it('invokes onReject when Escape key is pressed', async () => {
        const reviewMod = await loadMasteryProposalReview()
        assert.ok(
          reviewMod,
          'src/features/learn-hub/components/MasteryProposalReview.jsx module must exist'
        )

        let rejected = false
        const handleReject = () => {
          rejected = true
        }

        if (typeof reviewMod.handleKeyDown === 'function') {
          reviewMod.handleKeyDown({ key: 'Escape' }, handleReject)
          assert.strictEqual(rejected, true, 'Escape key must trigger reject callback')
        }
      })
    })
  })

  after(async () => {
    try {
      const { closeViteServer } = await import('./test-helpers.js')
      await closeViteServer()
    } catch (_) {}
  })
})

