import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  createTutorConversation,
  getTutorConversation,
  sendTutorMessage,
  submitTutorFeedback,
} from '../services/aiTutorApi'
import TutorMessageContent from '../components/TutorMessageContent'
import './learn-tutor.css'

const QUICK_PROMPTS = [
  { label: '💡 Giải thích bài học', text: 'Giải thích giúp em nội dung và ví dụ của bài học này.' },
  { label: '🎯 Gợi ý làm quiz', text: 'Cho em gợi ý phương pháp giải câu hỏi trắc nghiệm (không lộ đáp án).' },
  { label: '📐 Công thức & tính toán', text: 'Phân tích công thức và ý nghĩa tài chính của bài học.' },
  { label: '🛡️ Rủi ro định lượng (VaR)', text: 'Tính toán chỉ số VaR 95% và CVaR 1 ngày của danh mục.' },
]

export default function LearnTutorPanel({ courseId, lessonId, sessionId, videoTimeSeconds }) {
  const contextKey = `${courseId || ''}:${lessonId || ''}:${sessionId || ''}`
  const [conversationsByContext, setConversationsByContext] = useState({})
  const [inputText, setInputText] = useState('')
  const [sendingByContext, setSendingByContext] = useState({})
  const [error, setError] = useState(null)
  const [lastFailedAction, setLastFailedAction] = useState(null)
  const [feedbackSent, setFeedbackSent] = useState({})
  const messagesEndRef = useRef(null)
  const initPromisesRef = useRef({})
  const contextKeyRef = useRef(contextKey)
  // Ref to read conversationsByContext inside callbacks without adding to deps
  const convByCtxRef = useRef(conversationsByContext)

  // Keep refs synced
  useEffect(() => {
    contextKeyRef.current = contextKey
  }, [contextKey])

  useEffect(() => {
    convByCtxRef.current = conversationsByContext
  }, [conversationsByContext])

  // Directly derive current context's state
  const activeConversation = conversationsByContext[contextKey]
  const messages = React.useMemo(() => activeConversation?.messages || [], [activeConversation?.messages])
  const conversationId = activeConversation?.conversationId || null
  const isSending = Boolean(sendingByContext[contextKey])
  const loading = Boolean(activeConversation?.isInitializing || isSending)

  const initConversation = useCallback(
    async (targetKey = contextKey) => {
      if (initPromisesRef.current[targetKey]) {
        return initPromisesRef.current[targetKey]
      }

      const promise = (async () => {
        try {
          setError(null)
          setLastFailedAction(null)
          setConversationsByContext((prev) => ({
            ...prev,
            [targetKey]: {
              ...(prev[targetKey] || { conversationId: null, messages: [] }),
              isInitializing: true,
            },
          }))

          // Read current state from ref to avoid stale closure
          let activeId = convByCtxRef.current[targetKey]?.conversationId

          if (activeId) {
            // Revalidate existing cached conversation with server
            try {
              const details = await getTutorConversation({
                sessionId,
                conversationId: activeId,
              })
              if (details?.messages) {
                setConversationsByContext((prev) => ({
                  ...prev,
                  [targetKey]: {
                    conversationId: activeId,
                    messages: details.messages,
                    isInitializing: false,
                  },
                }))
                return activeId
              }
            } catch {
              // Stale or deleted conversation -> invalidate and recreate
              activeId = null
            }
          }

          // Create or retrieve active session from server
          const conv = await createTutorConversation({
            sessionId,
            surface: 'learn',
            contextId: lessonId || courseId,
          })

          if (conv?.conversation_id) {
            const details = await getTutorConversation({
              sessionId,
              conversationId: conv.conversation_id,
            })
            setConversationsByContext((prev) => ({
              ...prev,
              [targetKey]: {
                conversationId: conv.conversation_id,
                messages: details?.messages || [],
                isInitializing: false,
              },
            }))
            return conv.conversation_id
          }

          setConversationsByContext((prev) => ({
            ...prev,
            [targetKey]: {
              ...(prev[targetKey] || { conversationId: null, messages: [] }),
              isInitializing: false,
            },
          }))
          return null
        } catch (err) {
          if (contextKeyRef.current === targetKey) {
            setError(err.message)
            setLastFailedAction({ type: 'init', targetKey })
          }
          setConversationsByContext((prev) => ({
            ...prev,
            [targetKey]: {
              ...(prev[targetKey] || { conversationId: null, messages: [] }),
              isInitializing: false,
            },
          }))
          return null
        } finally {
          // Only clear this key's promise — never affects other context keys
          if (initPromisesRef.current[targetKey] === promise) {
            delete initPromisesRef.current[targetKey]
          }
        }
      })()

      initPromisesRef.current[targetKey] = promise
      return promise
    },
    [courseId, lessonId, sessionId, contextKey]
  )

  // Initialize and revalidate conversation upon context switch
  useEffect(() => {
    initConversation(contextKey)
  }, [contextKey, initConversation])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSendMessage = async (textToSend) => {
    const currentKey = contextKey
    const text = (textToSend || inputText).trim()
    if (!text || loading) return

    // Read conversation ID from ref to avoid stale closure
    let activeConversationId = convByCtxRef.current[currentKey]?.conversationId
    if (!activeConversationId) {
      activeConversationId = await initConversation(currentKey)
      if (!activeConversationId) {
        return
      }
    }

    setInputText('')
    setError(null)
    setLastFailedAction(null)
    setSendingByContext((prev) => ({ ...prev, [currentKey]: true }))

    // Optimistic user message isolated to currentKey
    const tempUserMsg = {
      message_id: `temp_${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setConversationsByContext((prev) => {
      const existing = prev[currentKey] || { conversationId: activeConversationId, messages: [] }
      return {
        ...prev,
        [currentKey]: {
          ...existing,
          conversationId: activeConversationId,
          messages: [...existing.messages, tempUserMsg],
        },
      }
    })

    try {
      const resp = await sendTutorMessage({
        sessionId,
        conversationId: activeConversationId,
        content: text,
        surface: 'learn',
        currentSurfaceId: lessonId,
        videoTimeSeconds,
      })

      const asstMsg = {
        message_id: resp.message_id,
        role: 'assistant',
        content: resp.answer,
        citations: resp.citations || [],
        numeric_claims: resp.numeric_claims || [],
        limitations: resp.limitations || [],
        check_question: resp.check_question,
        next_action: resp.next_action,
        created_at: resp.created_at,
      }

      setConversationsByContext((prev) => {
        const existing = prev[currentKey] || { conversationId: activeConversationId, messages: [] }
        return {
          ...prev,
          [currentKey]: {
            ...existing,
            messages: [...existing.messages, asstMsg],
          },
        }
      })
    } catch (err) {
      if (contextKeyRef.current === currentKey) {
        setError(err.message)
        setLastFailedAction({ type: 'send', text })
        setInputText(text)
      }
    } finally {
      setSendingByContext((prev) => ({ ...prev, [currentKey]: false }))
    }
  }

  const handleRetry = () => {
    if (!lastFailedAction) return
    if (lastFailedAction.type === 'init') {
      initConversation(lastFailedAction.targetKey || contextKey)
    } else if (lastFailedAction.type === 'send') {
      handleSendMessage(lastFailedAction.text)
    }
  }

  const handleFeedback = async (messageId, rating) => {
    if (feedbackSent[messageId]) return
    try {
      await submitTutorFeedback({
        sessionId,
        messageId,
        conversationId,
        rating,
      })
      setFeedbackSent((prev) => ({ ...prev, [messageId]: rating }))
    } catch (err) {
      console.error('Feedback error:', err)
    }
  }

  return (
    <div className="lh-tutor-container" role="region" aria-label="Northstar AI Tutor">
      <div className="lh-tutor-header">
        <div className="lh-tutor-header__title">
          <span>🎓 Northstar AI Tutor</span>
          <span className="lh-tutor-header__badge">Learn & Quant</span>
        </div>
      </div>

      {error ? (
        <div className="lh-tutor-error" role="alert" aria-live="assertive" aria-atomic="true">
          <span>{error}</span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              type="button"
              className="lh-tutor-feedback__btn"
              onClick={handleRetry}
              aria-label="Thử lại tác vụ bị lỗi"
            >
              🔄 Thử lại
            </button>
            <button
              type="button"
              className="lh-tutor-feedback__btn"
              onClick={() => setError(null)}
              aria-label="Đóng thông báo lỗi"
            >
              Đóng
            </button>
          </div>
        </div>
      ) : null}

      <div className="lh-tutor-messages" tabIndex={0} aria-live="polite">
        {messages.length === 0 ? (
          <div className="lh-tutor-msg lh-tutor-msg--assistant">
            <div className="lh-tutor-msg__text">
              Chào anh! Em là <strong>Northstar AI Tutor</strong>. Anh có thể hỏi về khái niệm, công thức hoặc yêu cầu gợi
              ý bài học đang mở nhé.
            </div>
          </div>
        ) : null}

        {messages.map((msg) => (
          <div
            key={msg.message_id}
            className={`lh-tutor-msg ${msg.role === 'user' ? 'lh-tutor-msg--user' : 'lh-tutor-msg--assistant'}`}
          >
            <div className="lh-tutor-msg__text">
              {msg.role === 'assistant' ? (
                <TutorMessageContent content={msg.content} />
              ) : (
                msg.content
              )}
            </div>

            {msg.citations && msg.citations.length > 0 ? (
              <div className="lh-tutor-citations">
                <span>Trích dẫn nguồn:</span>
                <div>
                  {msg.citations.map((c, i) => (
                    <span key={i} className="lh-tutor-citations__item" title={c.content_version ? `Phiên bản: ${c.content_version}` : undefined}>
                      📚 {c.label || c.source_id} {c.content_version ? `(v${c.content_version})` : ''}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {msg.limitations && msg.limitations.length > 0 ? (
              <div className="lh-tutor-limitations" style={{ fontSize: '0.8rem', color: 'var(--text-muted, #888)', marginTop: '4px' }}>
                {msg.limitations.map((lim, i) => (
                  <div key={i}>⚠️ <em>{lim}</em></div>
                ))}
              </div>
            ) : null}

            {msg.check_question || msg.next_action ? (
              <div className="lh-tutor-meta">
                {msg.check_question ? <div className="lh-tutor-meta__q">❓ {msg.check_question}</div> : null}
                {msg.next_action ? <div className="lh-tutor-meta__act">👉 Bước tiếp theo: {msg.next_action}</div> : null}
              </div>
            ) : null}

            {msg.role === 'assistant' && !msg.message_id.startsWith('temp_') ? (
              <div className="lh-tutor-feedback">
                <span>Hữu ích?</span>
                <button
                  type="button"
                  className={`lh-tutor-feedback__btn ${feedbackSent[msg.message_id] === 'helpful' ? 'is-active' : ''}`}
                  onClick={() => handleFeedback(msg.message_id, 'helpful')}
                  disabled={!!feedbackSent[msg.message_id]}
                  aria-label="Đánh giá hữu ích"
                >
                  👍
                </button>
                <button
                  type="button"
                  className={`lh-tutor-feedback__btn ${feedbackSent[msg.message_id] === 'not_helpful' ? 'is-active' : ''}`}
                  onClick={() => handleFeedback(msg.message_id, 'not_helpful')}
                  disabled={!!feedbackSent[msg.message_id]}
                  aria-label="Đánh giá không hữu ích"
                >
                  👎
                </button>
              </div>
            ) : null}
          </div>
        ))}

        {loading ? (
          <div className="lh-tutor-msg lh-tutor-msg--assistant" role="status" aria-label="AI Tutor đang trả lời">
            <div className="lh-tutor-loading">
              <span />
              <span />
              <span />
            </div>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts */}
      <div className="lh-tutor-chips" role="group" aria-label="Gợi ý câu hỏi nhanh">
        {QUICK_PROMPTS.map((qp, idx) => (
          <button
            key={idx}
            type="button"
            className="lh-tutor-chip"
            onClick={() => handleSendMessage(qp.text)}
            disabled={loading}
          >
            {qp.label}
          </button>
        ))}
      </div>

      <form
        className="lh-tutor-input-bar"
        onSubmit={(e) => {
          e.preventDefault()
          handleSendMessage()
        }}
      >
        <input
          type="text"
          id="lh-tutor-input"
          aria-label="Câu hỏi cho AI Tutor"
          className="lh-tutor-input"
          placeholder="Hỏi AI Tutor về bài học, công thức hoặc rủi ro..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="lh-tutor-send-btn" disabled={loading || !inputText.trim()}>
          Gửi
        </button>
      </form>
    </div>
  )
}
