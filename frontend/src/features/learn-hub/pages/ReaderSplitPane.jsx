import { useCallback, useEffect, useRef, useState } from 'react'

const STORAGE_KEY = 'learn-reader:split-pct'
const MIN_PCT = 28
const MAX_PCT = 72
const DEFAULT_PCT = 56

function clampPct(value) {
  if (!Number.isFinite(value)) return DEFAULT_PCT
  return Math.min(MAX_PCT, Math.max(MIN_PCT, value))
}

export function ReaderSplitPane({ book, notes, panel }) {
  const stageRef = useRef(null)
  const draggingRef = useRef(false)
  const [bookPct, setBookPct] = useState(() => {
    try {
      const stored = Number(window.localStorage.getItem(STORAGE_KEY))
      return stored ? clampPct(stored) : DEFAULT_PCT
    } catch { return DEFAULT_PCT }
  })

  const persist = (value) => { try { window.localStorage.setItem(STORAGE_KEY, String(Math.round(value))) } catch { /* Private browsing can disable storage. */ } }

  const handleMove = useCallback((event) => {
    if (!draggingRef.current || !stageRef.current) return
    const rect = stageRef.current.getBoundingClientRect()
    const clientX = event.touches?.[0]?.clientX ?? event.clientX
    const next = clampPct(((clientX - rect.left) / rect.width) * 100)
    setBookPct(next)
  }, [])

  const stopDrag = useCallback(() => {
    if (!draggingRef.current) return
    draggingRef.current = false
    document.body.classList.remove('br-resizing')
    setBookPct((current) => {
      persist(current)
      return current
    })
  }, [])

  useEffect(() => {
    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', stopDrag)
    window.addEventListener('pointercancel', stopDrag)
    window.addEventListener('blur', stopDrag)
    return () => {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', stopDrag)
      window.removeEventListener('pointercancel', stopDrag)
      window.removeEventListener('blur', stopDrag)
      document.body.classList.remove('br-resizing')
    }
  }, [handleMove, stopDrag])

  function startDrag(event) {
    event.preventDefault()
    draggingRef.current = true
    event.currentTarget.setPointerCapture?.(event.pointerId)
    document.body.classList.add('br-resizing')
  }

  return (
    <div
      ref={stageRef}
      className={`br-stage br-stage--${panel}`}
      style={{ '--br-book-pct': `${bookPct}%` }}
    >
      <section className="br-book" aria-label="Nội dung sách">{book}</section>
      <div
        className="br-splitter"
        role="separator"
        aria-orientation="vertical"
        aria-label="Kéo để chỉnh kích thước"
        aria-valuenow={Math.round(bookPct)}
        aria-valuemin={MIN_PCT}
        aria-valuemax={MAX_PCT}
        aria-valuetext={`Sách ${Math.round(bookPct)}%, ghi chú ${Math.round(100-bookPct)}%`}
        tabIndex={0}
        onPointerDown={startDrag}
        onDoubleClick={() => {
          setBookPct(DEFAULT_PCT)
          persist(DEFAULT_PCT)
        }}
        onKeyDown={(event) => {
          const next = event.key === 'Home' ? MIN_PCT : event.key === 'End' ? MAX_PCT : event.key === 'ArrowLeft' ? clampPct(bookPct - 2) : event.key === 'ArrowRight' ? clampPct(bookPct + 2) : null
          if (next !== null) { event.preventDefault(); setBookPct(next); persist(next) }
        }}
      >
        <span className="br-splitter__grip" aria-hidden="true" />
      </div>
      <aside className="br-notes" aria-label="Ghi chú khi đọc">{notes}</aside>
    </div>
  )
}
