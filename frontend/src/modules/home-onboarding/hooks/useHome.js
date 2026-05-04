import { useEffect, useState } from 'react'
import { fetchPersonalizedHome } from '../services/homeOnboardingApi'

export function useHome(sessionId, refreshKey = 0) {
  const [data, setData] = useState(null)
  const [isLoading, setIsLoading] = useState(Boolean(sessionId))
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function run() {
      if (!sessionId) {
        setData(null)
        setError('')
        setIsLoading(false)
        return
      }
      setIsLoading(true)
      setError('')
      try {
        const payload = await fetchPersonalizedHome(sessionId)
        if (!cancelled) setData(payload)
      } catch (err) {
        if (!cancelled) {
          setData(null)
          setError(err.message)
        }
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
