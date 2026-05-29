import { useQueries } from '@tanstack/react-query'

import {
  fetchLearningCoach,
  fetchLearningContext,
  fetchLearningLesson,
} from '../services/learningApi'

export function useLearningNextLessonBundle(sessionId, nextLessonId) {
  const enabled = Boolean(sessionId && nextLessonId)

  const queries = useQueries({
    queries: [
      {
        queryKey: ['learning', 'lesson', sessionId, nextLessonId],
        queryFn: () => fetchLearningLesson(sessionId, nextLessonId),
        enabled,
      },
      {
        queryKey: ['learning', 'coach', sessionId, 'continue_path'],
        queryFn: () => fetchLearningCoach(sessionId, 'continue_path'),
        enabled,
      },
      {
        queryKey: ['learning', 'context', 'drawdown'],
        queryFn: () => fetchLearningContext('drawdown'),
        enabled,
      },
      {
        queryKey: ['learning', 'context', 'compound_interest'],
        queryFn: () => fetchLearningContext('compound_interest'),
        enabled,
      },
    ],
  })

  const [lessonQ, coachQ, drawdownQ, compoundQ] = queries
  const contextCards = []
  if (drawdownQ.data) contextCards.push(drawdownQ.data)
  if (compoundQ.data) contextCards.push(compoundQ.data)

  const isPending = enabled && queries.some((q) => q.isPending && q.fetchStatus !== 'idle')
  const lessonError = lessonQ.error ? lessonQ.error.message || 'Không tải được bài học tiếp theo.' : ''

  return {
    lesson: lessonQ.data ?? null,
    coach: coachQ.data ?? null,
    contextCards,
    isLoading: isPending,
    lessonError,
  }
}
