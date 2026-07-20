import { useMemo, useState } from 'react'
import {
  TrendingUp,
  Star,
  Activity,
  Layers,
  Bitcoin,
  Wheat,
  CalendarDays,
  CircleUser,
  FileText,
  Briefcase,
  LockKeyhole,
} from 'lucide-react'

import GlobalTerminalPage from './GlobalTerminalPage'
import PortfolioPanel from './PortfolioPanel'
import TradePanel from './TradePanel'
import WatchlistPanel from './WatchlistPanel'
import DerivativesPanel from './DerivativesPanel'
import CryptoPanel from './CryptoPanel'
import CommoditiesPanel from './CommoditiesPanel'
import LeadersPanel from './LeadersPanel'
import './market-portfolio-panels.css'

const TABS = [
  { id: 'co_phieu', label: 'Cổ phiếu', icon: TrendingUp, group: 'main' },
  { id: 'watchlist', label: 'Watchlist', icon: Star, group: 'main' },
  { id: 'chi_so', label: 'Chỉ số', icon: Activity, group: 'main' },
  { id: 'phai_sinh', label: 'Phái sinh', icon: Layers, group: 'main' },
  { id: 'tai_san_so', label: 'Tài sản số', icon: Bitcoin, group: 'main' },
  { id: 'hang_hoa', label: 'Hàng hóa', icon: Wheat, group: 'main' },
  { id: 'lenh_giay', label: 'Lệnh giấy', icon: FileText, group: 'utility' },
  { id: 'danh_muc', label: 'Danh mục', icon: Briefcase, group: 'utility' },
  { id: 'su_kien', label: 'Sự kiện', icon: CalendarDays, group: 'extra' },
  { id: 'doanh_nhan', label: 'Doanh nhân', icon: CircleUser, group: 'extra' },
]

const MAIN_TABS = TABS.filter((t) => t.group === 'main')
const UTILITY_TABS = TABS.filter((t) => t.group === 'utility')
const EXTRA_TABS = TABS.filter((t) => t.group === 'extra')

function handleTabKeyDown(event, tabs, currentId, onSelect) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const currentIdx = tabs.findIndex((t) => t.id === currentId)
  const offset = event.key === 'ArrowLeft' ? -1 : 1
  const nextIdx =
    event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? tabs.length - 1
        : (currentIdx + offset + tabs.length) % tabs.length
  onSelect(tabs[nextIdx].id)
  const nextTab = event.currentTarget.parentElement?.children[nextIdx]
  if (nextTab instanceof HTMLElement) nextTab.focus()
}

export default function MarketPortfolioPage({ sessionId, onOpenProLab, onOpenNews, onOpenLogin }) {
  const [tab, setTab] = useState('co_phieu')
  const needsSession = ['watchlist', 'lenh_giay', 'danh_muc'].includes(tab)
  const sessionMissing = needsSession && !sessionId

  const body = useMemo(() => {
    if (sessionMissing && tab === 'watchlist') {
      return (
        <section className="mp-watchlist-locked" aria-labelledby="watchlist-login-title">
          <div className="mp-watchlist-locked__card">
            <span className="mp-watchlist-locked__icon" aria-hidden="true"><LockKeyhole size={22} strokeWidth={1.8} /></span>
            <span className="mp-watchlist-locked__eyebrow">WATCHLIST</span>
            <h2 id="watchlist-login-title">Đăng nhập để dùng Watchlist</h2>
            <p>Đăng nhập để tạo và theo dõi danh mục mã chứng khoán bạn quan tâm.</p>
            <button type="button" onClick={onOpenLogin}>Đăng nhập</button>
          </div>
        </section>
      )
    }
    if (tab === 'watchlist') return <WatchlistPanel sessionId={sessionId} />
    if (tab === 'lenh_giay') return <TradePanel sessionId={sessionId} />
    if (tab === 'danh_muc') return <PortfolioPanel sessionId={sessionId} />
    if (tab === 'chi_so') return <GlobalTerminalPage activeTab="indices" onOpenProLab={onOpenProLab} onOpenNews={onOpenNews} />
    if (tab === 'phai_sinh') return <DerivativesPanel />
    if (tab === 'tai_san_so') return <CryptoPanel />
    if (tab === 'hang_hoa') return <CommoditiesPanel />
    if (tab === 'su_kien') return <ComingSoonPanel label="Sự kiện" description="Lịch sự kiện kinh tế, ĐHCĐ và các mốc thời gian quan trọng." />
    if (tab === 'doanh_nhan') return <LeadersPanel />
    return <GlobalTerminalPage activeTab="dashboard" onOpenProLab={onOpenProLab} onOpenNews={onOpenNews} />
  }, [tab, sessionId, sessionMissing, onOpenProLab, onOpenNews, onOpenLogin])

  const allTabs = TABS
  const activeTab = allTabs.find((t) => t.id === tab) || allTabs[0]

  return (
    <section className="mp-desk" aria-labelledby="mp-desk-title">
      <div
        className="mp-desk__tabs"
        role="tablist"
        aria-label="Không gian Market & Portfolio"
      >
        {MAIN_TABS.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              id={`mp-tab-${item.id}`}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              aria-controls="mp-desk-panel"
              tabIndex={tab === item.id ? 0 : -1}
              className={tab === item.id ? 'is-active' : undefined}
              onClick={() => setTab(item.id)}
              onKeyDown={(e) => handleTabKeyDown(e, allTabs, item.id, setTab)}
            >
              <Icon size={16} strokeWidth={1.8} />
              <span>{item.label}</span>
            </button>
          )
        })}

        <div className="mp-desk__tabs-sep" aria-hidden="true" />

        {UTILITY_TABS.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              id={`mp-tab-${item.id}`}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              aria-controls="mp-desk-panel"
              tabIndex={tab === item.id ? 0 : -1}
              className={tab === item.id ? 'is-active' : undefined}
              onClick={() => setTab(item.id)}
              onKeyDown={(e) => handleTabKeyDown(e, allTabs, item.id, setTab)}
            >
              <Icon size={16} strokeWidth={1.8} />
              <span>{item.label}</span>
            </button>
          )
        })}

        <div className="mp-desk__tabs-sep" aria-hidden="true" />

        {EXTRA_TABS.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              id={`mp-tab-${item.id}`}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              aria-controls="mp-desk-panel"
              tabIndex={tab === item.id ? 0 : -1}
              className={tab === item.id ? 'is-active' : undefined}
              onClick={() => setTab(item.id)}
              onKeyDown={(e) => handleTabKeyDown(e, allTabs, item.id, setTab)}
            >
              <Icon size={16} strokeWidth={1.8} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </div>

      <div
        id="mp-desk-panel"
        className="mp-desk__panel"
        role="tabpanel"
        aria-labelledby={`mp-tab-${tab}`}
        tabIndex={0}
      >
        {body}
      </div>
    </section>
  )
}

function ComingSoonPanel({ label, description }) {
  return (
    <section className="mp-panel mp-panel--coming-soon">
      <div className="mp-coming-soon">
        <span className="mp-coming-soon__badge">SẮP RA MẮT</span>
        <h2>{label}</h2>
        <p>{description}</p>
        <div className="mp-coming-soon__grid">
          <div className="mp-coming-soon__card" />
          <div className="mp-coming-soon__card" />
          <div className="mp-coming-soon__card" />
        </div>
      </div>
    </section>
  )
}
