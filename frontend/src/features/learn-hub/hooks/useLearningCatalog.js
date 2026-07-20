import { useQuery } from '@tanstack/react-query'

import { fetchLearningCatalog, fetchLearningCatalogTopics } from '../services/learningApi'

export function useLearningCatalog({ enabled, kind, topic }) {
  const itemsQuery = useQuery({
    queryKey: ['learning', 'catalog', kind, topic || ''],
    queryFn: () => fetchLearningCatalog(kind, { topic: topic || undefined, limit: 60 }),
    enabled,
  })

  const topicsQuery = useQuery({
    queryKey: ['learning', 'catalog', 'topics'],
    queryFn: () => fetchLearningCatalogTopics(),
    enabled,
    staleTime: 60 * 60 * 1000,
  })

  return {
    items: itemsQuery.data?.items ?? [],
    topics: topicsQuery.data?.topics ?? [],
    isLoading:
      (itemsQuery.isPending && itemsQuery.fetchStatus !== 'idle') ||
      (topicsQuery.isPending && topicsQuery.fetchStatus !== 'idle'),
    error: itemsQuery.error ? itemsQuery.error.message || 'Không tải được thư viện.' : '',
  }
}
