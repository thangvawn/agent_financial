import { useCallback, useEffect, useState } from 'react'

import {
  askVideoAgent,
  fetchVideoAgentCheckpoint,
  gradeVideoAgentCheckpoint,
  prepareVideoAgent,
} from '../services/learningApi'
import './video-agent.css'

const OPTION_LETTERS = ['A', 'B', 'C', 'D']

function formatTime(seconds) {
  const value = Math.max(0, Math.round(Number(seconds) || 0))
  return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`
}

export default function VideoLearningAgentPanel({ lessonId, lesson, sessionId, currentTimeSeconds = 0 }) {
  const [preparation, setPreparation] = useState(null)
  const [checkpoint, setCheckpoint] = useState(null)
  const [selected, setSelected] = useState('')
  const [grade, setGrade] = useState(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const sourceUrl = lesson?.video_url || null

  const prepare = useCallback(async () => {
    if (!lessonId) return
    setLoading(true)
    setError(null)
    try {
      const result = await prepareVideoAgent(sessionId, lessonId, { sourceUrl })
      setPreparation(result)
      setCheckpoint(null)
      setGrade(null)
      setSelected('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [lessonId, sessionId, sourceUrl])

  useEffect(() => {
    setPreparation(null)
    setCheckpoint(null)
    setGrade(null)
    setSelected('')
    setAnswer(null)
    setError(null)
  }, [lessonId])

  const createCheckpoint = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchVideoAgentCheckpoint(sessionId, lessonId, {
        sourceUrl,
        currentTimeSeconds,
      })
      setCheckpoint(result)
      setSelected('')
      setGrade(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const submitCheckpoint = async () => {
    if (!checkpoint || !selected) return
    setLoading(true)
    setError(null)
    try {
      const result = await gradeVideoAgentCheckpoint(sessionId, lessonId, checkpoint.checkpoint_id, selected)
      setGrade(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const ask = async (event) => {
    event.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await askVideoAgent(sessionId, lessonId, {
        question: question.trim(),
        sourceUrl,
        currentTimeSeconds,
      })
      setAnswer(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="lh-video-agent" role="region" aria-label="Video Learning Agent">
      <div className="lh-video-agent__intro">
        <div>
          <span className="lh-video-agent__eyebrow">VIDEO LEARNING AGENT</span>
          <h3>Học cùng transcript của video</h3>
          <p>
            Agent đọc transcript, tạo câu hỏi ngắn theo đúng nội dung và trả lời có mốc thời gian.
            Mốc đang xem: <strong>{formatTime(currentTimeSeconds)}</strong>.
          </p>
        </div>
        <button type="button" className="lhc-btn lhc-btn--outline" onClick={prepare} disabled={loading}>
          {loading ? 'Đang chuẩn bị…' : 'Chuẩn bị nội dung'}
        </button>
      </div>

      {preparation ? (
        <div className="lh-video-agent__status" role="status">
          <span>✓ Đã sẵn sàng từ {preparation.source === 'youtube_captions' ? 'phụ đề YouTube' : 'nội dung bài học'}</span>
          <span>{preparation.segment_count} đoạn · {preparation.quiz_count} câu hỏi</span>
          {preparation.warnings?.map((warning) => <small key={warning}>⚠ {warning}</small>)}
        </div>
      ) : null}

      <div className="lh-video-agent__grid">
        <section className="lh-video-agent__card">
          <div className="lh-video-agent__card-head">
            <div><span className="lh-video-agent__number">01</span><h4>Kiểm tra nhanh</h4></div>
            <button type="button" className="lhc-btn lhc-btn--primary" onClick={createCheckpoint} disabled={loading}>
              Câu hỏi mới
            </button>
          </div>
          {checkpoint ? (
            <>
              <p className="lh-video-agent__prompt">{checkpoint.question.prompt}</p>
              <div className="lh-video-agent__options" role="radiogroup" aria-label="Các phương án trả lời">
                {checkpoint.question.options.map((option, index) => (
                  <button
                    type="button"
                    key={`${checkpoint.checkpoint_id}-${option}`}
                    role="radio"
                    aria-checked={selected === option}
                    className={selected === option ? 'is-selected' : ''}
                    onClick={() => setSelected(option)}
                    disabled={Boolean(grade)}
                  >
                    <span>{OPTION_LETTERS[index]}</span>{option}
                  </button>
                ))}
              </div>
              <button type="button" className="lhc-btn lhc-btn--outline" onClick={submitCheckpoint} disabled={!selected || loading || Boolean(grade)}>
                Gửi câu trả lời
              </button>
              {grade ? (
                <div className={`lh-video-agent__grade ${grade.passed ? 'is-correct' : 'is-wrong'}`} role="status">
                  <strong>{grade.passed ? '✓ Chính xác' : 'Chưa chính xác'} · {grade.score}/100</strong>
                  <p>{grade.feedback}</p>
                  <small>{grade.explanation}</small>
                </div>
              ) : null}
            </>
          ) : <p className="lh-video-agent__muted">Bấm “Câu hỏi mới” sau khi xem một đoạn video.</p>}
        </section>

        <section className="lh-video-agent__card">
          <div className="lh-video-agent__card-head"><div><span className="lh-video-agent__number">02</span><h4>Hỏi theo mốc đang xem</h4></div></div>
          <form onSubmit={ask}>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ví dụ: Vì sao dòng tiền quan trọng ở đoạn này?" maxLength={1000} rows={4} />
            <button type="submit" className="lhc-btn lhc-btn--primary" disabled={loading || !question.trim()}>Hỏi agent</button>
          </form>
          {answer ? (
            <div className="lh-video-agent__answer" role="status">
              <p>{answer.answer}</p>
              {answer.citations?.length ? <div className="lh-video-agent__citations">{answer.citations.map((citation) => <span key={citation.segment_id}>◷ {citation.label}</span>)}</div> : null}
              {answer.limitations?.map((limitation) => <small key={limitation}>⚠ {limitation}</small>)}
            </div>
          ) : null}
        </section>
      </div>

      {error ? <div className="lh-video-agent__error" role="alert">{error}</div> : null}
    </div>
  )
}
