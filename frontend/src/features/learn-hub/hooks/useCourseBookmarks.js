import { accountStorageKey } from '../../../shared/auth/accountContext'
import { useCallback, useState } from 'react'

const storageKey = owner => accountStorageKey(owner, 'bookmarks:v2')

function readStoredBookmarks(owner) {
  if (!owner) return []
  try {
    const raw = localStorage.getItem(storageKey(owner))
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function useCourseBookmarks(owner) {
  const [bookmarks, setBookmarks] = useState(() => readStoredBookmarks(owner))

  const toggleBookmark = useCallback((courseId) => {
    if (!owner) return
    setBookmarks((prev) => {
      const next = prev.includes(courseId)
        ? prev.filter((id) => id !== courseId)
        : [...prev, courseId]
      try {
        localStorage.setItem(storageKey(owner), JSON.stringify(next))
      } catch {
        /* noop */
      }
      return next
    })
  }, [owner])

  return { bookmarks, toggleBookmark }
}
