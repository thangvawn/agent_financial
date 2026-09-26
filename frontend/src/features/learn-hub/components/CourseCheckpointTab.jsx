import React, { useState, useEffect, useCallback } from 'react'
import { fetchCheckpoint, gradeCheckpoint, completeCheckpoint } from '../services/learningApi'
import CheckpointCard from './CheckpointCard'
import SocraticHintWidget from './SocraticHintWidget'
import MasteryProposalReview from './MasteryProposalReview'
import { useMasteryProposal, resolveMasteryThreshold } from '../hooks/useMasteryProposal'
import './checkpoint.css'

export default function CourseCheckpointTab({
  lessonId,
  sessionId,
  userTier = 'community',
  userRole = 'retail',
  onCompleteLesson,
}) {
  const [checkpoint, setCheckpoint] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedOption, setSelectedOption] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [gradeResult, setGradeResult] = useState(null)
  const [showHint, setShowHint] = useState(false)
  const [activeProposal, setActiveProposal] = useState(null)
  const [completed, setCompleted] = useState(false)

  const loadQuestion = useCallback(async () => {
    if (!lessonId) return
    try {
      setLoading(true)
      setError(null)
      setSelectedOption(null)
      setGradeResult(null)
      setShowHint(false)
      setActiveProposal(null)
      const data = await fetchCheckpoint(sessionId, lessonId)
      setCheckpoint(data)
    } catch (err) {
      setError(err.message || 'Không thể tải câu hỏi kiểm tra.')
    } finally {
      setLoading(false)
    }
  }, [lessonId, sessionId])

  useEffect(() => {
    loadQuestion()
  }, [loadQuestion])

  const handleSubmit = async ({ checkpointId, response }) => {
    try {
      setIsSubmitting(true)
      setError(null)
      const result = await gradeCheckpoint(sessionId, checkpointId, response)
      setGradeResult(result)

      const threshold = resolveMasteryThreshold({ tier: userTier, role: userRole })
      if (result.passed && result.score >= threshold && result.verified_event_id) {
        const expires = new Date(Date.now() + 10 * 60 * 1000).toISOString()
        setActiveProposal({
          proposal_id: `prop_${Date.now()}`,
          operation: 'complete_learning_checkpoint',
          verified_event_id: result.verified_event_id,
          idempotency_key: `idemp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          lesson_id: lessonId,
          score: result.score,
          threshold,
          risk_class: 'MEDIUM',
          expires_at: expires,
          payload_preview: {
            lesson_id: lessonId,
            verified_event_id: result.verified_event_id,
            score: result.score,
            status: 'completed',
          },
        })
      }
    } catch (err) {
      setError(err.message || 'Lỗi khi nộp bài.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfirmMastery = async ({ verified_event_id, idempotency_key }) => {
    try {
      await completeCheckpoint(sessionId, verified_event_id, idempotency_key)
      setCompleted(true)
      setActiveProposal(null)
      if (typeof onCompleteLesson === 'function') {
        onCompleteLesson(lessonId)
      }
    } catch (err) {
      setError(err.message || 'Lỗi khi xác nhận hoàn thành.')
    }
  }

  if (loading) {
    return (
      <div className="lh-checkpoint-loading" style={{ padding: 'var(--sp-5)', color: 'var(--ink-muted)' }}>
        Đang tải câu hỏi kiểm tra từ kho câu hỏi ngẫu nhiên...
      </div>
    )
  }

  return (
    <div className="lh-course-checkpoint-container" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
      {error && (
        <div style={{
          padding: 'var(--sp-4)',
          backgroundColor: 'rgba(239, 83, 80, 0.1)',
          border: '1px solid rgba(239, 83, 80, 0.3)',
          color: '#ef5350',
          borderRadius: 'var(--radius-sm)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>⚠️ {error}</div>
          <button
            type="button"
            onClick={loadQuestion}
            style={{
              padding: '4px 10px',
              backgroundColor: 'rgba(239, 83, 80, 0.2)',
              border: '1px solid rgba(239, 83, 80, 0.4)',
              color: '#ffffff',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Thử tải lại
          </button>
        </div>
      )}

      {checkpoint && (
        <CheckpointCard
          checkpointId={checkpoint.checkpoint_id}
          lessonId={checkpoint.lesson_id}
          prompt={checkpoint.prompt}
          options={checkpoint.options}
          selectedOption={selectedOption}
          onSelectOption={setSelectedOption}
          onSubmit={handleSubmit}
          onRequestHint={() => setShowHint((prev) => !prev)}
          isSubmitting={isSubmitting}
          disabled={completed}
          gradeResult={gradeResult}
        />
      )}

      {showHint && (
        <SocraticHintWidget
          lessonTitle={lessonId}
          onDismiss={() => setShowHint(false)}
        />
      )}

      {activeProposal && (
        <MasteryProposalReview
          proposal={activeProposal}
          onConfirm={handleConfirmMastery}
          onReject={() => setActiveProposal(null)}
        />
      )}

      {completed && (
        <div style={{ padding: 'var(--sp-3)', backgroundColor: 'var(--pos-soft)', color: 'var(--pos-strong)', borderRadius: 'var(--radius-sm)', fontWeight: 600 }}>
          ✓ Đã hoàn thành bài học và lưu tiến độ có kiểm chứng vào hồ sơ học tập!
        </div>
      )}
    </div>
  )
}

