import { useQuery } from '@tanstack/react-query'

import { fetchLearningHome } from '../services/learningApi'

export function learningHomeQueryKey(sessionId) {
  return ['learning', 'home', sessionId]
}

export function useLearningHome(sessionId) {
  const query = useQuery({
    queryKey: learningHomeQueryKey(sessionId),
    queryFn: () => fetchLearningHome(sessionId),
    enabled: Boolean(sessionId),
  })

  return {
    data: query.data ?? null,
    isLoading: query.isPending && query.fetchStatus !== 'idle',
    error: query.error ? query.error.message : '',
    refetch: query.refetch,
  }
}
