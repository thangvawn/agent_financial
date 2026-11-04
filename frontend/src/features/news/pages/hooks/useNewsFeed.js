import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchNewsFeed } from '../../services'

const PAGE_SIZE = 24

export default function useNewsFeed(filters) {
  const key = JSON.stringify(filters)
  const currentKey = useRef(key)
  currentKey.current = key
  const request = useRef({ sequence: 0, controller: null })
  const latest = useRef(null)
  const [state, setState] = useState({ key, payload: null, loading: true, loadingMore: false, error: '', pending: false })
  latest.current = state

  const load = useCallback(async function run({ append = false, force = false, background = false } = {}) {
    const previous = latest.current?.key === key ? latest.current.payload : null
    if (append && (!previous?.next_cursor || request.current.controller)) return null
    if (background && request.current.controller) return null
    request.current.controller?.abort()
    const controller = new AbortController()
    const sequence = request.current.sequence + 1
    request.current = { sequence, controller }
    setState(current => ({ ...current, key, payload: current.key === key ? current.payload : null,
      pending: current.key === key && current.pending, error: '', loading: !append, loadingMore: append }))
    try {
      const data = await fetchNewsFeed({ ...JSON.parse(key), limit: PAGE_SIZE, force,
        cursor: append ? previous.next_cursor : undefined, signal: controller.signal })
      if (controller.signal.aborted || sequence !== request.current.sequence || currentKey.current !== key) return null
      setState(current => {
        if (background && previous?.articles.length > PAGE_SIZE) {
          const changed = JSON.stringify([data.articles, data.total])
            !== JSON.stringify([previous.articles.slice(0, PAGE_SIZE), previous.total])
          return { ...current, loading: false, pending: current.pending || changed }
        }
        const articles = append ? [...previous.articles, ...data.articles] : data.articles
        return { key, payload: { ...data, articles: [...new Map(articles.map(a => [a.article_id, a])).values()] },
          loading: false, loadingMore: false, error: '', pending: false }
      })
      return data
    } catch (error) {
      if (controller.signal.aborted || sequence !== request.current.sequence || currentKey.current !== key) return null
      if (append && error.status === 410) return run()
      setState(current => ({ ...current, key, loading: false, loadingMore: false,
        failedAppend: append,
        error: append ? 'Không tải được trang tiếp theo. Bạn có thể thử lại.' : previous
          ? 'Không thể cập nhật tin. Đang giữ kết quả gần nhất.' : 'Không thể tải tin. Vui lòng thử lại.' }))
      return null
    } finally {
      if (sequence === request.current.sequence) request.current.controller = null
    }
  }, [key])

  useEffect(() => {
    const timer = setTimeout(() => load(), 250)
    return () => {
      clearTimeout(timer)
      request.current.controller?.abort()
      request.current.controller = null
      request.current.sequence += 1
    }
  }, [load])

  const refresh = useCallback(options => load(options), [load])
  const loadMore = useCallback(() => load({ append: true }), [load])
  const retry = useCallback(() => load({ append: latest.current?.failedAppend === true }), [load])
  const current = state.key === key ? state : { payload: null, loading: true, loadingMore: false, error: '', pending: false }
  return { ...current, refresh, loadMore, retry }
}
