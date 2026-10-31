export function readerStorageKey(sessionId, assetId) {
  return `learn-reader:${sessionId}:${assetId}`
}

export function createNotebookPage(seed = {}) {
  const uniqueId = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    ? crypto.randomUUID()
    : `page-${Date.now()}-${Math.random().toString(16).slice(2)}`
  return {
    id: typeof seed.id === 'string' && seed.id ? seed.id : uniqueId,
    title: typeof seed.title === 'string' && seed.title.trim() ? seed.title.trim() : '',
    noteText: typeof seed.noteText === 'string' ? seed.noteText : '',
    images: normalizeNoteImages(seed.images),
    drawingDataUrl: typeof seed.drawingDataUrl === 'string' && seed.drawingDataUrl.startsWith('data:image/')
      ? seed.drawingDataUrl
      : '',
    updatedAt: typeof seed.updatedAt === 'string' ? seed.updatedAt : new Date().toISOString(),
  }
}

export function hydrateNotebookPages(payload) {
  if (Array.isArray(payload?.pages) && payload.pages.length) {
    return payload.pages.map((page, index) => createNotebookPage({
      id: page?.id,
      title: page?.title || `Trang ${index + 1}`,
      noteText: page?.noteText,
      images: page?.images,
      drawingDataUrl: page?.drawingDataUrl,
      updatedAt: page?.updatedAt,
    }))
  }

  const legacyText = typeof payload?.noteText === 'string'
    ? payload.noteText
    : extractPlainTextFromHtml(payload?.noteHtml || '')
  const legacyImages = Array.isArray(payload?.images)
    ? normalizeNoteImages(payload.images)
    : extractImagesFromHtml(payload?.noteHtml || '')
  return [createNotebookPage({
    title: 'Trang 1',
    noteText: legacyText,
    images: legacyImages,
    drawingDataUrl: typeof payload?.drawingDataUrl === 'string' ? payload.drawingDataUrl : '',
    updatedAt: payload?.savedAt,
  })]
}

// The DOM supplies the fit measurement so wrapped lines use the actual paper width.
export function paginateNotebookText(text, fits) {
  if (!text || fits(text)) return [text]
  const letters = Array.from(text)
  const chunks = []
  let start = 0
  while (start < letters.length) {
    let low = 0
    let high = letters.length - start
    while (low < high) {
      const middle = Math.ceil((low + high) / 2)
      if (fits(letters.slice(start, start + middle).join(''))) low = middle
      else high = middle - 1
    }
    // A hidden/unmeasurable paper must never drop text or loop indefinitely.
    if (!low) { chunks.push(letters.slice(start).join('')); break }
    let end = start + low
    if (end < letters.length) {
      const minimum = start + Math.floor(low * .65)
      let boundary = -1
      // Prefer a complete line/paragraph, then a word boundary for wrapped prose.
      for (const separator of [/\n/u, /\s/u]) {
        for (let index = end - 1; index >= minimum; index--) {
          if (separator.test(letters[index])) { boundary = index + 1; break }
        }
        if (boundary > start) break
      }
      if (boundary > start) end = boundary
    }
    chunks.push(letters.slice(start, end).join(''))
    start = end
  }
  return chunks
}

export function continueNotebookText(pages, pageId, chunks) {
  const index = pages.findIndex(page => page.id === pageId)
  if (index < 0 || !chunks.length) return { pages, pageIds: [] }
  const updatedAt = new Date().toISOString()
  const continuation = [{ ...pages[index], noteText: chunks[0], updatedAt }]
  let nextIndex = index + 1
  let added = 0
  for (const noteText of chunks.slice(1)) {
    const next = pages[nextIndex]
    const empty = next && !next.noteText && !next.drawingDataUrl && !next.images?.length
    if (empty) {
      continuation.push({ ...next, noteText, updatedAt })
      nextIndex++
    } else {
      added++
      continuation.push(createNotebookPage({ title: `Trang ${pages.length + added}`, noteText }))
    }
  }
  return {
    pages: [...pages.slice(0, index), ...continuation, ...pages.slice(nextIndex)],
    pageIds: continuation.map(page => page.id),
  }
}

export function locateNotebookCaret(chunks, position) {
  let offset = Math.max(0, position)
  for (let index = 0; index < chunks.length; index++) {
    if (offset < chunks[index].length || index === chunks.length - 1) {
      return { index, offset: Math.min(offset, chunks[index].length) }
    }
    offset -= chunks[index].length
  }
  return { index: 0, offset: 0 }
}

export function safeJsonParse(value) {
  if (!value) return null
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

export async function fileToDataUrl(file) {
  if (!file) return ''
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
    reader.onerror = () => reject(new Error('Không đọc được ảnh'))
    reader.readAsDataURL(file)
  })
}

export function composeNoteHtml(noteText, images) {
  const escaped = escapeHtml(noteText).replace(/\n/g, '<br>')
  const imageBlocks = normalizeNoteImages(images)
    .map((image) => `<p><img src="${image.src}" alt="note-image" /></p>`)
    .join('')
  return `<p>${escaped || ''}</p>${imageBlocks}`
}

export function normalizeNoteImages(images) {
  if (!Array.isArray(images)) return []
  return images
    .map((item, index) => {
      if (typeof item === 'string' && item.startsWith('data:image/')) {
        return createNoteImage(item, index)
      }
      if (!item || typeof item !== 'object') return null
      const src = typeof item.src === 'string' ? item.src : ''
      if (!src.startsWith('data:image/')) return null
      return {
        src,
        x: clampNumber(item.x, 6, 70, 8 + (index % 3) * 8),
        y: clampNumber(item.y, 72, 1200, 112 + index * 28),
        width: clampNumber(item.width, 120, 520, 280),
      }
    })
    .filter(Boolean)
}

export function createNoteImage(src, index = 0) {
  return {
    src,
    x: 8 + (index % 3) * 8,
    y: 112 + index * 32,
    width: 300,
  }
}

function extractPlainTextFromHtml(html) {
  if (!html) return ''
  const container = document.createElement('div')
  container.innerHTML = html
  return container.textContent || ''
}

function extractImagesFromHtml(html) {
  if (!html) return []
  const container = document.createElement('div')
  container.innerHTML = html
  return Array.from(container.querySelectorAll('img'))
    .map((item) => item.getAttribute('src') || '')
    .filter((src) => src.startsWith('data:image/'))
    .map((src, index) => createNoteImage(src, index))
}

function clampNumber(value, min, max, fallback) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return fallback
  return Math.min(max, Math.max(min, numeric))
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function drawPersistedCanvas(dataUrl, canvas) {
  if (!canvas) return
  const context = canvas.getContext('2d')
  if (!context) return
  context.clearRect(0, 0, canvas.width, canvas.height)
  if (!dataUrl) return
  const image = new Image()
  image.onload = () => {
    context.clearRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
  }
  image.src = dataUrl
}

export function pointerPosition(event, canvas) {
  const rect = canvas.getBoundingClientRect()
  return {
    x: ((event.clientX - rect.left) / rect.width) * canvas.width,
    y: ((event.clientY - rect.top) / rect.height) * canvas.height,
  }
}
