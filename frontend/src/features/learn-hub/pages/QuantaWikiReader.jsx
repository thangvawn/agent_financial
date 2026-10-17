import { useState } from 'react'
import { Check, Copy, Hash, Terminal } from 'lucide-react'
import {
  WIKI_FUNCTION_GROUPS,
  WIKI_FUNCTIONS,
  WIKI_NAMESPACES,
} from '../content/quantaWikiData'

export default function QuantaWikiReader({ fnName, onSelectFn, onGoHome }) {
  const [copied, setCopied] = useState(false)
  const fnDetail = WIKI_FUNCTIONS[fnName]
  const nsDetail = WIKI_NAMESPACES.find((n) => n.name === fnName)

  let group = null
  for (const g of WIKI_FUNCTION_GROUPS) {
    if (g.items.includes(fnName)) {
      group = g
      break
    }
  }

  function handleCopy(text) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }).catch(() => {})
  }

  return (
    <div className="qd-reader-container thin-scrollbar">
      {/* Breadcrumbs */}
      <nav className="qd-breadcrumbs" aria-label="Breadcrumbs">
        <button type="button" className="qd-bc-link" onClick={onGoHome}>Quanta Docs</button>
        <span className="qd-bc-sep">/</span>
        <span className="qd-bc-sec">Wiki</span>
        <span className="qd-bc-sep">/</span>
        <span className="qd-bc-sec">{group ? group.title : 'Namespace'}</span>
        <span className="qd-bc-sep">/</span>
        <span className="qd-bc-current font-mono">{fnName}</span>
      </nav>

      {/* Header card */}
      <header className="qd-lesson-header">
        <div className="qd-meta-row">
          <span className="qd-level-badge qd-level--basic">
            {nsDetail ? 'Namespace' : 'Hàm Built-in'}
          </span>
          {group && <span className="qd-badge qd-badge--cyan">{group.title}</span>}
        </div>
        <h1 className="qd-lesson-h1 font-mono text-cyan-200">
          {fnDetail ? fnDetail.sig : fnName}
        </h1>
        <p className="qd-lesson-sub">
          {fnDetail ? fnDetail.desc : nsDetail?.desc}
        </p>
      </header>

      {/* Signature Code Box */}
      {fnDetail && (
        <section className="qd-code-section">
          <div className="qd-code-header">
            <div className="qd-code-lang">
              <Terminal size={13} className="text-cyan-400" />
              <span>Cú pháp & Ví dụ</span>
            </div>
            <button
              type="button"
              className="qd-code-btn"
              onClick={() => handleCopy(fnDetail.ex)}
            >
              {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              <span>{copied ? 'Đã chép' : 'Sao chép ví dụ'}</span>
            </button>
          </div>
          <pre className="qd-code-pre thin-scrollbar">
            <code>{fnDetail.ex}</code>
          </pre>
        </section>
      )}

      {/* Namespace members nếu là namespace */}
      {nsDetail && (
        <section className="qd-checklist-box">
          <h2 className="qd-checklist-title">
            <Hash size={16} className="text-cyan-300" />
            Mô tả Namespace {nsDetail.name}
          </h2>
          <p className="qd-p" style={{ marginTop: '0.5rem' }}>{nsDetail.desc}</p>
        </section>
      )}

      {/* Related Functions in the same group */}
      {group && (
        <section className="qd-related-box">
          <h3 className="qd-curr-title" style={{ marginBottom: '0.75rem' }}>
            Các hàm khác thuộc {group.title}:
          </h3>
          <div className="qd-wiki-pill-grid">
            {group.items.map((sibling) => (
              <button
                key={sibling}
                type="button"
                className={`qd-fn-tag ${sibling === fnName ? 'is-active' : ''}`}
                onClick={() => onSelectFn(sibling)}
              >
                {sibling}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
