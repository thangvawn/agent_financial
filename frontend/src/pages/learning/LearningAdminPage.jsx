import { useEffect, useMemo, useState } from 'react'

import {
  fetchLearningCmsDocument,
  fetchLearningCmsStatus,
  listLearningCmsDocuments,
  upsertLearningCmsDocument,
} from '../../modules/learning-admin'
import './learning.css'

const DOC_TYPE_CONFIG = {
  lessons: {
    label: 'Lessons',
    idField: 'lesson_id',
    emptyState: createEmptyLesson,
  },
  courses: {
    label: 'Courses',
    idField: 'course_id',
    emptyState: createEmptyCourse,
  },
  paths: {
    label: 'Paths',
    idField: 'path_id',
    emptyState: createEmptyPath,
  },
}

export default function LearningAdminPage({ onBack, onOpenContentOps }) {
  const [adminKeyInput, setAdminKeyInput] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [docType, setDocType] = useState('lessons')
  const [status, setStatus] = useState(null)
  const [documents, setDocuments] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [form, setForm] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const selectedConfig = DOC_TYPE_CONFIG[docType]

  useEffect(() => {
    const savedKey = window.localStorage.getItem('learning-cms.admin_key') || ''
    if (savedKey) {
      setAdminKey(savedKey)
      setAdminKeyInput(savedKey)
    }
  }, [])

  useEffect(() => {
    if (!adminKey) return
    let cancelled = false

    async function run() {
      setIsLoading(true)
      setError('')
      try {
        const [statusPayload, docsPayload] = await Promise.all([
          fetchLearningCmsStatus(adminKey),
          listLearningCmsDocuments(docType, adminKey),
        ])
        if (cancelled) return
        setStatus(statusPayload)
        setDocuments(docsPayload)
        if (!selectedId && docsPayload.length) {
          const nextId = docsPayload[0][DOC_TYPE_CONFIG[docType].idField]
          setSelectedId(nextId)
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [adminKey, docType])

  useEffect(() => {
    if (!adminKey || !selectedId) return
    if (!documents.some((item) => item[selectedConfig.idField] === selectedId) && form?.source === 'draft') return
    let cancelled = false

    async function run() {
      setIsLoading(true)
      setError('')
      setMessage('')
      try {
        const payload = await fetchLearningCmsDocument(docType, selectedId, adminKey)
        if (cancelled) return
        setForm(mapDocumentToForm(docType, payload))
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [adminKey, docType, documents, form?.source, selectedConfig.idField, selectedId])

  const selectedDoc = useMemo(
    () => documents.find((item) => item[selectedConfig.idField] === selectedId) || null,
    [documents, selectedConfig.idField, selectedId],
  )

  function handleConnect() {
    setError('')
    setMessage('')
    if (!adminKeyInput.trim()) {
      setError('Nhập admin key để mở CMS.')
      return
    }
    window.localStorage.setItem('learning-cms.admin_key', adminKeyInput.trim())
    setAdminKey(adminKeyInput.trim())
  }

  function handleNewDocument() {
    const empty = selectedConfig.emptyState()
    setSelectedId(empty[selectedConfig.idField])
    setForm(empty)
    setMessage('Đang tạo bản nháp mới. Hãy chỉnh ID trước khi lưu nếu cần.')
    setError('')
  }

  async function handleSave() {
    if (!adminKey || !form) return
    setError('')
    setMessage('')
    try {
      const docId = form[selectedConfig.idField]
      const payload = mapFormToPayload(docType, form)
      const saved = await upsertLearningCmsDocument(docType, docId, payload, adminKey)
      setMessage(`${selectedConfig.label.slice(0, -1)} đã được lưu với trạng thái ${saved.doc_status}.`)
      const docsPayload = await listLearningCmsDocuments(docType, adminKey)
      setDocuments(docsPayload)
      setSelectedId(saved[selectedConfig.idField])
      setForm(mapDocumentToForm(docType, saved))
    } catch (err) {
      setError(err.message)
    }
  }

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  return (
    <section>
      <h1>Learning CMS Admin</h1>
      <p>Đây là giao diện legacy chỉ nên dùng cho override cũ của Learn Hub. Đường admin chính cho nội dung mới là Content Ops.</p>

      {onBack ? (
        <button type="button" onClick={onBack}>
          Quay lại Learn Hub
        </button>
      ) : null}
      {onOpenContentOps ? (
        <button type="button" onClick={onOpenContentOps}>
          Mở Content Ops Admin (khuyến nghị)
        </button>
      ) : null}

      <section>
        <h2>Kết nối Admin</h2>
        <input
          type="password"
          placeholder="ADMIN_LEARNING_CMS_KEY"
          value={adminKeyInput}
          onChange={(e) => setAdminKeyInput(e.target.value)}
        />
        <button type="button" onClick={handleConnect}>
          Mở CMS
        </button>
        {status ? (
          <p>
            Catalog hiện có {status.lesson_count} lessons, {status.course_count} courses, {status.path_count} paths,
            và {status.override_count} override.
          </p>
        ) : null}
      </section>

      {!adminKey ? null : (
        <section>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
            {Object.entries(DOC_TYPE_CONFIG).map(([key, value]) => (
              <button
                key={key}
                type="button"
                onClick={() => {
                  setDocType(key)
                  setSelectedId('')
                  setForm(null)
                  setMessage('')
                }}
                style={{ fontWeight: docType === key ? 700 : 400 }}
              >
                {value.label}
              </button>
            ))}
            <button type="button" onClick={handleNewDocument} disabled>
              Tạo draft mới
            </button>
          </div>

          <p>Legacy mode: giao diện này chỉ còn để xem override cũ. Các thao tác lưu mới đã được chuyển sang Content Ops.</p>

          {error ? <p>{error}</p> : null}
          {message ? <p>{message}</p> : null}
          {isLoading ? <p>Đang tải CMS...</p> : null}

          <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16 }}>
            <aside>
              <h3>{selectedConfig.label}</h3>
              <ul style={{ paddingLeft: 18 }}>
                {documents.map((item) => {
                  const itemId = item[selectedConfig.idField]
                  return (
                    <li key={itemId}>
                      <button type="button" onClick={() => setSelectedId(itemId)}>
                        {item.title} ({item.doc_status})
                      </button>
                    </li>
                  )
                })}
              </ul>
            </aside>

            <article>
              {!form ? (
                <p>Chọn một document để sửa.</p>
              ) : (
                <div style={{ display: 'grid', gap: 12 }}>
                  <p>
                    Source: {selectedDoc?.source || form.source || 'draft'} · Status hiện tại: {selectedDoc?.doc_status || form.status}
                  </p>
                  {renderForm(docType, form, updateField, true)}
                  <button type="button" onClick={handleSave} disabled>
                    Lưu document
                  </button>
                </div>
              )}
            </article>
          </div>
        </section>
      )}
    </section>
  )
}

function renderForm(docType, form, updateField, disabled = false) {
  if (docType === 'lessons') {
    return (
      <>
        <label>
          Lesson ID
          <input disabled={disabled} value={form.lesson_id} onChange={(e) => updateField('lesson_id', e.target.value)} />
        </label>
        <label>
          Title
          <input disabled={disabled} value={form.title} onChange={(e) => updateField('title', e.target.value)} />
        </label>
        <label>
          Summary
          <textarea disabled={disabled} value={form.summary} onChange={(e) => updateField('summary', e.target.value)} rows={3} />
        </label>
        <label>
          Tier
          <input disabled={disabled} value={form.tier} onChange={(e) => updateField('tier', e.target.value)} />
        </label>
        <label>
          Content type
          <input disabled={disabled} value={form.content_type} onChange={(e) => updateField('content_type', e.target.value)} />
        </label>
        <label>
          Estimated minutes
          <input
            type="number"
            disabled={disabled}
            value={form.estimated_minutes}
            onChange={(e) => updateField('estimated_minutes', Number(e.target.value))}
          />
        </label>
        <label>
          Body (mỗi dòng là một block)
          <textarea disabled={disabled} value={form.bodyText} onChange={(e) => updateField('bodyText', e.target.value)} rows={8} />
        </label>
        <label>
          Glossary (mỗi dòng: term | definition)
          <textarea disabled={disabled} value={form.glossaryText} onChange={(e) => updateField('glossaryText', e.target.value)} rows={6} />
        </label>
        <label>
          Quiz (JSON array)
          <textarea disabled={disabled} value={form.quizText} onChange={(e) => updateField('quizText', e.target.value)} rows={10} />
        </label>
        <label>
          Next lesson id
          <input disabled={disabled} value={form.next_lesson_id} onChange={(e) => updateField('next_lesson_id', e.target.value)} />
        </label>
        <label>
          Status
          <select disabled={disabled} value={form.status} onChange={(e) => updateField('status', e.target.value)}>
            <option value="draft">draft</option>
            <option value="published">published</option>
          </select>
        </label>
      </>
    )
  }

  if (docType === 'courses') {
    return (
      <>
        <label>
          Course ID
          <input disabled={disabled} value={form.course_id} onChange={(e) => updateField('course_id', e.target.value)} />
        </label>
        <label>
          Title
          <input disabled={disabled} value={form.title} onChange={(e) => updateField('title', e.target.value)} />
        </label>
        <label>
          Description
          <textarea disabled={disabled} value={form.description} onChange={(e) => updateField('description', e.target.value)} rows={4} />
        </label>
        <label>
          Tier
          <input disabled={disabled} value={form.tier} onChange={(e) => updateField('tier', e.target.value)} />
        </label>
        <label>
          Lesson IDs (mỗi dòng một ID)
          <textarea disabled={disabled} value={form.lessonIdsText} onChange={(e) => updateField('lessonIdsText', e.target.value)} rows={6} />
        </label>
        <label>
          Status
          <select disabled={disabled} value={form.status} onChange={(e) => updateField('status', e.target.value)}>
            <option value="draft">draft</option>
            <option value="published">published</option>
          </select>
        </label>
      </>
    )
  }

  return (
    <>
      <label>
        Path ID
        <input disabled={disabled} value={form.path_id} onChange={(e) => updateField('path_id', e.target.value)} />
      </label>
      <label>
        Title
        <input disabled={disabled} value={form.title} onChange={(e) => updateField('title', e.target.value)} />
      </label>
      <label>
        Persona segment
        <input disabled={disabled} value={form.persona_segment} onChange={(e) => updateField('persona_segment', e.target.value)} />
      </label>
      <label>
        Description
        <textarea disabled={disabled} value={form.description} onChange={(e) => updateField('description', e.target.value)} rows={4} />
      </label>
      <label>
        Lesson IDs (mỗi dòng một ID)
        <textarea disabled={disabled} value={form.lessonIdsText} onChange={(e) => updateField('lessonIdsText', e.target.value)} rows={6} />
      </label>
      <label>
        Status
        <select disabled={disabled} value={form.status} onChange={(e) => updateField('status', e.target.value)}>
          <option value="draft">draft</option>
          <option value="published">published</option>
        </select>
      </label>
    </>
  )
}

function mapDocumentToForm(docType, payload) {
  if (docType === 'lessons') {
    return {
      lesson_id: payload.lesson_id,
      title: payload.title,
      summary: payload.summary,
      tier: payload.tier,
      content_type: payload.content_type,
      estimated_minutes: payload.estimated_minutes,
      bodyText: (payload.body || []).join('\n'),
      glossaryText: (payload.glossary || []).map((item) => `${item.term} | ${item.definition}`).join('\n'),
      quizText: JSON.stringify(payload.quiz_questions || [], null, 2),
      next_lesson_id: payload.next_lesson_id || '',
      status: payload.doc_status || 'draft',
      source: payload.source,
    }
  }

  if (docType === 'courses') {
    return {
      course_id: payload.course_id,
      title: payload.title,
      description: payload.description,
      tier: payload.tier,
      lessonIdsText: (payload.lesson_ids || []).join('\n'),
      status: payload.doc_status || 'draft',
      source: payload.source,
    }
  }

  return {
    path_id: payload.path_id,
    title: payload.title,
    persona_segment: payload.persona_segment,
    description: payload.description,
    lessonIdsText: (payload.lesson_ids || []).join('\n'),
    status: payload.doc_status || 'draft',
    source: payload.source,
  }
}

function mapFormToPayload(docType, form) {
  if (docType === 'lessons') {
    return {
      title: form.title.trim(),
      summary: form.summary.trim(),
      tier: form.tier.trim(),
      content_type: form.content_type.trim(),
      estimated_minutes: Number(form.estimated_minutes || 1),
      body: splitLines(form.bodyText),
      glossary: parseGlossary(form.glossaryText),
      quiz_questions: parseQuiz(form.quizText),
      next_lesson_id: form.next_lesson_id.trim() || null,
      status: form.status,
    }
  }

  if (docType === 'courses') {
    return {
      title: form.title.trim(),
      description: form.description.trim(),
      tier: form.tier.trim(),
      lesson_ids: splitLines(form.lessonIdsText),
      status: form.status,
    }
  }

  return {
    title: form.title.trim(),
    persona_segment: form.persona_segment.trim(),
    description: form.description.trim(),
    lesson_ids: splitLines(form.lessonIdsText),
    status: form.status,
  }
}

function splitLines(value) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function parseGlossary(value) {
  return splitLines(value).map((line) => {
    const [term, ...definition] = line.split('|')
    return {
      term: (term || '').trim(),
      definition: definition.join('|').trim(),
    }
  })
}

function parseQuiz(value) {
  const parsed = JSON.parse(value || '[]')
  if (!Array.isArray(parsed)) return []
  return parsed
}

function createEmptyLesson() {
  return {
    lesson_id: `draft-lesson-${Date.now()}`,
    title: 'Lesson mới',
    summary: 'Tóm tắt ngắn cho lesson mới.',
    tier: 'financial_basics',
    content_type: 'micro_lesson',
    estimated_minutes: 4,
    bodyText: 'Block 1',
    glossaryText: 'Cash flow | Dong tien vao va ra',
    quizText: JSON.stringify(
      [
        {
          question_id: 'q1',
          prompt: 'Cau hoi mau',
          options: ['Lua chon 1', 'Lua chon 2'],
          correct_answer: 'Lua chon 1',
          explanation: 'Giai thich ngan',
        },
      ],
      null,
      2,
    ),
    next_lesson_id: '',
    status: 'draft',
    source: 'draft',
  }
}

function createEmptyCourse() {
  return {
    course_id: `draft-course-${Date.now()}`,
    title: 'Course mới',
    description: 'Mo ta ngan cho course moi.',
    tier: 'financial_basics',
    lessonIdsText: 'money-basics-101',
    status: 'draft',
    source: 'draft',
  }
}

function createEmptyPath() {
  return {
    path_id: `draft-path-${Date.now()}`,
    title: 'Path mới',
    persona_segment: 'starter',
    description: 'Mo ta ngan cho path moi.',
    lessonIdsText: 'money-basics-101',
    status: 'draft',
    source: 'draft',
  }
}
