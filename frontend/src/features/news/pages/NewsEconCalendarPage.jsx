import { useEffect, useState } from 'react'

import { fetchFinnhubMacroDesk } from '../services'
import NewsFinnhubCalendarFull from './NewsFinnhubCalendarFull.jsx'
import './news.css'

export default function NewsEconCalendarPage({ onBackToNews, embed = false }) {
  const [macroDesk, setMacroDesk] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function run() {
      try {
        const d = await fetchFinnhubMacroDesk({ force: false, calendarDays: 14, includeQuotes: false })
        if (!cancelled) setMacroDesk(d)
      } catch {
        if (!cancelled) setMacroDesk({ enabled: false, client_error: true })
      }
    }
    run()
    const id = window.setInterval(run, 60_000)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  if (embed) {
    return (
      <div className="news-desk news-desk--econ-calendar-embed">
        <NewsFinnhubCalendarFull macroDesk={macroDesk} />
      </div>
    )
  }

  return (
    <section className="news-desk news-desk--econ-calendar-page">
      <header className="news-desk__econ-calendar-page-head">
        <div>
          <p className="news-desk__econ-calendar-page-kicker">News Desk</p>
          <h1 className="news-desk__econ-calendar-page-title">Lịch kinh tế đầy đủ</h1>
          <p className="news-desk__econ-calendar-page-lede">Finnhub — mở trong cửa sổ riêng để xem bảng lớn, không cuộn trang News.</p>
        </div>
        {onBackToNews ? (
          <button type="button" className="news-desk__button news-desk__button--ghost" onClick={onBackToNews}>
            ← Về News Desk
          </button>
        ) : null}
      </header>
      <NewsFinnhubCalendarFull macroDesk={macroDesk} />
    </section>
  )
}
