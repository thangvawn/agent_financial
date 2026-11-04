import { useMemo, useState } from 'react'
import {
  TrendingUp,
  LayoutDashboard,
  Star,
  Activity,
  Layers,
  Bitcoin,
  Wheat,
  Globe2,
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
import './market-portfolio-panels.css'

const TABS = [
  { id: 'tong_quan', label: 'Tổng quan', icon: LayoutDashboard, group: 'main' },
  { id: 'co_phieu', label: 'Cổ phiếu', icon: TrendingUp, group: 'main' },
  { id: 'watchlist', label: 'Watchlist', icon: Star, group: 'main' },
  { id: 'chi_so', label: 'Chỉ số', icon: Activity, group: 'main' },
  { id: 'ngoai_te', label: 'Ngoại hối', icon: Globe2, group: 'main' },
  { id: 'phai_sinh', label: 'Phái sinh', icon: Layers, group: 'main' },
  { id: 'tai_san_so', label: 'Tài sản số', icon: Bitcoin, group: 'main' },
  { id: 'hang_hoa', label: 'Hàng hóa', icon: Wheat, group: 'main' },
  { id: 'lenh_giay', label: 'Lệnh giấy', icon: FileText, group: 'utility' },
  { id: 'danh_muc', label: 'Danh mục', icon: Briefcase, group: 'utility' },
]

const MAIN_TABS = TABS.filter((t) => t.group === 'main')
const UTILITY_TABS = TABS.filter((t) => t.group === 'utility')

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
  const nextTab = event.currentTarget.closest('[role="tablist"]')?.querySelectorAll('[role="tab"]')[nextIdx]
  if (nextTab instanceof HTMLElement) nextTab.focus()
}

export default function MarketPortfolioPage({ sessionId, onOpenProLab, onOpenNews, onOpenLogin }) {
  const [tab, setTab] = useState('tong_quan')
  const needsSession = ['watchlist', 'lenh_giay', 'danh_muc'].includes(tab)
  const sessionMissing = needsSession && !sessionId

  const isTerminalTab = ['tong_quan', 'co_phieu', 'chi_so', 'ngoai_te'].includes(tab)
  const terminalActiveTab = tab === 'tong_quan' ? 'market_overview' : tab === 'chi_so' ? 'indices' : tab === 'ngoai_te' ? 'fx' : 'dashboard'

  const otherBody = useMemo(() => {
    if (sessionMissing) {
      return (
        <section className="mp-watchlist-locked" aria-labelledby="watchlist-login-title">
          <div className="mp-watchlist-locked__card">
            <span className="mp-watchlist-locked__icon" aria-hidden="true"><LockKeyhole size={22} strokeWidth={1.8} /></span>
            <span className="mp-watchlist-locked__eyebrow">KHÔNG GIAN CÁ NHÂN</span>
            <h2 id="watchlist-login-title">Đăng nhập để dùng {TABS.find((item) => item.id === tab)?.label}</h2>
            <p>Đăng nhập để lưu danh mục theo dõi và thực hành giao dịch mô phỏng.</p>
            <button type="button" onClick={onOpenLogin}>Đăng nhập</button>
          </div>
        </section>
      )
    }
    if (tab === 'watchlist') return <WatchlistPanel key={sessionId} sessionId={sessionId} />
    if (tab === 'lenh_giay') return <TradePanel key={sessionId} sessionId={sessionId} />
    if (tab === 'danh_muc') return <PortfolioPanel sessionId={sessionId} />
    if (tab === 'phai_sinh') return <DerivativesPanel />
    if (tab === 'tai_san_so') return <CryptoPanel />
    if (tab === 'hang_hoa') return <CommoditiesPanel />
    return null
  }, [tab, sessionId, sessionMissing, onOpenLogin])

  const allTabs = TABS

  return (
    <section className="mp-desk" aria-label="Market & Portfolio">
      <div className="mp-desk__toolbar">
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
      </div>

      </div>

      <div
        id="mp-desk-panel"
        className="mp-desk__panel"
        role="tabpanel"
        aria-labelledby={`mp-tab-${tab}`}
        tabIndex={0}
      >
        <div style={{ display: isTerminalTab && !sessionMissing ? 'block' : 'none', height: '100%' }}>
          <GlobalTerminalPage
            activeTab={terminalActiveTab}
            onOpenProLab={onOpenProLab}
            onOpenNews={onOpenNews}
          />
        </div>
        {!isTerminalTab || sessionMissing ? otherBody : null}
      </div>
    </section>
  )
}
