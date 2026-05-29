import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  askLearningTutor,
  completeLearningLesson,
  submitLearningQuiz,
} from '../services/learningApi'

function invalidateLearning(queryClient) {
  queryClient.invalidateQueries({ queryKey: ['learning', 'home'] })
  queryClient.invalidateQueries({ queryKey: ['learning', 'lesson'] })
  queryClient.invalidateQueries({ queryKey: ['learning', 'coach'] })
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

export function useAskLearningTutor() {
  return useMutation({
    mutationFn: ({ sessionId, lessonId, question, knowledgeLevel }) =>
      askLearningTutor(sessionId, lessonId, question, knowledgeLevel),
  })
}
