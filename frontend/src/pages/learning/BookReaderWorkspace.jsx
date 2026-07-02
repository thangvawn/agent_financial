import { useEffect, useRef, useState } from 'react'

export function BookReaderWorkspace({ book, sessionId, onClose, asPage = false }) {
  const noteTextareaRef = useRef(null)
  const uploadInputRef = useRef(null)
  const pageElementRefs = useRef(new Map())
  const pageBadgeTimerRef = useRef(null)

  const [pages, setPages] = useState(() => [createNotebookPage({ title: 'Trang 1' })])
  const [activePageId, setActivePageId] = useState('')
  const [scrollTargetPageId, setScrollTargetPageId] = useState('')
  const [visiblePageBadgeId, setVisiblePageBadgeId] = useState('')
  const [savedAt, setSavedAt] = useState('')
  const [editorMode, setEditorMode] = useState('type')
  const [drawColor, setDrawColor] = useState('#0b5a50')
  const [drawSize, setDrawSize] = useState(2.2)
  const [eraserSize, setEraserSize] = useState(32)

  const resolvedActivePageId = activePageId || pages[0]?.id || ''
  const activePageIndex = pages.findIndex((page) => page.id === resolvedActivePageId)
  const activePage = activePageIndex >= 0 ? pages[activePageIndex] : pages[0] || null

  useEffect(() => {
    document.body.classList.add('learn-reader-active')
    return () => document.body.classList.remove('learn-reader-active')
  }, [])

  useEffect(() => {
    const storageKey = readerStorageKey(sessionId, book.asset_id)
    const payload = safeJsonParse(window.localStorage.getItem(storageKey) || '')
    const hydratedPages = hydrateNotebookPages(payload)
    const nextPages = hydratedPages.length ? hydratedPages : [createNotebookPage({ title: 'Trang 1' })]
    const nextActivePageId = nextPages.some((page) => page.id === payload?.activePageId)
      ? payload.activePageId
      : nextPages[0].id
    setPages(nextPages)
    setActivePageId(nextActivePageId)
    setSavedAt(typeof payload?.savedAt === 'string' ? payload.savedAt : '')
    setEditorMode('type')
  }, [book.asset_id, sessionId])

  useEffect(() => {
    if (!pages.length) return
    if (!activePageId || !pages.some((page) => page.id === activePageId)) {
      setActivePageId(pages[0].id)
    }
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

  function revealPageBadge(pageId) {
    if (!pageId) return
    if (pageBadgeTimerRef.current) window.clearTimeout(pageBadgeTimerRef.current)
    setVisiblePageBadgeId(pageId)
    pageBadgeTimerRef.current = window.setTimeout(() => {
      setVisiblePageBadgeId('')
      pageBadgeTimerRef.current = null
    }, 2000)
  }

  function updateActivePage(patch) {
    if (!resolvedActivePageId) return
    setPages((current) => current.map((page) => {
      if (page.id !== resolvedActivePageId) return page
      const nextPatch = typeof patch === 'function' ? patch(page) : patch
      return {
        ...page,
        ...nextPatch,
        updatedAt: new Date().toISOString(),
      }
    }))
  }

  function syncCanvasInto(pageId) {
    if (!pageId) return
  }

  async function pasteImagesFromClipboard(event, pageId = resolvedActivePageId) {
    const items = Array.from(event.clipboardData?.items || [])
    const files = items
      .filter((item) => item.type.startsWith('image/'))
      .map((item) => item.getAsFile())
      .filter(Boolean)
    if (!files.length) return
    event.preventDefault()
    const next = await Promise.all(files.map(fileToDataUrl))
    const normalized = next.filter(Boolean)
    if (!normalized.length) return
    appendInlineImages(pageId, normalized)
  }

  useEffect(() => {
    function handleWindowPaste(event) {
      const target = event.target
      if (target?.tagName === 'TEXTAREA') return
      pasteImagesFromClipboard(event)
    }

    window.addEventListener('paste', handleWindowPaste)
    return () => window.removeEventListener('paste', handleWindowPaste)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedActivePageId])

  function appendInlineImages(pageId, srcList) {
    updatePageById(pageId || resolvedActivePageId, (page) => {
      const existing = normalizeNoteImages(page.images)
      const nextImages = srcList.map((src, index) => createNoteImage(src, existing.length + index))
      return { images: [...existing, ...nextImages] }
    })
  }

  async function handleImageUpload(event) {
    const files = Array.from(event.target.files || [])
    if (!files.length) return
    const next = await Promise.all(files.map(fileToDataUrl))
    const normalized = next.filter(Boolean)
    if (!normalized.length) return
    appendInlineImages(resolvedActivePageId, normalized)
    event.target.value = ''
  }

  function updatePageById(pageId, patch) {
    if (!pageId) return
    setPages((current) => current.map((page) => {
      if (page.id !== pageId) return page
      const nextPatch = typeof patch === 'function' ? patch(page) : patch
      return {
        ...page,
        ...nextPatch,
        updatedAt: new Date().toISOString(),
      }
    }))
  }

  function updateImageAt(pageId, index, patch) {
    updatePageById(pageId, (page) => {
      const images = normalizeNoteImages(page.images)
      return {
        images: images.map((image, idx) => (idx === index ? { ...image, ...patch } : image)),
      }
    })
  }

  function removeImageFromPage(pageId, index) {
    updatePageById(pageId, (page) => ({ images: normalizeNoteImages(page.images).filter((_, idx) => idx !== index) }))
  }

  function clearDrawing() {
    updatePageById(resolvedActivePageId, { drawingDataUrl: '' })
  }

  function handleSelectPage(pageId) {
    if (!pageId || pageId === resolvedActivePageId) return
    setActivePageId(pageId)
    setScrollTargetPageId(pageId)
    setEditorMode('type')
  }

  function handleAddPage() {
    syncCanvasInto(resolvedActivePageId)
    let createdId = ''
    setPages((current) => {
      const createdPage = createNotebookPage({ title: `Trang ${current.length + 1}` })
      createdId = createdPage.id
      const currentIndex = current.findIndex((page) => page.id === resolvedActivePageId)
      if (currentIndex < 0) return [...current, createdPage]
      const next = [...current]
      next.splice(currentIndex + 1, 0, createdPage)
      return next
    })
    if (createdId) setActivePageId(createdId)
    if (createdId) setScrollTargetPageId(createdId)
    if (createdId) revealPageBadge(createdId)
    setEditorMode('type')
  }

  function saveReaderState() {
    const storageKey = readerStorageKey(sessionId, book.asset_id)
    const savedIso = new Date().toISOString()
    const activeId = resolvedActivePageId || pages[0]?.id || ''
    const pagesToSave = (pages.length ? pages : [createNotebookPage({ title: 'Trang 1' })]).map((page) => (
      page.id === activeId ? { ...page, updatedAt: savedIso } : page
    ))
    const activeForExport = pagesToSave.find((page) => page.id === activeId) || pagesToSave[0]
    const payload = {
      pages: pagesToSave,
      activePageId: activeForExport?.id || '',
      noteHtml: composeNoteHtml(activeForExport?.noteText || '', activeForExport?.images || []),
      noteText: activeForExport?.noteText || '',
      images: activeForExport?.images || [],
      drawingDataUrl: activeForExport?.drawingDataUrl || '',
      savedAt: savedIso,
    }
    window.localStorage.setItem(storageKey, JSON.stringify(payload))
    setPages(pagesToSave)
    setSavedAt(savedIso)
  }

  function closeAndPersist() {
    saveReaderState()
    onClose()
  }

  function switchMode(nextMode) {
    setEditorMode(nextMode)
    if (nextMode === 'draw' || nextMode === 'erase') {
      noteTextareaRef.current?.blur()
      return
    }
    window.setTimeout(() => {
      noteTextareaRef.current?.focus()
    }, 0)
  }

  const canInlinePdf = /\.pdf$/i.test(book.file_name || '')
  const pdfBookModeUrl = canInlinePdf
    ? `${book.url}#toolbar=0&navpanes=0&statusbar=0&messages=0&page=1&view=FitH&zoom=page-width`
    : book.url

  const toolbarButtonClass = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 dark:bg-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-700 text-slate-800 dark:text-zinc-200 border border-slate-200 dark:border-zinc-700 transition cursor-pointer active:scale-95'
  const activeToolbarButtonClass = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-teal-500 hover:bg-teal-600 text-white border border-teal-500 transition cursor-pointer active:scale-95'

  return (
    <div className={`fixed inset-0 ${asPage ? 'z-[120]' : 'z-[120]'} bg-slate-100 dark:bg-zinc-950`}>
      {!asPage && <div className="absolute inset-0 bg-black/70 backdrop-blur-[6px]" onClick={closeAndPersist} />}
      <div className="relative flex h-full min-h-0 flex-col overflow-hidden bg-slate-100 dark:bg-zinc-950 text-slate-900 dark:text-zinc-150">
        <header className="flex h-12 shrink-0 items-center justify-between gap-3 border-b border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4">
          <div className="flex min-w-0 items-center gap-3">
            <strong className="truncate text-sm font-bold text-slate-900 dark:text-white">{book.title}</strong>
            <span className="rounded-full border border-slate-200 dark:border-zinc-700 bg-slate-50 dark:bg-zinc-800 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-zinc-400">
              {activePage ? `Note ${activePageIndex + 1}/${pages.length}` : 'Note'}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <button type="button" className={toolbarButtonClass} onClick={handleAddPage} title="Thêm trang">
              + Trang
            </button>
            <button type="button" className={toolbarButtonClass} onClick={() => uploadInputRef.current?.click()} title="Chèn ảnh">
              □ Ảnh
            </button>
            <button type="button" className={toolbarButtonClass} onClick={clearDrawing} title="Xóa nét vẽ">
              ⌫ Vẽ
            </button>
            <button
              type="button"
              className={editorMode === 'type' ? activeToolbarButtonClass : toolbarButtonClass}
              onClick={() => switchMode('type')}
              title="Gõ chữ"
            >
              T
            </button>
            <button
              type="button"
              className={editorMode === 'draw' ? activeToolbarButtonClass : toolbarButtonClass}
              onClick={() => switchMode('draw')}
              title="Bút vẽ"
            >
              ✎
            </button>
            <button
              type="button"
              className={editorMode === 'erase' ? activeToolbarButtonClass : toolbarButtonClass}
              onClick={() => switchMode('erase')}
              title="Tẩy nét vẽ"
            >
              Tẩy
            </button>
            <label className="flex items-center gap-1.5 text-xs text-slate-650 dark:text-zinc-400 font-medium" title="Kích thước tẩy">
              <span>Tẩy:</span>
              <input
                type="range"
                className="w-16 h-1 bg-slate-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer"
                min={8}
                max={96}
                step={2}
                value={eraserSize}
                onChange={(event) => setEraserSize(Number(event.target.value))}
                aria-label="Kích thước tẩy"
              />
            </label>
            <label className="flex items-center gap-1.5">
              <input className="w-5 h-5 rounded border-0 cursor-pointer" type="color" value={drawColor} onChange={(event) => setDrawColor(event.target.value)} />
            </label>
            <label className="flex items-center gap-1.5 text-xs text-slate-655 dark:text-zinc-400 font-medium">
              <span>Bút:</span>
              <input
                type="range"
                className="w-16 h-1 bg-slate-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer"
                min={1}
                max={12}
                step={0.5}
                value={drawSize}
                onChange={(event) => setDrawSize(Number(event.target.value))}
              />
            </label>
            <button type="button" className={toolbarButtonClass} onClick={saveReaderState}>Lưu</button>
            {asPage && (
              <button type="button" className={toolbarButtonClass} onClick={closeAndPersist}>Learn</button>
            )}
            <button type="button" className={activeToolbarButtonClass} onClick={closeAndPersist}>Đóng</button>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-2">
          <section className="min-h-0 overflow-hidden border-r border-slate-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            {canInlinePdf ? (
              <object data={pdfBookModeUrl} type="application/pdf" aria-label={book.title} className="h-full w-full bg-white dark:bg-zinc-950">
                <iframe className="h-full w-full border-0" src={pdfBookModeUrl} title={book.title} />
              </object>
            ) : (
              <div className="grid h-full place-content-center justify-items-center gap-3 text-center p-6">
                <p className="text-sm text-slate-600 dark:text-zinc-400">Định dạng này chưa hỗ trợ xem trực tiếp trong app.</p>
                <a className={activeToolbarButtonClass} href={book.url} target="_blank" rel="noreferrer">
                  Mở file ở tab mới
                </a>
              </div>
            )}
          </section>

          <aside className="flex min-h-0 flex-col overflow-hidden bg-white dark:bg-zinc-900">
            <div className="flex h-11 shrink-0 items-center gap-4 border-b border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-850/50 px-4">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-zinc-400">
                <span>Trang</span>
                <select
                  className="rounded border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 outline-none text-xs font-bold"
                  value={resolvedActivePageId}
                  onChange={(event) => handleSelectPage(event.target.value)}
                  aria-label="Chọn trang ghi chú"
                >
                  {pages.map((page, index) => (
                    <option key={page.id} value={page.id}>
                      {page.title || `Trang ${index + 1}`}
                    </option>
                  ))}
                </select>
              </label>
              <input
                type="text"
                className="flex-1 bg-transparent border-0 font-semibold text-xs outline-none text-slate-800 dark:text-white"
                value={activePage?.title || ''}
                onChange={(event) => updateActivePage({ title: event.target.value })}
                placeholder={`Trang ${Math.max(activePageIndex + 1, 1)}`}
                aria-label="Tên trang ghi chú hiện tại"
              />
            </div>

            <input
              ref={uploadInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="hidden"
            />

            <div className="min-h-0 flex-1 overflow-y-auto bg-slate-100 dark:bg-zinc-950 p-4 pb-4 [scrollbar-width:thin]">
              <div className="mx-auto grid w-full max-w-[900px] gap-6">
                {pages.map((page, index) => (
                  <NotePaper
                    key={page.id}
                    page={page}
                    pageIndex={index}
                    isActive={page.id === resolvedActivePageId}
                    showPageLabel={page.id === visiblePageBadgeId}
                    editorMode={editorMode}
                    drawColor={drawColor}
                    drawSize={drawSize}
                    eraserSize={eraserSize}
                    setPageRef={(node) => {
                      if (node) pageElementRefs.current.set(page.id, node)
                      else pageElementRefs.current.delete(page.id)
                    }}
                    onActivate={() => setActivePageId(page.id)}
                    onTextChange={(noteText) => updatePageById(page.id, { noteText })}
                    onDrawingChange={(drawingDataUrl) => updatePageById(page.id, { drawingDataUrl })}
                    onImageChange={(imageIndex, patch) => updateImageAt(page.id, imageIndex, patch)}
                    onImageRemove={(imageIndex) => removeImageFromPage(page.id, imageIndex)}
                    onPaste={(event) => pasteImagesFromClipboard(event, page.id)}
                    onTypeMode={() => setEditorMode('type')}
                  />
                ))}
              </div>

              <div className="mx-auto mt-4 flex w-full max-w-[900px] items-center justify-between gap-3 px-1">
                <button type="button" className={toolbarButtonClass} onClick={handleAddPage}>+ Trang mới</button>
                <small className="text-[10px] text-slate-500 dark:text-zinc-400 font-medium">{savedAt ? `Lưu lúc: ${new Date(savedAt).toLocaleString('vi-VN')}` : 'Chưa lưu.'}</small>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

function NotePaper({
  page,
  pageIndex,
  isActive,
  showPageLabel,
  editorMode,
  drawColor,
  drawSize,
  eraserSize,
  setPageRef,
  onActivate,
  onTextChange,
  onDrawingChange,
  onImageChange,
  onImageRemove,
  onPaste,
  onTypeMode,
}) {
  const canvasRef = useRef(null)
  const pointerStateRef = useRef({ drawing: false, x: 0, y: 0 })
  const imageDragRef = useRef(null)
  const images = normalizeNoteImages(page.images)

  useEffect(() => {
    drawPersistedCanvas(page.drawingDataUrl || null, canvasRef.current)
  }, [page.drawingDataUrl, page.id])

  function snapshotCanvas() {
    return canvasRef.current?.toDataURL('image/png') || ''
  }

  function pointerDown(event) {
    onActivate()
    if (!['draw', 'erase'].includes(editorMode) || !canvasRef.current) return
    event.preventDefault()
    const { x, y } = pointerPosition(event, canvasRef.current)
    pointerStateRef.current = { drawing: true, x, y }
    if (typeof event.currentTarget?.setPointerCapture === 'function') {
      event.currentTarget.setPointerCapture(event.pointerId)
    }
  }

  function pointerMove(event) {
    if (!['draw', 'erase'].includes(editorMode)) return
    const state = pointerStateRef.current
    const canvas = canvasRef.current
    if (!state.drawing || !canvas) return
    event.preventDefault()
    const context = canvas.getContext('2d')
    if (!context) return
    const next = pointerPosition(event, canvas)
    context.save()
    context.globalCompositeOperation = editorMode === 'erase' ? 'destination-out' : 'source-over'
    context.strokeStyle = editorMode === 'erase' ? 'rgba(0,0,0,1)' : drawColor
    context.lineWidth = editorMode === 'erase' ? eraserSize : drawSize
    context.lineCap = 'round'
    context.lineJoin = 'round'
    context.beginPath()
    context.moveTo(state.x, state.y)
    context.lineTo(next.x, next.y)
    context.stroke()
    context.restore()
    pointerStateRef.current = { drawing: true, x: next.x, y: next.y }
  }

  function pointerUp() {
    if (pointerStateRef.current.drawing) {
      onDrawingChange(snapshotCanvas())
    }
    pointerStateRef.current = { drawing: false, x: 0, y: 0 }
  }

  function imagePointerDown(event, index, mode = 'move') {
    event.preventDefault()
    event.stopPropagation()
    onActivate()
    const pageRect = event.currentTarget.closest('[data-note-paper]')?.getBoundingClientRect()
    const image = images[index]
    if (!pageRect || !image) return
    imageDragRef.current = {
      index,
      mode,
      startClientX: event.clientX,
      startClientY: event.clientY,
      startX: image.x,
      startY: image.y,
      startWidth: image.width,
      pageWidth: pageRect.width,
    }
    if (typeof event.currentTarget?.setPointerCapture === 'function') {
      event.currentTarget.setPointerCapture(event.pointerId)
    }
  }

  function imagePointerMove(event) {
    const drag = imageDragRef.current
    if (!drag) return
    event.preventDefault()
    const deltaX = event.clientX - drag.startClientX
    const deltaY = event.clientY - drag.startClientY
    if (drag.mode === 'resize') {
      onImageChange(drag.index, {
        width: Math.round(Math.min(720, Math.max(96, drag.startWidth + deltaX))),
      })
      return
    }
    const nextX = drag.startX + (deltaX / Math.max(drag.pageWidth, 1)) * 100
    onImageChange(drag.index, {
      x: Math.round(Math.min(82, Math.max(0, nextX)) * 10) / 10,
      y: Math.round(Math.min(1500, Math.max(0, drag.startY + deltaY))),
    })
  }

  function imagePointerUp() {
    imageDragRef.current = null
  }

  return (
    <section
      ref={setPageRef}
      data-note-paper
      className={`relative min-h-[500px] w-full overflow-hidden rounded-xl border bg-white dark:bg-zinc-900 shadow-sm ${isActive ? 'border-teal-500 ring-2 ring-teal-500/20' : 'border-slate-200 dark:border-zinc-800'}`}
      onPointerDown={onActivate}
    >
      {showPageLabel && (
        <span className="absolute left-3 top-2.5 z-[4] rounded-full border border-slate-200 dark:border-zinc-700 bg-white/90 dark:bg-zinc-800/90 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-slate-400">
          Trang {pageIndex + 1}
        </span>
      )}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 z-[1] h-full w-full touch-none bg-transparent opacity-100 ${['draw', 'erase'].includes(editorMode) && isActive ? 'pointer-events-auto cursor-crosshair' : 'pointer-events-none'}`}
        width={960}
        height={1400}
        onPointerDown={pointerDown}
        onPointerMove={pointerMove}
        onPointerUp={pointerUp}
        onPointerLeave={pointerUp}
        onPointerCancel={pointerUp}
      />
      <textarea
        className={`relative z-[2] min-h-[500px] w-full resize-none border-0 bg-transparent px-8 py-8 text-sm leading-7 text-slate-800 dark:text-zinc-200 caret-teal-500 outline-none placeholder:text-slate-400 ${['draw', 'erase'].includes(editorMode) && isActive ? 'pointer-events-none select-none' : 'pointer-events-auto'}`}
        value={page.noteText || ''}
        onChange={(event) => onTextChange(event.target.value)}
        onPaste={onPaste}
        onFocus={() => {
          onActivate()
          onTypeMode()
        }}
        spellCheck={false}
        placeholder="Viết ghi chú tại đây..."
      />
      {images.map((image, index) => (
        <figure
          key={`${image.src}-${index}`}
          className="group absolute z-[3] m-0 overflow-hidden rounded border border-slate-200 dark:border-zinc-700 bg-white shadow-sm"
          style={{
            left: `${image.x}%`,
            top: `${image.y}px`,
            width: `${image.width}px`,
          }}
          onPointerDown={(event) => imagePointerDown(event, index, 'move')}
          onPointerMove={imagePointerMove}
          onPointerUp={imagePointerUp}
          onPointerCancel={imagePointerUp}
          onPointerLeave={imagePointerUp}
        >
          <img className="block h-auto w-full object-contain" src={image.src} alt={`note-image-${index + 1}`} />
          <button
            type="button"
            className="absolute right-1 top-1 hidden min-h-0 rounded bg-white/90 px-1 text-[10px] font-bold text-slate-700 shadow group-hover:inline-flex"
            onClick={() => onImageRemove(index)}
            aria-label={`Xóa ảnh ${index + 1}`}
          >
            x
          </button>
          <span
            className="absolute bottom-1 right-1 hidden h-3.5 w-3.5 cursor-nwse-resize rounded bg-white/90 border border-teal-500 group-hover:block"
            onPointerDown={(event) => imagePointerDown(event, index, 'resize')}
            aria-hidden="true"
          />
        </figure>
      ))}
    </section>
  )
}

function readerStorageKey(sessionId, assetId) {
  return `learn-reader:${sessionId}:${assetId}`
}

function createNotebookPage(seed = {}) {
  const uniqueId = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function')
    ? crypto.randomUUID()
    : `page-${Date.now()}-${Math.random().toString(16).slice(2)}`
  const normalizedImages = normalizeNoteImages(seed.images)
  return {
    id: typeof seed.id === 'string' && seed.id ? seed.id : uniqueId,
    title: typeof seed.title === 'string' && seed.title.trim() ? seed.title.trim() : '',
    noteText: typeof seed.noteText === 'string' ? seed.noteText : '',
    images: normalizedImages,
    drawingDataUrl: typeof seed.drawingDataUrl === 'string' && seed.drawingDataUrl.startsWith('data:image/')
      ? seed.drawingDataUrl
      : '',
    updatedAt: typeof seed.updatedAt === 'string' ? seed.updatedAt : new Date().toISOString(),
  }
}

function hydrateNotebookPages(payload) {
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
  const legacyDrawing = typeof payload?.drawingDataUrl === 'string' ? payload.drawingDataUrl : ''
  return [createNotebookPage({
    title: 'Trang 1',
    noteText: legacyText,
    images: legacyImages,
    drawingDataUrl: legacyDrawing,
    updatedAt: payload?.savedAt,
  })]
}

function safeJsonParse(value) {
  if (!value) return null
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function drawPersistedCanvas(dataUrl, canvas) {
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

function pointerPosition(event, canvas) {
  const rect = canvas.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * canvas.width
  const y = ((event.clientY - rect.top) / rect.height) * canvas.height
  return { x, y }
}

async function fileToDataUrl(file) {
  if (!file) return ''
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
    reader.onerror = () => reject(new Error('Không đọc được ảnh'))
    reader.readAsDataURL(file)
  })
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

function composeNoteHtml(noteText, images) {
  const escaped = escapeHtml(noteText).replace(/\n/g, '<br>')
  const imageBlocks = normalizeNoteImages(images)
    .map((image) => `<p><img src="${image.src}" alt="note-image" /></p>`)
    .join('')
  return `<p>${escaped || ''}</p>${imageBlocks}`
}

function normalizeNoteImages(images) {
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

function createNoteImage(src, index = 0) {
  return {
    src,
    x: 8 + (index % 3) * 8,
    y: 112 + index * 32,
    width: 300,
  }
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
