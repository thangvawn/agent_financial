import { useState, useEffect } from 'react'
import { handleKeyDown } from './masteryProposalUtils'

function calculateTime(expiresAt) {
  if (!expiresAt) return { expired: false, text: '' }
  const diff = new Date(expiresAt).getTime() - Date.now()
  if (diff <= 0) return { expired: true, text: 'Expired' }
  const m = Math.floor(diff / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  return { expired: false, text: `${m}m ${s}s` }
}

export function MasteryProposalReview({ proposal, onConfirm, onReject }) {
  const expiresAt = proposal?.expires_at
  const [timerState, setTimerState] = useState(() => calculateTime(expiresAt))

  useEffect(() => {
    if (!expiresAt) return
    const update = () => setTimerState(calculateTime(expiresAt))
    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [expiresAt])

  useEffect(() => {
    const onWindowKey = (e) => handleKeyDown(e, onReject)
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', onWindowKey)
      return () => window.removeEventListener('keydown', onWindowKey)
    }
  }, [onReject])

  if (!proposal) return null
  const isExpired = timerState.expired

  const triggerConfirm = () => {
    if (isExpired || !onConfirm) return
    onConfirm({
      verified_event_id: proposal.verified_event_id,
      idempotency_key: proposal.idempotency_key,
      proposal_id: proposal.proposal_id,
    })
  }

  return (
    <section
      role="region"
      aria-label="Mastery Proposal Review"
      aria-labelledby="mastery-proposal-heading"
      onKeyDown={(e) => handleKeyDown(e, onReject)}
      tabIndex={0}
      style={{
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--sp-5)',
        backgroundColor: 'var(--surface)',
        boxShadow: 'var(--shadow-sm)',
        color: 'var(--ink)',
        fontFamily: 'var(--font-sans)',
        maxWidth: '480px',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--sp-3)' }}>
        <div>
          <h4 id="mastery-proposal-heading" style={{ margin: '0 0 var(--sp-1) 0', fontSize: 'var(--fs-base)', fontWeight: 600, color: 'var(--ink-strong)' }}>
            Mastery Proposal: {proposal.topic || proposal.lesson_id}
          </h4>
          <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)' }}>
            Verified Event: {proposal.verified_event_id}
          </div>
          <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--ink-muted)', marginTop: '2px' }}>
            Score: <strong style={{ color: 'var(--ink-strong)' }}>{proposal.score}%</strong> (Threshold: {proposal.threshold || 80}%)
          </div>
        </div>
        <span
          aria-label="Risk Level: MEDIUM RISK"
          style={{
            fontSize: 'var(--fs-xs)',
            fontWeight: 600,
            padding: '2px 8px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--warn-soft)',
            color: 'var(--warn)',
            letterSpacing: '0.04em',
            fontFamily: 'var(--font-mono)',
            whiteSpace: 'nowrap',
          }}
        >
          MEDIUM RISK
        </span>
      </header>

      <div
        style={{
          marginBottom: 'var(--sp-4)',
          padding: 'var(--sp-3)',
          backgroundColor: 'var(--surface-alt)',
          border: '1px solid var(--line-subtle)',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--fs-xs)',
          fontFamily: 'var(--font-mono)',
          overflowX: 'auto',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        <pre style={{ margin: 0 }}>{JSON.stringify(proposal.payload_preview || proposal, null, 2)}</pre>
      </div>

      <footer style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--sp-3)' }}>
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          style={{
            fontSize: 'var(--fs-sm)',
            color: isExpired ? 'var(--neg)' : 'var(--ink-muted)',
            fontVariantNumeric: 'tabular-nums',
            fontWeight: 500,
          }}
        >
          {isExpired ? 'Proposal expired' : `Expires in: ${timerState.text}`}
        </div>

        <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
          <button
            type="button"
            onClick={onReject}
            style={{
              padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--line-strong)',
              backgroundColor: 'var(--surface)', color: 'var(--ink)', cursor: 'pointer', fontSize: 'var(--fs-sm)', fontWeight: 500,
            }}
          >
            Reject
          </button>
          <button
            type="button"
            onClick={triggerConfirm}
            disabled={isExpired}
            style={{
              padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)', border: 'none',
              backgroundColor: isExpired ? 'var(--surface-sunken)' : 'var(--accent)',
              color: isExpired ? 'var(--ink-subtle)' : 'var(--accent-ink)',
              cursor: isExpired ? 'not-allowed' : 'pointer', fontSize: 'var(--fs-sm)', fontWeight: 600,
            }}
          >
            Confirm Action
          </button>
        </div>
      </footer>
    </section>
  )
}

MasteryProposalReview.handleConfirm = (proposal, onConfirm) => {
  if (typeof onConfirm === 'function' && proposal) {
    onConfirm({
      verified_event_id: proposal.verified_event_id,
      idempotency_key: proposal.idempotency_key,
      proposal_id: proposal.proposal_id,
    })
  }
}

export default MasteryProposalReview
