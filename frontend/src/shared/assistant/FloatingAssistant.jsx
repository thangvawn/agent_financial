import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { respondWithAssistant, synthesizeAssistantVoice } from './assistantApi'
import { trackAnalyticsEvent } from '../analytics/trackEvent'
import './floating-assistant.css'

export default function FloatingAssistant({ sessionId, surface, surfaceLabel }) {
  const [isOpen, setIsOpen] = useState(false)
  const [prompt, setPrompt] = useState(defaultPromptForSurface(surface))
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [voiceError, setVoiceError] = useState('')
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [draftTranscript, setDraftTranscript] = useState('')
  const threadEndRef = useRef(null)
  const inputRef = useRef(null)
  const recognitionRef = useRef(null)
  const audioRef = useRef(null)
  const voiceFinalTranscriptRef = useRef('')
  const voiceMergedTranscriptRef = useRef('')
  const voiceSubmitOnEndRef = useRef(true)

  const meta = useMemo(() => assistantMeta(surface), [surface])

  useEffect(() => {
    if (!isOpen) return
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [isOpen, messages, loading])

  useEffect(() => {
    if (!isOpen) return
    const timer = window.setTimeout(() => inputRef.current?.focus(), 160)
    return () => window.clearTimeout(timer)
  }, [isOpen])

  useEffect(() => {
    return () => {
      stopListening({ submitCurrent: false })
      stopSpeaking()
      window.speechSynthesis?.cancel?.()
    }
  }, [])

  async function submitPrompt(inputPrompt, inputMode = 'text') {
    if (!sessionId || !inputPrompt.trim()) return
    const userPrompt = inputPrompt.trim()
    const now = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    setMessages((current) => [
      ...current,
      {
        id: `u-${Date.now()}`,
        sender: 'user',
        title: 'Bạn',
        body: userPrompt,
        timestamp: now,
      },
    ])
    setPrompt('')
    setLoading(true)
    setError('')
    try {
      trackAnalyticsEvent({
        event_name: 'floating_assistant_prompt_submitted',
        module: 'ai_assistant',
        surface,
        session_id: sessionId,
        properties: { role_hint: meta.roleHint, prompt_length: userPrompt.length, input_mode: inputMode },
      })
      const payload = await respondWithAssistant({
        session_id: sessionId,
        surface,
        prompt: userPrompt,
        role_hint: meta.roleHint,
        conversation_id: conversationId || undefined,
        knowledge_level: meta.knowledgeLevel,
        trigger: meta.trigger,
        focus: meta.focus,
      })
      setConversationId(payload.conversation_id)
      setMessages((current) => [
        ...current,
        {
          id: payload.message_id,
          sender: 'assistant',
          title: payload.title,
          body: payload.explanation,
          summary: payload.summary,
          nextStep: payload.next_step,
          ctaPath: payload.cta_path,
          confidenceNote: payload.confidence_note,
          modeUsed: payload.mode_used || payload.role,
          intent: payload.intent,
          confidenceLabel: payload.confidence_label,
          dataFreshness: payload.data_freshness,
          warnings: payload.warnings || [],
          nextActions: payload.next_actions || [],
          learningSuggestions: payload.learning_suggestions || [],
          sources: payload.sources || [],
          timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
      if (voiceEnabled) {
        const speechText = [payload.summary, payload.next_step].filter(Boolean).join('. ')
        void speakAssistant(speechText || payload.explanation)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleAsk() {
    void submitPrompt(prompt, 'text')
  }

  function handleKeyDown(event) {
    if (event.key !== 'Enter' || event.shiftKey) return
    event.preventDefault()
    handleAsk()
  }

  function speechRecognitionConstructor() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null
  }

  function stopListening({ submitCurrent = false } = {}) {
    if (recognitionRef.current) {
      voiceSubmitOnEndRef.current = submitCurrent
      recognitionRef.current.stop()
    }
    setListening(false)
  }

  function stopSpeaking() {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }
    window.speechSynthesis?.cancel?.()
    setSpeaking(false)
  }

  async function startVoiceCapture() {
    if (!sessionId || loading) return
    const SpeechRecognitionCtor = speechRecognitionConstructor()
    if (!SpeechRecognitionCtor) {
      setVoiceError('Trình duyệt chưa hỗ trợ voice input realtime.')
      return
    }
    stopListening({ submitCurrent: false })
    setVoiceError('')
    voiceFinalTranscriptRef.current = ''
    voiceMergedTranscriptRef.current = ''
    voiceSubmitOnEndRef.current = true
    const recognition = new SpeechRecognitionCtor()
    recognition.lang = 'vi-VN'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setListening(true)
      setDraftTranscript('')
    }
    recognition.onresult = (event) => {
      let interimText = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const phrase = event.results[i][0]?.transcript || ''
        if (event.results[i].isFinal) {
          voiceFinalTranscriptRef.current = `${voiceFinalTranscriptRef.current} ${phrase}`.trim()
        } else {
          interimText += ` ${phrase}`
        }
      }
      const merged = `${voiceFinalTranscriptRef.current} ${interimText}`.trim()
      if (merged) {
        voiceMergedTranscriptRef.current = merged
        setDraftTranscript(merged)
        setPrompt(merged)
      }
    }
    recognition.onerror = (event) => {
      const reason = event?.error || 'unknown'
      setVoiceError(`Mic error: ${reason}`)
    }
    recognition.onend = () => {
      setListening(false)
      recognitionRef.current = null
      const finalPrompt = voiceFinalTranscriptRef.current.trim() || voiceMergedTranscriptRef.current.trim()
      const shouldSubmit = voiceSubmitOnEndRef.current
      voiceFinalTranscriptRef.current = ''
      voiceMergedTranscriptRef.current = ''
      voiceSubmitOnEndRef.current = true
      setDraftTranscript('')
      if (shouldSubmit && finalPrompt) {
        void submitPrompt(finalPrompt, 'voice')
      }
    }
    recognitionRef.current = recognition
    recognition.start()
  }

  function speakWithBrowser(text) {
    const synth = window.speechSynthesis
    if (!synth || !text.trim()) {
      setSpeaking(false)
      return
    }
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'vi-VN'
    utterance.rate = 1.02
    utterance.pitch = 1
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    synth.cancel()
    synth.speak(utterance)
  }

  async function speakAssistant(text) {
    if (!voiceEnabled || !text.trim() || !sessionId) return
    stopSpeaking()
    setVoiceError('')
    setSpeaking(true)
    try {
      const payload = await synthesizeAssistantVoice({
        text,
        session_id: sessionId,
        surface,
        role_hint: meta.roleHint,
      })
      if (payload.enabled && payload.audio_base64) {
        const audio = new Audio(`data:${payload.mime_type || 'audio/mpeg'};base64,${payload.audio_base64}`)
        audioRef.current = audio
        audio.onended = () => {
          setSpeaking(false)
          audioRef.current = null
        }
        audio.onerror = () => {
          setVoiceError('Không phát được audio từ ElevenLabs, chuyển sang voice local.')
          audioRef.current = null
          speakWithBrowser(text)
        }
        await audio.play()
        return
      }
      if (payload.fallback_reason) setVoiceError(payload.fallback_reason)
      speakWithBrowser(text)
    } catch (err) {
      setVoiceError(err.message || 'Không tạo được audio realtime.')
      speakWithBrowser(text)
    }
  }

  const assistantNode = (
    <div className={`floating-assistant ${isOpen ? 'floating-assistant--open' : ''}`}>
      {isOpen ? (
        <section className="floating-assistant__panel" role="dialog" aria-label="AI Assistant chat">
          <div className="floating-assistant__head">
            <div className="floating-assistant__head-copy">
              <div className="floating-assistant__meta">
                <span className="floating-assistant__role">{meta.shortLabel}</span>
                <span className="floating-assistant__status">
                  <span className="floating-assistant__status-dot" aria-hidden="true" />
                  Đang ở {surfaceLabel}
                </span>
              </div>
              <h2 className="floating-assistant__title">{meta.title}</h2>
            </div>
            <button type="button" className="floating-assistant__close" onClick={() => setIsOpen(false)} aria-label="Thu gọn chat">
              ×
            </button>
          </div>

          <div className="floating-assistant__trust-strip">
            <span>{roleLabel(meta.roleHint)}</span>
            <span>Education-first</span>
            <span>Không phải khuyến nghị cá nhân hóa</span>
          </div>

          <div className="floating-assistant__body">
            <div className="floating-assistant__thread" aria-live="polite">
              {!messages.length ? (
                <div className="floating-assistant__empty">
                  <div className="floating-assistant__empty-orb" aria-hidden="true" />
                  <h3>{sessionId ? 'Mình đang ở đây để đi cùng bạn.' : 'Hoàn tất onboarding để chat đầy đủ.'}</h3>
                  <p>{meta.description}</p>
                </div>
              ) : null}

              {messages.length
                ? messages.map((message) => (
                  <div
                    key={message.id}
                    className={`floating-assistant__message-row ${
                      message.sender === 'assistant' ? 'floating-assistant__message-row--assistant' : 'floating-assistant__message-row--user'
                    }`}
                  >
                    {message.sender === 'assistant' ? <span className="floating-assistant__avatar">AI</span> : null}
                    <article
                      className={`floating-assistant__message ${
                        message.sender === 'assistant' ? 'floating-assistant__message--assistant' : 'floating-assistant__message--user'
                      }`}
                    >
                      {message.sender === 'assistant' ? (
                        <div className="floating-assistant__message-head">
                          <strong>{message.title}</strong>
                          <span>{message.timestamp}</span>
                        </div>
                      ) : null}
                      {message.sender === 'assistant' ? (
                        <div className="floating-assistant__message-badges" aria-label="Trạng thái câu trả lời">
                          {message.modeUsed ? <span>{modeBadgeLabel(message.modeUsed)}</span> : null}
                          {message.confidenceLabel ? <span>{confidenceBadgeLabel(message.confidenceLabel)}</span> : null}
                          {message.dataFreshness ? <span>{freshnessBadgeLabel(message.dataFreshness)}</span> : null}
                        </div>
                      ) : null}
                      {message.warnings?.length && message.sender === 'assistant' ? (
                        <div className="floating-assistant__warning" role="note">
                          <strong>Lưu ý an toàn</strong>
                          <p>{message.warnings[0]}</p>
                        </div>
                      ) : null}
                      {message.summary && message.sender === 'assistant' ? (
                        <p className="floating-assistant__message-summary">{message.summary}</p>
                      ) : null}
                      <p className="floating-assistant__message-body">{message.body}</p>
                      {message.nextStep && message.sender === 'assistant' ? (
                        <div className="floating-assistant__next-step">
                          <span>Bước tiếp theo</span>
                          <p>{message.nextStep}</p>
                        </div>
                      ) : null}
                      {message.nextActions?.length && message.sender === 'assistant' ? (
                        <div className="floating-assistant__actions" aria-label="Hành động gợi ý">
                          {message.nextActions.slice(0, 2).map((action) => (
                            <a key={`${action.path}-${action.label}`} href={action.path} className="floating-assistant__action">
                              {action.label}
                            </a>
                          ))}
                        </div>
                      ) : null}
                      {message.learningSuggestions?.length && message.sender === 'assistant' ? (
                        <div className="floating-assistant__chips" aria-label="Bài học liên quan">
                          {message.learningSuggestions.slice(0, 2).map((lesson) => (
                            <span key={lesson}>Học: {lesson}</span>
                          ))}
                        </div>
                      ) : null}
                      {message.sources?.length && message.sender === 'assistant' ? (
                        <div className="floating-assistant__sources" aria-label="Nguồn ngữ cảnh">
                          {message.sources.slice(0, 3).map((source) => (
                            <span key={`${source.source_type}-${source.label}`}>
                              {source.label} · {source.freshness}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      {message.confidenceNote && message.sender === 'assistant' ? (
                        <p className="floating-assistant__fine-print">{message.confidenceNote}</p>
                      ) : null}
                      {message.sender === 'user' ? <span className="floating-assistant__timestamp">{message.timestamp}</span> : null}
                    </article>
                  </div>
                ))
                : null}

              {loading ? (
                <div className="floating-assistant__message-row floating-assistant__message-row--assistant">
                  <span className="floating-assistant__avatar">AI</span>
                  <article className="floating-assistant__message floating-assistant__message--assistant floating-assistant__typing">
                    <span />
                    <span />
                    <span />
                  </article>
                </div>
              ) : null}
              <div ref={threadEndRef} />
            </div>

            <div className="floating-assistant__suggestions">
              {meta.examples.map((example) => (
                <button
                  key={example}
                  type="button"
                  className="floating-assistant__suggestion"
                  onClick={() => setPrompt(example)}
                  disabled={!sessionId || loading}
                >
                  {example}
                </button>
              ))}
            </div>

            <div className="floating-assistant__composer">
              <div className="floating-assistant__composer-tools">
                <button
                  type="button"
                  className={`floating-assistant__voice-btn ${listening ? 'floating-assistant__voice-btn--live' : ''}`}
                  onClick={listening ? () => stopListening({ submitCurrent: true }) : () => void startVoiceCapture()}
                  disabled={!sessionId || loading}
                  aria-label={listening ? 'Dừng nghe và gửi' : 'Nói trực tiếp'}
                >
                  {listening ? 'Đang nghe… bấm để gửi' : 'Nói trực tiếp'}
                </button>
                <button
                  type="button"
                  className={`floating-assistant__voice-btn ${voiceEnabled ? '' : 'floating-assistant__voice-btn--off'}`}
                  onClick={() => {
                    if (voiceEnabled) stopSpeaking()
                    setVoiceEnabled((current) => !current)
                  }}
                  aria-label={voiceEnabled ? 'Tắt voice output' : 'Bật voice output'}
                >
                  {voiceEnabled ? (speaking ? 'Đang đọc…' : 'Voice bật') : 'Voice tắt'}
                </button>
                {speaking ? (
                  <button
                    type="button"
                    className="floating-assistant__voice-btn floating-assistant__voice-btn--danger"
                    onClick={stopSpeaking}
                    aria-label="Dừng phát audio"
                  >
                    Dừng đọc
                  </button>
                ) : null}
              </div>
              {draftTranscript ? (
                <p className="floating-assistant__voice-draft">{draftTranscript}</p>
              ) : null}
              <textarea
                ref={inputRef}
                rows={4}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={sessionId ? meta.placeholder : 'Hoàn tất onboarding để dùng assistant'}
                disabled={!sessionId || loading}
                aria-label="Nhập câu hỏi cho AI Assistant"
              />
              <button
                type="button"
                className="floating-assistant__send"
                onClick={handleAsk}
                disabled={!sessionId || loading || !prompt.trim()}
                aria-label={loading ? 'Đang trả lời' : 'Gửi câu hỏi'}
              >
                {loading ? '…' : '↑'}
              </button>
            </div>
            {voiceError ? <p className="floating-assistant__error">{voiceError}</p> : null}
            {error ? <p className="floating-assistant__error">{error}</p> : null}
          </div>
        </section>
      ) : null}

      <button
        type="button"
        className="floating-assistant__launcher"
        onClick={() => {
          setIsOpen((current) => !current)
          trackAnalyticsEvent({
            event_name: 'floating_assistant_toggled',
            module: 'ai_assistant',
            surface,
            session_id: sessionId || undefined,
            properties: { open: !isOpen, role_hint: meta.roleHint },
          })
        }}
      >
        <span className="floating-assistant__launcher-orb" aria-hidden="true">
          <span className="floating-assistant__launcher-orb-core" />
        </span>
        <span className="floating-assistant__launcher-text">
          <strong className="floating-assistant__launcher-copy">{meta.shortLabel}</strong>
          <span className="floating-assistant__launcher-subtitle">
            {sessionId ? 'Luôn sẵn sàng' : 'Cần onboarding'}
          </span>
        </span>
      </button>
    </div>
  )

  if (typeof document === 'undefined') return assistantNode
  return createPortal(assistantNode, document.body)
}

function roleLabel(roleHint) {
  if (roleHint === 'tutor') return 'Giải thích kiến thức và kiểm tra hiểu'
  if (roleHint === 'analyst') return 'Diễn giải insight, rủi ro và bối cảnh'
  if (roleHint === 'pro_assistant') return 'Hỗ trợ research có caveat'
  return 'Đẩy bước nhỏ tiếp theo trong app'
}

function modeBadgeLabel(mode) {
  if (mode === 'tutor') return 'Tutor mode'
  if (mode === 'coach') return 'Coach mode'
  if (mode === 'analyst') return 'Analyst mode'
  if (mode === 'pro_assistant') return 'Pro mode'
  return 'Assistant'
}

function confidenceBadgeLabel(label) {
  if (label === 'high') return 'Tin cậy cao'
  if (label === 'moderate') return 'Tin cậy vừa'
  if (label === 'limited_context') return 'Thiếu bối cảnh'
  if (label === 'guarded') return 'Đã chặn rủi ro'
  if (label === 'low_needs_clarification') return 'Cần hỏi thêm'
  return label
}

function freshnessBadgeLabel(label) {
  if (label === 'fresh') return 'Dữ liệu mới'
  if (label === 'stale') return 'Dữ liệu cũ'
  return `Freshness: ${label}`
}

function assistantMeta(surface) {
  if (surface === 'learning') {
    return {
      title: 'Tutor luôn sẵn sàng',
      shortLabel: 'Tutor',
      roleHint: 'tutor',
      description: 'Giải thích bài học, tóm tắt nhanh, và hỏi lại để bạn biết mình đã hiểu tới đâu.',
      placeholder: 'Ví dụ: Tóm tắt bài này như cho người mới bắt đầu.',
      examples: ['Tóm tắt bài này trong 3 dòng.', 'Giải thích khái niệm này như cho người mới.', 'Hỏi tôi 1 câu để kiểm tra hiểu.'],
      knowledgeLevel: 'beginner',
      trigger: 'floating_tutor',
      focus: 'lesson_understanding',
    }
  }
  if (surface === 'insights' || surface === 'guided_investing') {
    return {
      title: 'Analyst đang đi cùng bạn',
      shortLabel: 'Analyst',
      roleHint: 'analyst',
      description: 'Giải thích điều đang diễn ra, vì sao đáng quan tâm, và điều không nên overread từ dữ liệu hiện tại.',
      placeholder: 'Ví dụ: Điều gì đang thay đổi ở market context này?',
      examples: ['Điểm quan trọng nhất trong insight này là gì?', 'Rủi ro nào đang kéo bối cảnh đi lên?', 'Tôi không nên overread điều gì ở đây?'],
      knowledgeLevel: 'basic',
      trigger: 'floating_analyst',
      focus: 'market_context',
    }
  }
  if (surface === 'pro_lab' || surface === 'pro_lab_admin') {
    return {
      title: 'Pro Assistant luôn mở',
      shortLabel: 'Pro',
      roleHint: 'pro_assistant',
      description: 'Hỗ trợ đọc experiment, nhắc caveat, và giúp bạn đóng gói research thành câu hỏi tiếp theo.',
      placeholder: 'Ví dụ: Tóm tắt experiment này theo kiểu objective-assumption-caveat.',
      examples: ['Tóm tắt experiment này giúp tôi.', 'Caveat lớn nhất của report này là gì?', 'Nên kiểm tra thêm giả định nào?'],
      knowledgeLevel: 'intermediate',
      trigger: 'floating_pro_assistant',
      focus: 'research_workspace',
    }
  }
  return {
    title: 'Coach luôn ở đây',
    shortLabel: 'Coach',
    roleHint: 'coach',
    description: 'Nhắc một bước nhỏ tiếp theo trong app, giữ nhịp đều đặn và không ép bạn đi quá nhanh.',
    placeholder: 'Ví dụ: Bước nhỏ hợp lý nhất tôi nên làm tiếp là gì?',
    examples: ['Tôi nên làm bước gì tiếp theo?', 'Tôi đang bị kẹt, hãy gợi ý một bước nhỏ.', 'Nên ưu tiên Learn, Health hay Goals trước?'],
    knowledgeLevel: 'beginner',
    trigger: 'floating_coach',
    focus: 'next_step',
  }
}

function defaultPromptForSurface(surface) {
  return assistantMeta(surface).examples[0]
}
