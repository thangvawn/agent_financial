import { useQueries } from '@tanstack/react-query'

import { fetchLearningAssets } from '../services/learningApi'

export function useLearningAssets(sessionId) {
  const enabled = Boolean(sessionId)

  const queries = useQueries({
    queries: [
      {
        queryKey: ['learning', 'assets', 'videos'],
        queryFn: () => fetchLearningAssets('videos'),
        enabled,
      },
      {
        queryKey: ['learning', 'assets', 'books'],
        queryFn: () => fetchLearningAssets('books'),
        enabled,
      },
    ],
  })

  const [videoQ, bookQ] = queries
  const isPending = enabled && queries.some((q) => q.isPending && q.fetchStatus !== 'idle')
  const errorMsg = videoQ.error?.message || bookQ.error?.message || ''

  return {
    videoItems: videoQ.data?.items ?? [],
    bookItems: bookQ.data?.items ?? [],
    isLoading: isPending,
    error: errorMsg,
  }
}
