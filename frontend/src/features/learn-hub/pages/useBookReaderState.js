import { useEffect, useRef, useState } from 'react'
import {
  composeNoteHtml,
  continueNotebookText,
  createNoteImage,
  createNotebookPage,
  fileToDataUrl,
  hydrateNotebookPages,
  locateNotebookCaret,
  normalizeNoteImages,
  readerStorageKey,
  safeJsonParse,
} from './bookReaderModel'
import {notebookCaretTop} from './notePaperLayout'

export function useBookReaderState({ book, sessionId }) {
  const uploadInputRef = useRef(null)
  const pageElementRefs = useRef(new Map())
  const pageBadgeTimerRef = useRef(null)
  const notesScrollRef = useRef(null)
  const scrollIntentRef = useRef(0)
  const lastScrollTopRef = useRef(0)
  const lastAppendRef = useRef('')
  const touchYRef = useRef(0)
  const pendingCaretRef = useRef(null)

  const [pages, setPages] = useState(() => [createNotebookPage({ title: 'Trang 1' })])
  const [activePageId, setActivePageId] = useState('')
  const [scrollTargetPageId, setScrollTargetPageId] = useState('')
  const [visiblePageBadgeId, setVisiblePageBadgeId] = useState('')
  const [savedAt, setSavedAt] = useState('')
  const [continuationMessage, setContinuationMessage] = useState('')
  const [editorMode, setEditorMode] = useState('type')
  const [drawColor, setDrawColor] = useState('#0d6d62')
  const [drawSize, setDrawSize] = useState(2.2)
  const [eraserSize, setEraserSize] = useState(32)
  const [panel, setPanel] = useState(() => typeof window !== 'undefined' && window.matchMedia('(max-width: 960px)').matches ? 'book' : 'split')

  useEffect(() => {
    const narrow = window.matchMedia('(max-width: 960px)')
    const adapt = () => { if (narrow.matches) setPanel(current => current === 'split' ? 'book' : current) }
    narrow.addEventListener('change', adapt)
    return () => narrow.removeEventListener('change', adapt)
  }, [])

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
    const frame = window.requestAnimationFrame(() => {
      const paper = pageElementRefs.current.get(scrollTargetPageId)
      const caret = pendingCaretRef.current
      scrollIntentRef.current = 0
      if (caret?.pageId === scrollTargetPageId && paper) {
        const input = paper.querySelector('textarea')
        const scroll = notesScrollRef.current
        if (input && scroll) {
          input.focus({ preventScroll: true })
          input.setSelectionRange(caret.start, caret.end)
          const top = input.getBoundingClientRect().top - scroll.getBoundingClientRect().top + scroll.scrollTop
          scroll.scrollTop = Math.max(0, top + notebookCaretTop(input, caret.end) - scroll.clientHeight / 2)
        }
        pendingCaretRef.current = null
      } else {
        const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        paper?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
      }
      setScrollTargetPageId('')
    })
    return () => window.cancelAnimationFrame(frame)
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
    const created = createNotebookPage({ title: `Trang ${pages.length + 1}` })
    setPages((current) => {
      const idx = current.findIndex((page) => page.id === resolvedActivePageId)
      if (idx < 0) return [...current, created]
      const next = [...current]
      next.splice(idx + 1, 0, created)
      return next
    })
    setActivePageId(created.id)
    setScrollTargetPageId(created.id)
    revealPageBadge(created.id)
    setEditorMode('type')
    setPanel('notes')
  }

  function prepareNextPage(pageId = pages.at(-1)?.id) {
    if (!pageId || pages.at(-1)?.id !== pageId || lastAppendRef.current === pageId) return
    lastAppendRef.current = pageId
    scrollIntentRef.current = 0
    const created = createNotebookPage({ title: `Trang ${pages.length + 1}` })
    setPages(current => current.at(-1)?.id === pageId ? [...current, created] : current)
    setContinuationMessage(`Đã thêm trang ${pages.length + 1}. Tiếp tục ghi chú bên dưới.`)
    // Appending ahead must not move focus, the current page or the PDF/notes layout.
  }

  function appendAtBottom(element) {
    if (!element?.clientHeight || element.scrollHeight - element.scrollTop - element.clientHeight > 100) return
    prepareNextPage()
  }

  function handleNotesScroll(event) {
    const element = event.currentTarget
    const downward = element.scrollTop > lastScrollTopRef.current
    lastScrollTopRef.current = element.scrollTop
    if (downward && performance.now() < scrollIntentRef.current) appendAtBottom(element)
  }

  function handleNotesWheel(event) {
    if (event.deltaY <= 0) return
    scrollIntentRef.current = performance.now() + 800
    appendAtBottom(event.currentTarget)
  }

  function handleNotesKey(event) {
    if (event.target.matches('textarea,input,select') || !['ArrowDown','PageDown','End',' '].includes(event.key)) return
    scrollIntentRef.current = performance.now() + 800
    appendAtBottom(event.currentTarget)
  }

  function handleNotesTouch(event) {
    const y = event.touches[0]?.clientY
    if (y < touchYRef.current) {
      scrollIntentRef.current = performance.now() + 800
      appendAtBottom(event.currentTarget)
    }
    touchYRef.current = y
  }

  function handleTextOverflow(pageId, chunks, selection) {
    const result = continueNotebookText(pages, pageId, chunks)
    if (!result.pageIds.length) return
    const caret = locateNotebookCaret(chunks, selection.end)
    const start = locateNotebookCaret(chunks, selection.start)
    const focusId = result.pageIds[caret.index]
    scrollIntentRef.current = 0
    pendingCaretRef.current = { pageId: focusId, start: start.index === caret.index ? start.offset : 0, end: caret.offset }
    setPages(result.pages)
    setActivePageId(focusId)
    setScrollTargetPageId(focusId)
    setContinuationMessage(`Nội dung đã được nối sang trang tiếp theo.`)
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

  function triggerUpload() {
    uploadInputRef.current?.click()
  }

  function setPageElementRef(pageId, node) {
    if (node) pageElementRefs.current.set(pageId, node)
    else pageElementRefs.current.delete(pageId)
  }

  return {
    uploadInputRef,
    setPageElementRef,
    triggerUpload,
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
    prepareNextPage,
    handleTextOverflow,
    continuationMessage,
    notesScrollProps: {
      ref: notesScrollRef,
      onScroll: handleNotesScroll,
      onWheel: handleNotesWheel,
      onKeyDown: handleNotesKey,
      onTouchStart: event => { touchYRef.current = event.touches[0]?.clientY },
      onTouchMove: handleNotesTouch,
      onPointerDown: event => { if (event.target === event.currentTarget) scrollIntentRef.current = performance.now() + 3000 },
    },
    saveReaderState,
    setActivePageId,
  }
}
