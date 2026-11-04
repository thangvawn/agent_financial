import { useEffect, useRef, useState } from 'react'
import { clampView, focusBounds, zoomAt, retainLiveView } from '../services/marketHeatmapViewport'

const IDENTITY = { scale: 1, x: 0, y: 0 }

function clearGesture(g) {
  const captures = [...g.captures]
  g.pointers.clear(); g.captures.clear(); g.suppressClick = false
  for (const [id, element] of captures) if (element.hasPointerCapture(id)) element.releasePointerCapture(id)
}

export default function useHeatmapCamera(width, height, layout, scope, onMove, selectedId) {
  const [stored, setStored] = useState(null)
  const key = `${width}:${height}:${scope}`
  const active = stored?.key === key ? stored : null
  const maxScale = layout?.maxScale || active?.layout?.maxScale || 1
  const changed = layout && active?.layout && active.layout !== layout
  const view = changed ? retainLiveView(active.view, active.layout, layout, width, height, selectedId)
    : active ? clampView(active.view, width, height, maxScale) : IDENTITY
  // Derive the new camera before rendering the new layout, without an effect-frame jump.
  if (stored && stored.key !== key) setStored(null)
  else if (changed) setStored({ key, layout, view })
  const gesture = useRef({ pointers: new Map(), captures: new Map(), suppressClick: false })
  useEffect(() => {
    const g = gesture.current
    const reset = () => clearGesture(g)
    const hidden = () => { if (document.hidden) reset() }
    window.addEventListener('blur', reset)
    document.addEventListener('visibilitychange', hidden)
    return () => { window.removeEventListener('blur', reset); document.removeEventListener('visibilitychange', hidden); reset() }
  }, [])
  const update = next => { onMove(); setStored({ key, layout: layout || active?.layout, view: clampView(next, width, height, maxScale) }) }
  const zoom = (factor, point = { x: width / 2, y: height / 2 }) => update(zoomAt(view, factor, point, width, height, maxScale))
  const point = event => { const r = event.currentTarget.getBoundingClientRect(); return { x: event.clientX - r.left, y: event.clientY - r.top } }
  const anchor = () => {
    const g = gesture.current, pts = [...g.pointers.values()]
    g.base = view
    g.origin = pts.length > 1 ? { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 } : pts[0]
    g.distance = pts.length > 1 ? Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y) : 0
  }
  const endPointer = event => {
    const g = gesture.current
    if (!g.pointers.delete(event.pointerId)) return
    const element = g.captures.get(event.pointerId)
    g.captures.delete(event.pointerId)
    if (element?.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId)
    if (g.pointers.size) anchor()
  }
  return {
    view, zoom, reset: () => update(IDENTITY), focus: bounds => update(focusBounds(bounds, width, height, maxScale)),
    events: {
      onPointerDown(event) {
        if (event.button !== 0) return
        if (event.target.closest('button')) { gesture.current.suppressClick = false; return }
        const g = gesture.current
        if (!g.pointers.size) g.suppressClick = false
        g.pointers.set(event.pointerId, point(event)); anchor()
        // Capture from the first press, on the cell so normal clicks still reach it.
        const element = event.target.closest('[data-cell-id]') || event.currentTarget
        element.setPointerCapture(event.pointerId)
        g.captures.set(event.pointerId, element)
        if (g.pointers.size > 1) g.suppressClick = true
      },
      onPointerMove(event) {
        const g = gesture.current
        if (!g.pointers.has(event.pointerId)) return
        if (event.pointerType === 'mouse' && event.buttons === 0) { endPointer(event); return }
        g.pointers.set(event.pointerId, point(event))
        const pts = [...g.pointers.values()]
        if (pts.length > 1) {
          const mid = { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 }
          const distance = Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y)
          const next = zoomAt(g.base, distance / Math.max(1, g.distance), g.origin, width, height, maxScale)
          update({ ...next, x: next.x + mid.x - g.origin.x, y: next.y + mid.y - g.origin.y })
        } else {
          const dx = pts[0].x - g.origin.x, dy = pts[0].y - g.origin.y
          if (Math.hypot(dx, dy) < 5 && !g.suppressClick) return
          g.suppressClick = true
          update({ ...g.base, x: g.base.x + dx, y: g.base.y + dy })
        }
      },
      onPointerUp: endPointer,
      onLostPointerCapture: endPointer,
      onPointerCancel() { clearGesture(gesture.current) },
      onClickCapture(event) {
        const suppress = gesture.current.suppressClick
        gesture.current.suppressClick = false
        if (suppress && event.detail > 0) { event.preventDefault(); event.stopPropagation() }
      },
    },
  }
}
