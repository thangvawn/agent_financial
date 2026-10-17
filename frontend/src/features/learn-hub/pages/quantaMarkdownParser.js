/**
 * Lightweight Markdown Block & Inline Parser for Quanta Docs (< 200 lines)
 */

export function parseQuantaBlocks(markdown) {
  if (!markdown) return []
  const lines = markdown.replace(/\r\n/g, '\n').split('\n')
  const blocks = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]
    const trimmed = line.trim()
    if (!trimmed) { i++; continue }

    if (trimmed.startsWith('```')) {
      const lang = trimmed.slice(3).trim()
      const codeLines = []
      i++
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++ // Skip closing ```
      blocks.push({ type: 'code', lang, content: codeLines.join('\n') })
      continue
    }

    if (trimmed.startsWith('|')) {
      const tableLines = []
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i].trim())
        i++
      }
      if (tableLines.length >= 2) {
        const parseRow = (r) => r.split('|').slice(1, -1).map((c) => c.trim())
        const headers = parseRow(tableLines[0])
        const rows = tableLines.slice(2).map(parseRow)
        blocks.push({ type: 'table', headers, rows })
        continue
      }
    }

    if (trimmed.startsWith('>')) {
      const quoteLines = []
      let isTip = false, isWarn = false
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        const qLine = lines[i].trim().replace(/^>\s?/, '')
        if (qLine.includes('[!TIP]')) isTip = true
        else if (qLine.includes('[!WARNING]')) isWarn = true
        else if (qLine) quoteLines.push(qLine)
        i++
      }
      blocks.push({
        type: 'callout',
        variant: isTip ? 'tip' : isWarn ? 'warn' : 'info',
        content: quoteLines.join(' '),
      })
      continue
    }

    if (trimmed.startsWith('## ')) {
      blocks.push({ type: 'h2', text: trimmed.slice(3).trim() })
      i++
      continue
    }
    if (trimmed.startsWith('### ')) {
      blocks.push({ type: 'h3', text: trimmed.slice(4).trim() })
      i++
      continue
    }

    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const items = []
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        items.push(lines[i].trim().slice(2).trim())
        i++
      }
      blocks.push({ type: 'ul', items })
      continue
    }

    if (/^\d+\.\s/.test(trimmed)) {
      const items = []
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s*/, '').trim())
        i++
      }
      blocks.push({ type: 'ol', items })
      continue
    }

    // Paragraph
    const paraLines = []
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('```') &&
      !lines[i].trim().startsWith('|') &&
      !lines[i].trim().startsWith('>') &&
      !lines[i].trim().startsWith('- ') &&
      !lines[i].trim().startsWith('* ') &&
      !/^\d+\.\s/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i].trim())
      i++
    }
    blocks.push({ type: 'p', text: paraLines.join(' ') })
  }

  return blocks
}
