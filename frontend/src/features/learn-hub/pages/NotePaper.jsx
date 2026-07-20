import { useEffect, useRef } from 'react'
import { drawPersistedCanvas, normalizeNoteImages, pointerPosition } from './bookReaderModel'

export function NotePaper({
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
    event.currentTarget?.setPointerCapture?.(event.pointerId)
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
    if (pointerStateRef.current.drawing) onDrawingChange(snapshotCanvas())
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
    event.currentTarget?.setPointerCapture?.(event.pointerId)
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

  const inkActive = ['draw', 'erase'].includes(editorMode) && isActive

  return (
    <section
      ref={setPageRef}
      data-note-paper
      className={`br-paper${isActive ? ' is-active' : ''}`}
      onPointerDown={onActivate}
    >
      {showPageLabel ? <span className="br-paper__badge">Trang {pageIndex + 1}</span> : null}
      <canvas
        ref={canvasRef}
        className={`br-paper__canvas${inkActive ? ' is-ink' : ''}`}
        width={960}
        height={1400}
        onPointerDown={pointerDown}
        onPointerMove={pointerMove}
        onPointerUp={pointerUp}
        onPointerLeave={pointerUp}
        onPointerCancel={pointerUp}
      />
      <textarea
        className={`br-paper__text${inkActive ? ' is-locked' : ''}`}
        value={page.noteText || ''}
        onChange={(event) => onTextChange(event.target.value)}
        onPaste={onPaste}
        onFocus={() => {
          onActivate()
          onTypeMode()
        }}
        spellCheck={false}
        placeholder="Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ."
      />
      {images.map((image, index) => (
        <figure
          key={`${image.src}-${index}`}
          className="br-paper__image"
          style={{ left: `${image.x}%`, top: `${image.y}px`, width: `${image.width}px` }}
          onPointerDown={(event) => imagePointerDown(event, index, 'move')}
          onPointerMove={imagePointerMove}
          onPointerUp={imagePointerUp}
          onPointerCancel={imagePointerUp}
          onPointerLeave={imagePointerUp}
        >
          <img src={image.src} alt={`Ảnh ghi chú ${index + 1}`} />
          <button type="button" className="br-paper__image-x" onClick={() => onImageRemove(index)} aria-label={`Xóa ảnh ${index + 1}`}>×</button>
          <span
            className="br-paper__image-resize"
            onPointerDown={(event) => imagePointerDown(event, index, 'resize')}
            aria-hidden="true"
          />
        </figure>
      ))}
    </section>
  )
}
