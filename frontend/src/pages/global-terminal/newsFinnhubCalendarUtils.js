/** Finnhub economic calendar helpers shared by News desk + full-calendar page. */

export function formatFinnhubMacroAsOf(value) {
  if (!value) return '--'
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatFinnhubDayHeadingVi(ymd) {
  const [y, m, d] = ymd.split('-').map((x) => Number(x))
  if (!y || !m || !d) return ymd
  const dt = new Date(Date.UTC(y, m - 1, d))
  return dt.toLocaleDateString('vi-VN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export function parseFinnhubEconDay(dateRaw) {
  if (dateRaw == null || dateRaw === '') return null
  const s = String(dateRaw)
  const ymd = s.includes('T') ? s.split('T')[0] : s.slice(0, 10)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ymd)) return null
  return ymd
}

export function finnhubCell(v) {
  if (v == null || v === '') return '—'
  return String(v)
}

export function finnhubNumCell(v, unit) {
  if (v == null || v === '') return '—'
  const u = unit && String(unit).trim() ? ` ${unit}` : ''
  return `${v}${u}`
}

/** Milliseconds UTC for sorting; robust to Finnhub date/time shapes. */
export function finnhubEventInstantUtc(ev) {
  const ymd = parseFinnhubEconDay(ev.date)
  if (!ymd) return 0
  const t = ev.time
  if (t == null || t === '') return Date.parse(`${ymd}T00:00:00Z`)
  if (typeof t === 'number') {
    const ms = t < 2e12 ? t * 1000 : t
    return Number.isNaN(ms) ? Date.parse(`${ymd}T12:00:00Z`) : ms
  }
  const s = String(t).trim()
  if (/\d{4}-\d{2}-\d{2}T\d/.test(s)) {
    const ms = Date.parse(s)
    return Number.isNaN(ms) ? Date.parse(`${ymd}T12:00:00Z`) : ms
  }
  const m = s.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?/)
  if (m) {
    const hh = Number(m[1])
    const mm = Number(m[2])
    return Date.parse(
      `${ymd}T${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:00Z`,
    )
  }
  return Date.parse(`${ymd}T12:00:00Z`)
}

/** Time column: UTC + approx Vietnam (UTC+7) when a definite time exists. */
export function formatFinnhubEconTimeCell(ev) {
  const t = ev.time
  if (t == null || t === '') {
    return { main: '—', utcLabel: null, vnLine: null, sub: 'Cả ngày' }
  }
  const ms = finnhubEventInstantUtc(ev)
  if (!Number.isFinite(ms) || ms <= 0) {
    return { main: '—', utcLabel: null, vnLine: null, sub: '' }
  }
  const utcHm = new Date(ms).toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  })
  const vnHm = new Date(ms).toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Ho_Chi_Minh',
  })
  return {
    main: utcHm,
    utcLabel: 'UTC',
    vnLine: `≈ ${vnHm} VN`,
    sub: '',
  }
}

export function groupFinnhubEconomicDays(events) {
  const map = new Map()
  for (const ev of events) {
    const day = parseFinnhubEconDay(ev.date) || 'unknown'
    if (!map.has(day)) map.set(day, [])
    map.get(day).push(ev)
  }
  const keys = [...map.keys()].filter((k) => k !== 'unknown').sort()
  if (map.has('unknown')) keys.push('unknown')
  return keys.map((day) => {
    const items = (map.get(day) || []).slice().sort((a, b) => finnhubEventInstantUtc(a) - finnhubEventInstantUtc(b))
    return {
      day,
      dayLabel: day === 'unknown' ? 'Không rõ ngày' : formatFinnhubDayHeadingVi(day),
      items,
    }
  })
}
