import { useState, useEffect, useCallback } from 'react'

export function resolveMasteryThreshold(options = {}) {
  const tier = (options?.tier || '').toLowerCase().trim()
  const role = (options?.role || '').toLowerCase().trim()

  if (['community', 'free', 'starter'].includes(tier) || role === 'retail') {
    return 75
  }
  if (['pro', 'enterprise'].includes(tier) || ['institutional', 'pro'].includes(role)) {
    return 85
  }
  return 80
}

export function formatTimeRemaining(expiresAt, now = new Date()) {
  if (!expiresAt) return { expired: true, text: 'Expired', diff: 0 }
  const expires = new Date(expiresAt).getTime()
  const currentTime = now instanceof Date ? now.getTime() : new Date(now).getTime()
  const diff = expires - currentTime

  if (diff <= 0) {
    return { expired: true, text: 'Expired', diff: 0 }
  }
  const minutes = Math.floor(diff / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)
  return {
    expired: false,
    text: `${minutes}m ${seconds}s`,
    diff,
  }
}

export function createMasteryProposal({
  verifiedEvent,
  tier = 'community',
  role = null,
  ttlMinutes = 5,
} = {}) {
  if (!verifiedEvent) return null
  const threshold = resolveMasteryThreshold({ tier, role })
  const expiresAt = new Date(Date.now() + ttlMinutes * 60000).toISOString()
  const eventId = verifiedEvent.event_id || verifiedEvent.verified_event_id
  const idempotencyKey = `idemp_mst_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

  return {
    proposal_id: `prop_mst_${eventId || Date.now()}`,
    verified_event_id: eventId,
    lesson_id: verifiedEvent.lesson_id,
    topic: verifiedEvent.topic || verifiedEvent.lesson_id,
    score: verifiedEvent.score,
    threshold,
    risk_class: 'MEDIUM',
    expires_at: expiresAt,
    idempotency_key: idempotencyKey,
    payload_preview: {
      lesson_id: verifiedEvent.lesson_id,
      score: verifiedEvent.score,
      threshold,
      verified_event_id: eventId,
    },
  }
}

export function useMasteryProposal(initialProposal = null) {
  const [proposal, setProposal] = useState(initialProposal)
  const [timeLeft, setTimeLeft] = useState(() => formatTimeRemaining(initialProposal?.expires_at).text)
  const [isExpired, setIsExpired] = useState(() => formatTimeRemaining(initialProposal?.expires_at).expired)

  useEffect(() => {
    if (!proposal?.expires_at) return
    const updateTimer = () => {
      const { expired, text } = formatTimeRemaining(proposal.expires_at)
      setTimeLeft(text)
      setIsExpired(expired)
    }
    updateTimer()
    const interval = setInterval(updateTimer, 1000)
    return () => clearInterval(interval)
  }, [proposal?.expires_at])

  const confirmProposal = useCallback(
    async (onConfirmCallback) => {
      if (isExpired || !proposal) return
      const payload = {
        verified_event_id: proposal.verified_event_id,
        idempotency_key: proposal.idempotency_key,
        proposal_id: proposal.proposal_id,
      }
      if (onConfirmCallback) {
        await onConfirmCallback(payload)
      }
      return payload
    },
    [isExpired, proposal]
  )

  const rejectProposal = useCallback(
    (onRejectCallback) => {
      if (onRejectCallback && proposal) {
        onRejectCallback({ proposal_id: proposal.proposal_id })
      }
      setProposal(null)
    },
    [proposal]
  )

  return {
    proposal,
    setProposal,
    timeLeft,
    isExpired,
    confirmProposal,
    rejectProposal,
    threshold: proposal ? resolveMasteryThreshold() : 80,
  }
}

