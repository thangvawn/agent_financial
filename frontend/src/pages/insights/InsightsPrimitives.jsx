import React from 'react'

export function SectionHeader({ icon, title, subtitle = '', action = null }) {
  return (
    <header className="section-header">
      <div><Icon name={icon} /><span><strong>{title}</strong>{subtitle ? <p>{subtitle}</p> : null}</span></div>
      {action}
    </header>
  )
}

export function Badge({ tone = 'neutral', children }) {
  return <span className={`badge-v2 badge-v2--${tone}`}>{children}</span>
}

export function TimeFilter({ active, onChange }) {
  return <div className="time-filter">{['1M', '3M', '6M', 'YTD', '1Y'].map((item) => <button key={item} type="button" className={active === item ? 'is-active' : ''} onClick={() => onChange(item)}>{item}</button>)}</div>
}

export function Sparkline({ values }) {
  return <svg className="sparkline" viewBox="0 0 96 28"><polyline points={toPoints(values, 96, 28)} /></svg>
}

export function AssetLine({ item, index }) {
  return <svg className={`asset-line-v2 asset-line-v2--${index}`} viewBox="0 0 680 210" style={{ color: item.color }}><polyline points={toPoints(item.values, 680, 210)} /></svg>
}

export function Icon({ name }) {
  const paths = {
    pulse: <><path d="M3 12h4l2-5 4 10 2-5h6" /></>,
    shield: <><path d="M12 3 5 6v5c0 4.2 2.8 7.4 7 9 4.2-1.6 7-4.8 7-9V6l-7-3Z" /><path d="m9 12 2 2 4-5" /></>,
    globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18" /></>,
    bolt: <><path d="m13 2-8 12h6l-1 8 8-12h-6l1-8Z" /></>,
    bell: <><path d="M6 9a6 6 0 0 1 12 0c0 7 3 6 3 8H3c0-2 3-1 3-8Z" /><path d="M10 20h4" /></>,
    chart: <><path d="M4 19V5" /><path d="M4 19h16" /><path d="m7 15 3-4 3 2 4-7 3 3" /></>,
    scenario: <><path d="M4 17 9 7l4 7 3-4 4 7H4Z" /><path d="M4 21h16" /></>,
    spark: <><path d="M12 3v18M3 12h18M6 6l12 12M18 6 6 18" /></>,
    radar: <><circle cx="12" cy="12" r="8" /><path d="M12 12 18 8M4 12h3M12 4v3" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    target: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="4" /><path d="M12 2v3M22 12h-3M12 22v-3M2 12h3" /></>,
    rotate: <><path d="M4 12a8 8 0 0 1 13.6-5.6L20 9" /><path d="M20 4v5h-5M20 12a8 8 0 0 1-13.6 5.6L4 15" /><path d="M4 20v-5h5" /></>,
    calendar: <><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16" /></>,
    book: <><path d="M4 5h7a3 3 0 0 1 3 3v12H7a3 3 0 0 0-3 3V5ZM20 5h-7a3 3 0 0 0-3 3" /></>,
    rates: <><path d="M4 18h16M7 14h10M9 10h6M12 6v12" /></>,
    chevron: <><path d="m9 6 6 6-6 6" /></>,
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name] || paths.spark}</svg>
}

export function trendIcon(key) {
  return { fx: 'globe', rates: 'rates', energy: 'bolt', breadth: 'pulse', liquidity: 'shield' }[key] || 'radar'
}

export function statusTone(status) {
  if (['High', 'Elevated'].includes(status)) return 'red'
  if (['Medium', 'Mixed'].includes(status)) return 'amber'
  if (['Low', 'Adequate'].includes(status)) return 'green'
  return 'neutral'
}

export function viewTone(view) {
  if (view === 'Tích cực') return 'green'
  if (view === 'Tiêu cực') return 'red'
  return 'amber'
}

function toPoints(values, width, height) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  return values.map((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * width
    const y = height - ((value - min) / span) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}
