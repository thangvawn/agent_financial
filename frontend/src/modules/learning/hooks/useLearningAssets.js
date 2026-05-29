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
        queryKey: ['learning', 'assets', 'audios'],
        queryFn: () => fetchLearningAssets('audios'),
        enabled,
      },
      {
        queryKey: ['learning', 'assets', 'books'],
        queryFn: () => fetchLearningAssets('books'),
        enabled,
      },
    ],
  })

  const [videoQ, audioQ, bookQ] = queries
  const isPending = enabled && queries.some((q) => q.isPending && q.fetchStatus !== 'idle')
  const allFailed = videoQ.isError && audioQ.isError && bookQ.isError

  return {
    videoItems: videoQ.data?.items ?? [],
    audioItems: audioQ.data?.items ?? null,
    bookItems: bookQ.data?.items ?? [],
    isLoading: isPending,
    error: allFailed ? 'Không tải được danh sách media local.' : '',
    audioFailed: audioQ.isError,
  }
}
