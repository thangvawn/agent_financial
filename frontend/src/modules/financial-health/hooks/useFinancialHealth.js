import { useEffect, useState } from 'react'
import { fetchFinancialHealthSnapshot } from '../services/financialHealthApi'

export function useFinancialHealth(sessionId) {
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
        const payload = await fetchFinancialHealthSnapshot(sessionId)
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
  }, [sessionId])

  return { data, isLoading, error }
}
