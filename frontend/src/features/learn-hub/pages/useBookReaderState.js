import { useEffect, useRef, useState } from 'react'
import {
  composeNoteHtml,
  createNoteImage,
  createNotebookPage,
  fileToDataUrl,
  hydrateNotebookPages,
  normalizeNoteImages,
  readerStorageKey,
  safeJsonParse,
} from './bookReaderModel'

export function useBookReaderState({ book, sessionId }) {
  const uploadInputRef = useRef(null)
  const pageElementRefs = useRef(new Map())
  const pageBadgeTimerRef = useRef(null)

  const [pages, setPages] = useState(() => [createNotebookPage({ title: 'Trang 1' })])
  const [activePageId, setActivePageId] = useState('')
  const [scrollTargetPageId, setScrollTargetPageId] = useState('')
  const [visiblePageBadgeId, setVisiblePageBadgeId] = useState('')
  const [savedAt, setSavedAt] = useState('')
  const [editorMode, setEditorMode] = useState('type')
  const [drawColor, setDrawColor] = useState('#0d6d62')
  const [drawSize, setDrawSize] = useState(2.2)
  const [eraserSize, setEraserSize] = useState(32)
  const [panel, setPanel] = useState('book')

  const resolvedActivePageId = activePageId || pages[0]?.id || ''
  const activePageIndex = pages.findIndex((page) => page.id === resolvedActivePageId)
  const activePage = activePageIndex >= 0 ? pages[activePageIndex] : pages[0] || null

  useEffect(() => {
    document.body.classList.add('learn-reader-active')
    return () => document.body.classList.remove('learn-reader-active')
  }, [])

  useEffect(() => {
    const payload = safeJsonParse(window.localStorage.getItem(readerStorageKey(sessionId, book.asset_id)) || '')
    const hydrated = hydrateNotebookPages(payload)
    const nextPages = hydrated.length ? hydrated : [createNotebookPage({ title: 'Trang 1' })]
    const nextActive = nextPages.some((p) => p.id === payload?.activePageId) ? payload.activePageId : nextPages[0].id
    setPages(nextPages)
    setActivePageId(nextActive)
    setSavedAt(typeof payload?.savedAt === 'string' ? payload.savedAt : '')
    setEditorMode('type')
  }, [book.asset_id, sessionId])

  useEffect(() => {
    if (!pages.length) return
    if (!activePageId || !pages.some((page) => page.id === activePageId)) setActivePageId(pages[0].id)
  }, [activePageId, pages])

  useEffect(() => {
    if (!scrollTargetPageId) return
    window.requestAnimationFrame(() => {
      pageElementRefs.current.get(scrollTargetPageId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setScrollTargetPageId('')
    })
  }, [scrollTargetPageId])

  useEffect(() => () => {
    if (pageBadgeTimerRef.current) window.clearTimeout(pageBadgeTimerRef.current)
  }, [])

  function updatePageById(pageId, patch) {
    if (!pageId) return
    setPages((current) => current.map((page) => {
      if (page.id !== pageId) return page
      const nextPatch = typeof patch === 'function' ? patch(page) : patch
      return { ...page, ...nextPatch, updatedAt: new Date().toISOString() }
    }))
  }

  function revealPageBadge(pageId) {
    if (!pageId) return
    if (pageBadgeTimerRef.current) window.clearTimeout(pageBadgeTimerRef.current)
    setVisiblePageBadgeId(pageId)
    pageBadgeTimerRef.current = window.setTimeout(() => {
      setVisiblePageBadgeId('')
      pageBadgeTimerRef.current = null
    }, 1800)
  }

  async function pasteImagesFromClipboard(event, pageId = resolvedActivePageId) {
    const files = Array.from(event.clipboardData?.items || [])
      .filter((item) => item.type.startsWith('image/'))
      .map((item) => item.getAsFile())
      .filter(Boolean)
    if (!files.length) return
    event.preventDefault()
    const srcList = (await Promise.all(files.map(fileToDataUrl))).filter(Boolean)
    if (!srcList.length) return
    updatePageById(pageId, (page) => {
      const existing = normalizeNoteImages(page.images)
      return { images: [...existing, ...srcList.map((src, i) => createNoteImage(src, existing.length + i))] }
    })
  }

  useEffect(() => {
    function handleWindowPaste(event) {
      if (event.target?.tagName === 'TEXTAREA') return
      pasteImagesFromClipboard(event)
    }
    window.addEventListener('paste', handleWindowPaste)
    return () => window.removeEventListener('paste', handleWindowPaste)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedActivePageId])

  async function handleImageUpload(event) {
    const files = Array.from(event.target.files || [])
    if (!files.length) return
    const srcList = (await Promise.all(files.map(fileToDataUrl))).filter(Boolean)
    if (srcList.length) {
      updatePageById(resolvedActivePageId, (page) => {
        const existing = normalizeNoteImages(page.images)
        return { images: [...existing, ...srcList.map((src, i) => createNoteImage(src, existing.length + i))] }
      })
    }
    event.target.value = ''
  }

  function handleSelectPage(pageId) {
    if (!pageId || pageId === resolvedActivePageId) return
    setActivePageId(pageId)
    setScrollTargetPageId(pageId)
    setEditorMode('type')
  }

  function handleAddPage() {
    let createdId = ''
    setPages((current) => {
      const created = createNotebookPage({ title: `Trang ${current.length + 1}` })
      createdId = created.id
      const idx = current.findIndex((page) => page.id === resolvedActivePageId)
      if (idx < 0) return [...current, created]
      const next = [...current]
      next.splice(idx + 1, 0, created)
      return next
    })
    if (createdId) {
      setActivePageId(createdId)
      setScrollTargetPageId(createdId)
      revealPageBadge(createdId)
    }
    setEditorMode('type')
    setPanel('notes')
  }

  function saveReaderState() {
    const savedIso = new Date().toISOString()
    const activeId = resolvedActivePageId || pages[0]?.id || ''
    const pagesToSave = (pages.length ? pages : [createNotebookPage({ title: 'Trang 1' })]).map((page) => (
      page.id === activeId ? { ...page, updatedAt: savedIso } : page
    ))
    const active = pagesToSave.find((page) => page.id === activeId) || pagesToSave[0]
    window.localStorage.setItem(readerStorageKey(sessionId, book.asset_id), JSON.stringify({
      pages: pagesToSave,
      activePageId: active?.id || '',
      noteHtml: composeNoteHtml(active?.noteText || '', active?.images || []),
      noteText: active?.noteText || '',
      images: active?.images || [],
      drawingDataUrl: active?.drawingDataUrl || '',
      savedAt: savedIso,
    }))
    setPages(pagesToSave)
    setSavedAt(savedIso)
  }

  return {
    uploadInputRef,
    pageElementRefs,
    pages,
    visiblePageBadgeId,
    savedAt,
    editorMode,
    setEditorMode,
    drawColor,
    setDrawColor,
    drawSize,
    setDrawSize,
    eraserSize,
    setEraserSize,
    panel,
    setPanel,
    resolvedActivePageId,
    activePage,
    updatePageById,
    pasteImagesFromClipboard,
    handleImageUpload,
    handleSelectPage,
    handleAddPage,
    saveReaderState,
    setActivePageId,
  }
}
