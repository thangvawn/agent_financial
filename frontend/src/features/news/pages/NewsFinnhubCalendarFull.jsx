import { Fragment, useEffect, useRef, useState } from 'react'

import {
  finnhubCell,
  finnhubNumCell,
  formatFinnhubEconTimeCell,
  formatFinnhubMacroAsOf,
  groupFinnhubEconomicDays,
} from './newsFinnhubCalendarUtils.js'

const FINNHUB_CAL_INITIAL = 15
const FINNHUB_CAL_STEP = 15
const FINNHUB_CAL_MAX = 60

/**
 * Full Finnhub economic calendar table (scroll / “Xem thêm”, same markup as former in-page block).
 * @param {{ macroDesk: object | null }} props
 */
export default function NewsFinnhubCalendarFull({ macroDesk }) {
  const [finnhubCalVisible, setFinnhubCalVisible] = useState(FINNHUB_CAL_INITIAL)
  const finnhubScrollRef = useRef(null)
  const finnhubSentinelRef = useRef(null)

  const finnhubCalEvents = macroDesk?.calendar?.events || []
  const finnhubCalCap = Math.min(
    finnhubCalVisible,
    finnhubCalEvents.length,
    FINNHUB_CAL_MAX,
  )
  const finnhubCalSlice = finnhubCalEvents.slice(0, finnhubCalCap)
  const finnhubCalTotal = Math.min(finnhubCalEvents.length, FINNHUB_CAL_MAX)

  useEffect(() => {
    const win = macroDesk?.calendar
    if (!win?.from || !win?.to) return
    setFinnhubCalVisible(FINNHUB_CAL_INITIAL)
  }, [macroDesk?.calendar?.from, macroDesk?.calendar?.to])

  useEffect(() => {
    const root = finnhubScrollRef.current
    const target = finnhubSentinelRef.current
    if (!root || !target || finnhubCalVisible >= finnhubCalTotal) return
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setFinnhubCalVisible((n) => Math.min(n + FINNHUB_CAL_STEP, finnhubCalTotal))
        }
      },
      { root, rootMargin: '80px 0px', threshold: 0 },
    )
    io.observe(target)
    return () => io.disconnect()
  }, [finnhubCalTotal, finnhubCalVisible])

  if (macroDesk == null) {
    return <p className="news-desk__state">Đang tải lịch kinh tế…</p>
  }

  if (macroDesk.enabled) {
    return (
      <section id="news-econ-calendar" className="news-desk__econ-calendar news-desk__finnhub news-desk__finnhub--prominent" aria-label="Lịch kinh tế Finnhub">
        <div className="news-desk__econ-calendar-head">
          <h2 className="news-desk__econ-calendar-title">Lịch kinh tế</h2>
          <span className="news-desk__econ-calendar-source">Finnhub</span>
        </div>
        <div className="news-desk__finnhub-head">
          <p className="news-desk__finnhub-lede">
            Sự kiện vĩ mô đã lên lịch (chỉ số, họp NHNN, phát biểu…). Dùng để theo dõi giờ công bố — không phải tư vấn đầu tư.
          </p>
          <div className="news-desk__finnhub-tzline" aria-label="Múi giờ">
            <span className="news-desk__finnhub-pill">Giờ công bố: UTC</span>
            <span className="news-desk__finnhub-pill news-desk__finnhub-pill--muted">≈ Việt Nam: UTC + 7 (xem cột Giờ)</span>
          </div>
        </div>
        <details className="news-desk__finnhub-help">
          <summary>Cách đọc nhanh</summary>
          <ul>
            <li><strong>QG</strong>: quốc gia / vùng (CA, EU…).</li>
            <li><strong>Mức</strong>: độ “ồn ào” thường gặp trên lịch (high / medium / low), không phải xếp hạng đầu tư.</li>
            <li><strong>Dự báo / Thực tế / Trước</strong>: chỉ khi là chỉ số có số; phát biểu / ngày lễ thường trống — bình thường.</li>
            <li><strong>Cả ngày</strong>: không có mốc giờ từ nguồn — không đồng nghĩa 00:00.</li>
          </ul>
        </details>
        {macroDesk.calendar?.events?.length ? (
          <>
            <p className="news-desk__finnhub-range">
              Hiển thị {finnhubCalSlice.length}/{finnhubCalTotal} sự kiện (tối đa {FINNHUB_CAL_MAX} gần nhất)
              {finnhubCalSlice.length < finnhubCalTotal ? ' · cuộn trong khung hoặc “Xem thêm”' : ''}
            </p>
            <div className="news-desk__finnhub-cal-scroll" ref={finnhubScrollRef}>
              <table className="news-desk__finnhub-table">
                <caption className="news-desk__finnhub-caption">
                  Finnhub · {macroDesk.calendar.from} → {macroDesk.calendar.to}
                </caption>
                <thead>
                  <tr>
                    <th scope="col" className="news-desk__finnhub-th-time">
                      <span className="news-desk__finnhub-th-main">Giờ</span>
                      <span className="news-desk__finnhub-th-sub">UTC · VN</span>
                    </th>
                    <th scope="col">QG</th>
                    <th scope="col">Mức</th>
                    <th scope="col">Sự kiện</th>
                    <th scope="col">Dự báo</th>
                    <th scope="col">Thực tế</th>
                    <th scope="col">Trước</th>
                  </tr>
                </thead>
                {groupFinnhubEconomicDays(finnhubCalSlice).map((g) => (
                  <Fragment key={g.day}>
                    <tbody className="news-desk__finnhub-tbody">
                      <tr className="news-desk__finnhub-dayrow">
                        <td colSpan={7}>
                          <div className="news-desk__finnhub-dayrow-inner">
                            <span className="news-desk__finnhub-dayrow-title">{g.dayLabel}</span>
                            {g.day !== 'unknown' ? (
                              <span className="news-desk__finnhub-dayrow-iso">{g.day}</span>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                      {g.items.map((ev, i) => {
                        const timeCell = formatFinnhubEconTimeCell(ev)
                        const rk = `e-${g.day}-${i}-${ev.country}-${String(ev.event).slice(0, 40)}`
                        return (
                          <tr key={rk} className="news-desk__finnhub-row">
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--time">
                              <span className="news-desk__finnhub-time-main">{timeCell.main}</span>
                              {timeCell.utcLabel ? (
                                <span className="news-desk__finnhub-time-zone">{timeCell.utcLabel}</span>
                              ) : null}
                              {timeCell.vnLine ? (
                                <span className="news-desk__finnhub-time-vn">{timeCell.vnLine}</span>
                              ) : null}
                              {timeCell.sub ? (
                                <span className="news-desk__finnhub-time-sub">{timeCell.sub}</span>
                              ) : null}
                            </td>
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--cc">{finnhubCell(ev.country)}</td>
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--impact">
                              <span className={`news-desk__finnhub-impact is-${((ev.impact && String(ev.impact).trim()) ? String(ev.impact).toLowerCase() : 'none')}`}>
                                {finnhubCell(ev.impact)}
                              </span>
                            </td>
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--event">{finnhubCell(ev.event)}</td>
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--num">{finnhubNumCell(ev.estimate, ev.unit)}</td>
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--num">{finnhubNumCell(ev.actual, ev.unit)}</td>
                            <td className="news-desk__finnhub-td news-desk__finnhub-td--num">{finnhubNumCell(ev.prev, ev.unit)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </Fragment>
                ))}
              </table>
              {finnhubCalSlice.length < finnhubCalTotal ? (
                <>
                  <div ref={finnhubSentinelRef} className="news-desk__list-sentinel" aria-hidden />
                  <div className="news-desk__load-more-wrap">
                    <button
                      type="button"
                      className="news-desk__button news-desk__button--ghost news-desk__load-more"
                      onClick={() => setFinnhubCalVisible((n) => Math.min(n + FINNHUB_CAL_STEP, finnhubCalTotal))}>
                      Xem thêm lịch ({finnhubCalTotal - finnhubCalSlice.length} sự kiện)
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          </>
        ) : macroDesk.calendar_error ? (
          <p className="news-desk__state news-desk__state--warning">Lịch: {macroDesk.calendar_error}</p>
        ) : (
          <p className="news-desk__state">Chưa có sự kiện trong cửa sổ ngày.</p>
        )}
        <p className="news-desk__finnhub-foot">
          Làm mới ~{Math.round((macroDesk.cache?.calendar_ttl_sec ?? 0) / 60)} phút
          {macroDesk.as_of ? ` · cập nhật ${formatFinnhubMacroAsOf(macroDesk.as_of)}` : ''}
        </p>
      </section>
    )
  }

  if (macroDesk.client_error) {
    return (
      <section id="news-econ-calendar" className="news-desk__econ-calendar news-desk__finnhub news-desk__finnhub--prominent" aria-label="Lịch kinh tế">
        <div className="news-desk__econ-calendar-head">
          <h2 className="news-desk__econ-calendar-title">Lịch kinh tế</h2>
        </div>
        <p className="news-desk__state news-desk__state--warning">Không tải được Finnhub (mạng hoặc server).</p>
      </section>
    )
  }

  return (
    <section id="news-econ-calendar" className="news-desk__econ-calendar news-desk__finnhub news-desk__finnhub--prominent" aria-label="Lịch kinh tế">
      <div className="news-desk__econ-calendar-head">
        <h2 className="news-desk__econ-calendar-title">Lịch kinh tế</h2>
      </div>
      <p className="news-desk__state">Macro Finnhub: thêm <code>FINNHUB_API_KEY</code> vào <code>.env</code> rồi restart backend.</p>
    </section>
  )
}
