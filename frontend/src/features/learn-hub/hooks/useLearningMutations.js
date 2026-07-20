import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  completeLearningLesson,
  submitLearningQuiz,
} from '../services/learningApi'

function invalidateLearning(queryClient) {
  queryClient.invalidateQueries({ queryKey: ['learning', 'home'] })
  queryClient.invalidateQueries({ queryKey: ['learning', 'lesson'] })
}

export function useSubmitLearningQuiz() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, lessonId, answers }) => submitLearningQuiz(sessionId, lessonId, answers),
    onSuccess: () => invalidateLearning(queryClient),
  })
}

export function useCompleteLearningLesson() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sessionId, lessonId }) => completeLearningLesson(sessionId, lessonId),
    onSuccess: () => invalidateLearning(queryClient),
  })
}
