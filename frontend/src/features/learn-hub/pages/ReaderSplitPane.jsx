import { useCallback, useEffect, useRef, useState } from 'react'

const STORAGE_KEY = 'learn-reader:split-pct'
const MIN_PCT = 22
const MAX_PCT = 78

function clampPct(value) {
  if (!Number.isFinite(value)) return 42
  return Math.min(MAX_PCT, Math.max(MIN_PCT, value))
}

export function ReaderSplitPane({ book, notes, panel }) {
  const stageRef = useRef(null)
  const draggingRef = useRef(false)
  const [bookPct, setBookPct] = useState(() => {
    const stored = Number(window.localStorage.getItem(STORAGE_KEY))
    return stored ? clampPct(stored) : 42
  })

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
      window.localStorage.setItem(STORAGE_KEY, String(Math.round(current)))
      return current
    })
  }, [])

  useEffect(() => {
    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', stopDrag)
    window.addEventListener('pointercancel', stopDrag)
    return () => {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', stopDrag)
      window.removeEventListener('pointercancel', stopDrag)
    }
  }, [handleMove, stopDrag])

  function startDrag(event) {
    event.preventDefault()
    draggingRef.current = true
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
        tabIndex={0}
        onPointerDown={startDrag}
        onDoubleClick={() => {
          setBookPct(42)
          window.localStorage.setItem(STORAGE_KEY, '42')
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowLeft') setBookPct((v) => clampPct(v - 2))
          if (event.key === 'ArrowRight') setBookPct((v) => clampPct(v + 2))
        }}
      >
        <span className="br-splitter__grip" aria-hidden="true" />
      </div>
      <aside className="br-notes" aria-label="Ghi chú khi đọc">{notes}</aside>
    </div>
  )
}
