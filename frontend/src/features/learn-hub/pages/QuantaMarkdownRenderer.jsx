import { Info, Lightbulb, AlertTriangle, Terminal } from 'lucide-react'
import { parseQuantaBlocks } from './quantaMarkdownParser'

function renderInline(text) {
  if (!text) return null
  const tokens = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/)
    const codeMatch = remaining.match(/`([^`]+)`/)
    const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/)

    const matches = [
      boldMatch ? { type: 'bold', index: boldMatch.index, len: boldMatch[0].length, val: boldMatch[1] } : null,
      codeMatch ? { type: 'code', index: codeMatch.index, len: codeMatch[0].length, val: codeMatch[1] } : null,
      italicMatch ? { type: 'italic', index: italicMatch.index, len: italicMatch[0].length, val: italicMatch[1] } : null,
    ].filter(Boolean)

    if (matches.length === 0) {
      tokens.push(remaining)
      break
    }

    matches.sort((a, b) => a.index - b.index)
    const first = matches[0]

    if (first.index > 0) tokens.push(remaining.slice(0, first.index))

    if (first.type === 'bold') {
      tokens.push(<strong key={key++} className="qd-strong">{first.val}</strong>)
    } else if (first.type === 'code') {
      tokens.push(<code key={key++} className="qd-inline-code">{first.val}</code>)
    } else if (first.type === 'italic') {
      tokens.push(<em key={key++} className="text-sky-300 italic">{first.val}</em>)
    }

    remaining = remaining.slice(first.index + first.len)
  }

  return tokens
}

export default function QuantaMarkdownRenderer({ content }) {
  const blocks = parseQuantaBlocks(content)

  return (
    <div className="qd-article-flow">
      {blocks.map((block, idx) => {
        if (block.type === 'h2') return <h2 key={idx} className="qd-h2">{renderInline(block.text)}</h2>
        if (block.type === 'h3') return <h3 key={idx} className="qd-h3">{renderInline(block.text)}</h3>
        if (block.type === 'p') return <p key={idx} className="qd-p">{renderInline(block.text)}</p>
        if (block.type === 'ul') {
          return (
            <ul key={idx} className="qd-ul">
              {block.items.map((it, iIdx) => <li key={iIdx}>{renderInline(it)}</li>)}
            </ul>
          )
        }
        if (block.type === 'ol') {
          return (
            <ol key={idx} className="qd-ol">
              {block.items.map((it, iIdx) => <li key={iIdx}>{renderInline(it)}</li>)}
            </ol>
          )
        }
        if (block.type === 'code') {
          return (
            <div key={idx} className="qd-code-section my-3">
              {block.lang && (
                <div className="qd-code-header">
                  <div className="qd-code-lang">
                    <Terminal size={12} className="text-cyan-400" />
                    <span>{block.lang}</span>
                  </div>
                </div>
              )}
              <pre className="qd-code-pre thin-scrollbar"><code>{block.content}</code></pre>
            </div>
          )
        }
        if (block.type === 'table') {
          return (
            <div key={idx} className="qd-table-wrap">
              <table className="qd-table">
                <thead>
                  <tr>{block.headers.map((h, hIdx) => <th key={hIdx}>{renderInline(h)}</th>)}</tr>
                </thead>
                <tbody>
                  {block.rows.map((row, rIdx) => (
                    <tr key={rIdx}>{row.map((c, cIdx) => <td key={cIdx}>{renderInline(c)}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        }
        if (block.type === 'callout') {
          return (
            <aside key={idx} className={`qd-callout qd-callout--${block.variant}`}>
              <div className="qd-callout-title">
                {block.variant === 'tip' ? <Lightbulb size={14} /> : block.variant === 'warn' ? <AlertTriangle size={14} /> : <Info size={14} />}
                <span>{block.variant === 'tip' ? 'Mẹo thực tế' : block.variant === 'warn' ? 'Lưu ý' : 'Thông tin'}</span>
              </div>
              <p className="qd-callout-text">{renderInline(block.content)}</p>
            </aside>
          )
        }
        return null
      })}
    </div>
  )
}
