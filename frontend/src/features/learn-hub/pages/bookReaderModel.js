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
