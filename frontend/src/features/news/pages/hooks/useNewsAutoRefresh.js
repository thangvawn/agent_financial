import { useEffect } from 'react'

export default function useNewsAutoRefresh(refresh) {
  useEffect(() => {
    let last = 0
    function update() {
      if (document.visibilityState === 'hidden' || Date.now() - last < 1000) return
      last = Date.now()
      refresh()
    }
    const timer = setInterval(update, 60000)
    window.addEventListener('focus', update)
    document.addEventListener('visibilitychange', update)
    return () => {
      clearInterval(timer)
      window.removeEventListener('focus', update)
      document.removeEventListener('visibilitychange', update)
    }
  }, [refresh])
}
