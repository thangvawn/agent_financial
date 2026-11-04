import { useCallback, useEffect, useRef, useState } from 'react'

export default function useHeatmapLayout(groups, width, height, { focused = false, scope = '' } = {}) {
  const [result, setResult] = useState(null)
  const [attempt, setAttempt] = useState(0)
  const workerRef = useRef(null)
  const requestRef = useRef(null)
  const retry = useCallback(() => setAttempt(value => value + 1), [])
  // Canonical order excludes quote text and the feed's value ranking.
  const key = JSON.stringify({ groups: groups.map(g => ({ id: g.id, name: g.name,
    children: g.children.map(c => ({ id: c.id, weight: c.weight })).sort((a, b) => a.id.localeCompare(b.id)) }))
    .sort((a, b) => a.id.localeCompare(b.id)), width, height, options: { focused }, scope, attempt })

  useEffect(() => {
    let worker, stopped = false
    const fail = message => {
      const pending = requestRef.current
      clearTimeout(pending?.timer)
      if (!stopped && pending) setResult(previous => ({ key: pending.key, scope,
        layout: previous?.scope === scope ? previous.layout : null, error: message }))
    }
    try {
      worker = new Worker(new URL('../services/marketHeatmap.worker.js', import.meta.url), { type: 'module' })
      workerRef.current = worker
      worker.onmessage = ({ data }) => {
        if (stopped || data.key !== requestRef.current?.key) return
        clearTimeout(requestRef.current.timer)
        if (data.error) fail(data.error)
        else setResult({ ...data, scope })
      }
      worker.onerror = () => { worker.terminate(); workerRef.current = null; fail('Không khởi tạo được bản đồ. Bạn vẫn có thể xem dữ liệu dạng bảng.') }
    } catch {
      // The request effect installs the pending key before this microtask runs.
      queueMicrotask(() => fail('Trình duyệt chưa dựng được bản đồ. Hãy thử dạng bảng.'))
    }
    return () => { stopped = true; clearTimeout(requestRef.current?.timer); worker?.terminate(); workerRef.current = null }
  }, [scope, attempt])

  useEffect(() => {
    const input = JSON.parse(key)
    clearTimeout(requestRef.current?.timer)
    if (!input.width || !input.groups.length) { requestRef.current = null; return }
    const timer = setTimeout(() => {
      workerRef.current?.terminate(); workerRef.current = null
      setResult(previous => ({ key, scope, layout: previous?.scope === scope ? previous.layout : null,
        error: 'Bản đồ cần thêm thời gian. Hãy thử lại hoặc xem dạng bảng.' }))
    }, 10000)
    requestRef.current = { key, timer }
    workerRef.current?.postMessage({ ...input, key })
    return () => clearTimeout(timer)
  }, [key, scope])

  return { retry, layout: groups.length && result?.scope === scope ? result.layout : null,
    error: result?.key === key ? result.error || '' : '',
    computing: Boolean(width && groups.length && result?.key !== key) }
}
