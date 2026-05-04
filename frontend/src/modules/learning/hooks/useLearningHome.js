import { useEffect, useState } from 'react'

import { fetchLearningHome } from '../services/learningApi'

export function useLearningHome(sessionId, refreshKey = 0) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(Boolean(sessionId))
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function run() {
      if (!sessionId) {
        setIsLoading(false)
        return
      }
      setIsLoading(true)
      setError('')
      try {
        const payload = await fetchLearningHome(sessionId)
        if (!cancelled) setData(payload)
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [refreshKey, sessionId])

  return { data, isLoading, error }
}
