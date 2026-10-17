import { useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Terminal,
} from 'lucide-react'
import { getAdjacentLessons, getQuantaLessonDetail } from '../content/quantaContentService'
import QuantaMarkdownRenderer from './QuantaMarkdownRenderer'
import QuantaLessonLabCta from './components/QuantaLessonLabCta'

export default function QuantaLessonReader({ lessonSlug, onSelectLesson, onGoHome }) {
  const [copied, setCopied] = useState(false)
  const [checkedItems, setCheckedItems] = useState({})
  const lesson = getQuantaLessonDetail(lessonSlug)
  const { prev, next } = getAdjacentLessons(lessonSlug)

  if (!lesson) {
    return (
      <div className="qd-reader-empty">
        <p>Không tìm thấy bài học này.</p>
        <button type="button" className="qd-btn qd-btn--primary" onClick={onGoHome}>
          Về trang chủ Quanta Docs
        </button>
      </div>
    )
  }

  function handleCopy(text) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }).catch(() => {})
  }

  function toggleCheck(idx) {
    setCheckedItems((prev) => ({ ...prev, [idx]: !prev[idx] }))
  }

  return (
    <div className="qd-reader-container thin-scrollbar">
      {/* Breadcrumbs */}
      <nav className="qd-breadcrumbs" aria-label="Breadcrumbs">
        <button type="button" className="qd-bc-link" onClick={onGoHome}>Quanta Docs</button>
        <span className="qd-bc-sep">/</span>
        <span className="qd-bc-sec">{lesson.sectionTitle}</span>
        <span className="qd-bc-sep">/</span>
        <span className="qd-bc-current">{lesson.title}</span>
      </nav>

      {/* Lesson Header Card */}
      <header className="qd-lesson-header">
        <div className="qd-meta-row">
          <span className={`qd-level-badge qd-level--${lesson.level === 'Cơ bản' ? 'basic' : lesson.level === 'Trung bình' ? 'mid' : 'adv'}`}>
            {lesson.level}
          </span>
          <span className="qd-time-badge">
            <Clock size={12} /> {lesson.estimated_min} phút
          </span>
        </div>
        <h1 className="qd-lesson-h1">{lesson.title}</h1>
        <p className="qd-lesson-sub">{lesson.subtitle}</p>
      </header>

      {/* Checklist mục tiêu bài học */}
      {Array.isArray(lesson.checklist) && lesson.checklist.length > 0 && (
        <section className="qd-checklist-box">
          <h2 className="qd-checklist-title">
            <CheckCircle2 size={16} className="text-cyan-300" />
            Mục tiêu cần nắm vững:
          </h2>
          <ul className="qd-check-items">
            {lesson.checklist.map((item, idx) => (
              <li key={idx} className="qd-check-item">
                <button
                  type="button"
                  className={`qd-check-btn ${checkedItems[idx] ? 'is-checked' : ''}`}
                  onClick={() => toggleCheck(idx)}
                >
                  <span className="qd-check-box">{checkedItems[idx] ? '✓' : ''}</span>
                  <span className="qd-check-text">{item}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Demo Code Block nếu có */}
      {lesson.demo_code && (
        <section className="qd-code-section">
          <div className="qd-code-header">
            <div className="qd-code-lang">
              <Terminal size={13} className="text-cyan-400" />
              <span>quanta story code</span>
            </div>
            <button
              type="button"
              className="qd-code-btn"
              onClick={() => handleCopy(lesson.demo_code)}
            >
              {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              <span>{copied ? 'Đã chép' : 'Sao chép code'}</span>
            </button>
          </div>
          <pre className="qd-code-pre thin-scrollbar">
            <code>{lesson.demo_code}</code>
          </pre>
        </section>
      )}

      {/* Lesson Body Markdown text */}
      <article className="qd-article-body">
        <QuantaMarkdownRenderer content={lesson.body} />
      </article>

      {/* 1-Click Action Bridge to Simulation Lab */}
      <QuantaLessonLabCta lessonTitle={lesson.title} demoCode={lesson.demo_code} />

      {/* Prev / Next Footer Navigation */}
      <footer className="qd-reader-footer">
        {prev ? (
          <button
            type="button"
            className="qd-nav-btn qd-nav-btn--prev"
            onClick={() => onSelectLesson(prev.slug)}
          >
            <ArrowLeft size={15} />
            <div className="qd-nav-label">
              <span>Bài trước</span>
              <strong>{prev.title}</strong>
            </div>
          </button>
        ) : <div />}

        {next ? (
          <button
            type="button"
            className="qd-nav-btn qd-nav-btn--next"
            onClick={() => onSelectLesson(next.slug)}
          >
            <div className="qd-nav-label text-right">
              <span>Bài tiếp theo</span>
              <strong>{next.title}</strong>
            </div>
            <ArrowRight size={15} />
          </button>
        ) : null}
      </footer>
    </div>
  )
}
