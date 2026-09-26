import React from 'react'

/**
 * Format math/formula string into readable mathematical expression.
 * Cleanly transforms LaTeX \text{}, \frac{}, \times, etc.
 */
function formatMathFormula(raw) {
  let cleaned = raw.trim()
  if (cleaned.startsWith('$$') && cleaned.endsWith('$$')) {
    cleaned = cleaned.slice(2, -2).trim()
  } else if (cleaned.startsWith('\\[') && cleaned.endsWith('\\]')) {
    cleaned = cleaned.slice(2, -2).trim()
  }

  // Replace \text{XYZ} -> XYZ
  cleaned = cleaned.replace(/\\text\{([^}]+)\}/g, '$1')
  // Replace \times -> ×
  cleaned = cleaned.replace(/\\times/g, '×')
  // Replace \div -> ÷
  cleaned = cleaned.replace(/\\div/g, '÷')
  // Replace \frac{A}{B} -> (A) / (B) or A / B
  cleaned = cleaned.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1) / ($2)')
  // Remove trailing slashes or unescaped symbols
  cleaned = cleaned.replace(/\\([a-zA-Z]+)/g, '$1')

  return cleaned
}

/**
 * Render bold markdown **text** within inline strings.
 */
function renderInlineFormatting(text) {
  if (!text) return null
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={idx} className="lh-tutor-strong">
          {part.slice(2, -2)}
        </strong>
      )
    }
    // Inline math $...$
    if (part.startsWith('$') && part.endsWith('$') && part.length > 2) {
      return (
        <code key={idx} className="lh-tutor-inline-math">
          {formatMathFormula(part.slice(1, -1))}
        </code>
      )
    }
    return part
  })
}

/**
 * Pedagogical Tutor Message Parser & Renderer.
 * Eliminates raw markdown syntax (###, $$, **, >) and provides clean visual cards.
 */
export default function TutorMessageContent({ content }) {
  if (!content) return null

  // Split lines while preserving blocks
  const rawLines = content.split('\n')
  const elements = []
  let currentList = []
  let currentCallout = []

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list_${elements.length}`} className="lh-tutor-bullet-list">
          {currentList.map((item, i) => (
            <li key={i} className="lh-tutor-bullet-item">
              <span className="lh-tutor-bullet-dot">•</span>
              <span className="lh-tutor-bullet-text">{renderInlineFormatting(item)}</span>
            </li>
          ))}
        </ul>
      )
      currentList = []
    }
  }

  const flushCallout = () => {
    if (currentCallout.length > 0) {
      elements.push(
        <div key={`callout_${elements.length}`} className="lh-tutor-callout-card">
          <div className="lh-tutor-callout-icon">💡</div>
          <div className="lh-tutor-callout-body">
            {currentCallout.map((line, i) => (
              <p key={i} className="lh-tutor-callout-line">
                {renderInlineFormatting(line)}
              </p>
            ))}
          </div>
        </div>
      )
      currentCallout = []
    }
  }

  let idx = 0
  while (idx < rawLines.length) {
    const line = rawLines[idx].trim()

    // 1. Math block detection $$ ... $$
    if (line.startsWith('$$')) {
      flushList()
      flushCallout()

      let formulaText = line
      if (line === '$$' || (line.startsWith('$$') && !line.slice(2).includes('$$'))) {
        // Multi-line formula
        idx++
        while (idx < rawLines.length && !rawLines[idx].trim().endsWith('$$')) {
          formulaText += ' ' + rawLines[idx].trim()
          idx++
        }
        if (idx < rawLines.length) {
          formulaText += ' ' + rawLines[idx].trim()
        }
      }

      elements.push(
        <div key={`formula_${elements.length}`} className="lh-tutor-formula-box">
          <div className="lh-tutor-formula-header">
            <span className="lh-tutor-formula-badge">📐 CÔNG THỨC & NGUYÊN LÝ</span>
          </div>
          <div className="lh-tutor-formula-content">
            {formatMathFormula(formulaText)}
          </div>
        </div>
      )
      idx++
      continue
    }

    // 2. Callout quote > ...
    if (line.startsWith('>')) {
      flushList()
      currentCallout.push(line.replace(/^>\s*/, ''))
      idx++
      continue
    } else {
      flushCallout()
    }

    // 3. Headings ### or ##
    if (line.startsWith('###') || line.startsWith('##')) {
      flushList()
      const title = line.replace(/^#+\s*/, '')
      elements.push(
        <div key={`h_${elements.length}`} className="lh-tutor-section-heading">
          <span className="lh-tutor-heading-bar" />
          <h4 className="lh-tutor-heading-title">{renderInlineFormatting(title)}</h4>
        </div>
      )
      idx++
      continue
    }

    // 4. Horizontal dividers ---
    if (line === '---' || line === '***') {
      flushList()
      elements.push(<hr key={`hr_${elements.length}`} className="lh-tutor-divider" />)
      idx++
      continue
    }

    // 5. Bullet items * or - or 1.
    const isBullet = /^([*•-]|(\d+\.))\s+/.test(line)
    if (isBullet) {
      const cleanItem = line.replace(/^([*•-]|(\d+\.))\s+/, '')
      currentList.push(cleanItem)
      idx++
      continue
    } else {
      flushList()
    }

    // 6. Regular paragraph
    if (line.length > 0) {
      elements.push(
        <p key={`p_${elements.length}`} className="lh-tutor-paragraph">
          {renderInlineFormatting(line)}
        </p>
      )
    }

    idx++
  }

  flushList()
  flushCallout()

  return <div className="lh-tutor-formatted-content">{elements}</div>
}

