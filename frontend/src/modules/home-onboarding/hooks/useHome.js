import { useQuery } from '@tanstack/react-query'
import { fetchPersonalizedHome } from '../services/homeOnboardingApi'

export function homeQueryKey(sessionId) {
  return ['home', sessionId]
}

export function useHome(sessionId, refreshKey = 0) {
  const query = useQuery({
    queryKey: [...homeQueryKey(sessionId), refreshKey],
    queryFn: () => fetchPersonalizedHome(sessionId),
    enabled: Boolean(sessionId),
  })

  return {
    data: query.data ?? null,
    isLoading: query.isPending && query.fetchStatus !== 'idle',
    error: query.error ? query.error.message : '',
    refetch: query.refetch,
  }
}
