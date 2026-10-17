import { useCallback, useState } from 'react'

const STORAGE_KEY = 'northstar.learn-hub.bookmarks'

function readStoredBookmarks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function useCourseBookmarks() {
  const [bookmarks, setBookmarks] = useState(readStoredBookmarks)

  const toggleBookmark = useCallback((courseId) => {
    setBookmarks((prev) => {
      const next = prev.includes(courseId)
        ? prev.filter((id) => id !== courseId)
        : [...prev, courseId]
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        /* noop */
      }
      return next
    })
  }, [])

  return { bookmarks, toggleBookmark }
}
