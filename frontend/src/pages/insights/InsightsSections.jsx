import React from 'react'

import {
  AssetLine,
  Badge,
  Icon,
  SectionHeader,
  Sparkline,
  TimeFilter,
  statusTone,
  trendIcon,
  viewTone,
} from './InsightsPrimitives'

export function MarketIntelligenceHero({ summary, onReview }) {
  return (
    <header className="insights-v2-hero">
      <div className="insights-v2-hero__copy">
        <h1>Market Intelligence Summary</h1>
        <p>{summary.summary}</p>
        <div className="insights-v2-hero__actions">
          <button type="button" onClick={onReview}><Icon name="target" />Review exposure</button>
          <button type="button"><Icon name="scenario" />Open scenario</button>
          <button type="button"><Icon name="spark" />Ask Analyst</button>
        </div>
      </div>
      <div className="insights-v2-hero__badges">
        <Badge tone="amber"><Icon name="rates" />No buy/sell recommendation</Badge>
        <Badge tone="teal"><Icon name="globe" />Cross-asset active</Badge>
        <Badge tone="green"><Icon name="check" />Fresh data</Badge>
      </div>
      <RegimeRadar />
    </header>
  )
}

export function SnapshotRow({ summary }) {
  const cards = [
    { icon: 'pulse', label: 'Market Regime', value: summary.regime, subtext: 'Thận trọng', tone: 'amber' },
    { icon: 'shield', label: 'Risk Level', value: summary.riskLevel, subtext: 'Rủi ro theo dõi', tone: 'amber' },
    { icon: 'globe', label: 'Cross-Asset Theme', value: summary.crossAssetTheme, subtext: 'Lãi suất & USD dẫn dắt', tone: 'green' },
    { icon: 'bolt', label: 'Top Driver', value: summary.topDriver, subtext: 'Đồng USD mạnh', tone: 'green' },
    { icon: 'bell', label: 'Alerts', value: `${summary.alertsCount} active`, subtext: 'Cần theo dõi', tone: 'red' },
  ]
  return (
    <section className="snapshot-row">
      {cards.map((card) => <SnapshotCard key={card.label} card={card} />)}
    </section>
  )
}

export function MarketNarrativeCard({ narrative, loading }) {
  return (
    <article className="insights-v2-card market-narrative-card">
      <SectionHeader icon="spark" title="Today’s Market Narrative" action={<Badge tone="green">Confidence: {narrative.confidence}</Badge>} />
      <ul>
        {narrative.bullets.map((item) => <li key={item}><Icon name="check" />{loading ? 'Đang cập nhật bối cảnh thị trường...' : item}</li>)}
      </ul>
      <div className="monitor-block">
        <p>What to monitor</p>
        <div>
          {narrative.monitors.map((item) => <Badge key={item} tone="neutral">{item}</Badge>)}
        </div>
      </div>
    </article>
  )
}

export function TrendRadarCard({ rows }) {
  return (
    <article className="insights-v2-card trend-radar-card">
      <SectionHeader icon="radar" title="Trend Radar" />
      <div className="trend-radar-list">
        {rows.map((row) => <TrendRadarRow key={row.key} row={row} />)}
      </div>
    </article>
  )
}

export function CrossAssetPulseChart({ series, range, onRange }) {
  return (
    <article className="insights-v2-card cross-asset-card">
      <SectionHeader
        icon="chart"
        title="Cross-Asset Pulse"
        subtitle="Chuẩn hoá về 100 tại 21/04/2025"
        action={<TimeFilter active={range} onChange={onRange} />}
      />
      <div className="cross-asset-card__body">
        <div className="cross-asset-chart">
          <div className="cross-asset-chart__axis"><span>110</span><span>105</span><span>100</span><span>95</span><span>90</span></div>
          {series.map((item, index) => <AssetLine key={item.key} item={item} index={index} />)}
          <div className="cross-asset-chart__dates"><span>21 Apr</span><span>5 May</span><span>19 May</span><span>2 Jun</span><span>16 Jun</span></div>
        </div>
        <aside className="cross-asset-values">
          {series.map((item) => (
            <div key={item.key}>
              <span style={{ '--asset-color': item.color }} /> <p>{item.label}</p>
              <strong className={item.latest.startsWith('-') ? 'is-down' : 'is-up'}>{item.latest}</strong>
            </div>
          ))}
        </aside>
      </div>
    </article>
  )
}

export function ScenarioMonitorCard({ scenarios }) {
  return (
    <article className="insights-v2-card scenario-card">
      <SectionHeader icon="scenario" title="Scenario Monitor" />
      <div className="scenario-table">
        {scenarios.map((item) => (
          <div key={item.key} className="scenario-row">
            <span><Icon name="scenario" /></span>
            <div><strong>{item.name}</strong><p>{item.summary}</p></div>
            <b>{item.probability}%</b>
            <Badge tone={item.impact === 'High' ? 'red' : 'amber'}>{item.impact}</Badge>
          </div>
        ))}
      </div>
    </article>
  )
}

export function SectorRotationCard({ sectors }) {
  return (
    <article className="insights-v2-card sector-card">
      <SectionHeader icon="rotate" title="Sector Rotation" action={<div className="sector-legend"><span>Yếu</span><span>Trung tính</span><span>Mạnh</span></div>} />
      <div className="sector-list">
        {sectors.map((item) => (
          <div key={item.sector} className="sector-item">
            <strong>{item.sector}</strong>
            <Badge tone={viewTone(item.view)}>{item.view}</Badge>
            <div className="strength-bar"><i style={{ left: `${item.score}%` }} /></div>
          </div>
        ))}
      </div>
    </article>
  )
}

export function WatchlistImpactCard({ rows }) {
  return (
    <article className="insights-v2-card watchlist-card">
      <SectionHeader icon="target" title="Watchlist Impact" action={<button type="button" className="text-action">Xem tất cả</button>} />
      <div className="watchlist-table">
        <div className="watchlist-table__head"><span>Ticker</span><span>Theme bị ảnh hưởng</span><span>Mức độ</span><span>Ghi chú</span></div>
        {rows.map((row) => (
          <div key={row.ticker} className="watchlist-table__row">
            <strong>{row.ticker}</strong><span>{row.theme}</span><Badge tone={statusTone(row.level)}>{row.level}</Badge><p>{row.note}</p>
          </div>
        ))}
      </div>
    </article>
  )
}

export function LearnFromInsightsCard({ links, onOpen }) {
  return (
    <section className="learn-insights-card">
      <SectionHeader icon="book" title="Learn from Insights" subtitle="Kết nối bối cảnh hôm nay với Learn Hub." />
      <div className="learn-insights-card__grid">
        {links.map((link) => (
          <button key={link.id} type="button" onClick={onOpen}>
            <span><Icon name={link.id.includes('fx') ? 'globe' : link.id.includes('rates') ? 'rates' : 'rotate'} /></span>
            <strong>{link.title}</strong>
            <p>{link.subtext}</p>
            <em>{link.duration}</em>
            <Icon name="chevron" />
          </button>
        ))}
      </div>
    </section>
  )
}

export function EventCalendarCard({ events }) {
  return (
    <article className="insights-v2-card calendar-card">
      <SectionHeader icon="calendar" title="What to watch next" />
      <div>
        {events.map((event) => (
          <div key={`${event.date}-${event.name}`} className="event-row">
            <time>{event.date}</time>
            <p>{event.name}</p>
            <Badge tone={event.impact === 'Cao' ? 'red' : 'amber'}>{event.impact}</Badge>
          </div>
        ))}
      </div>
    </article>
  )
}

function RegimeRadar() {
  return (
    <div className="regime-radar" aria-label="Market regime radar visual">
      <span className="regime-radar__label regime-radar__label--left">Risk Off</span>
      <span className="regime-radar__label regime-radar__label--right">Risk On</span>
      <span className="regime-radar__label regime-radar__label--top">Growth</span>
      <span className="regime-radar__label regime-radar__label--bottom">Liquidity</span>
      <div className="regime-radar__ring" />
      <div className="regime-radar__needle" />
      <div className="regime-radar__core">
        <Icon name="spark" />
        <strong>Cautious</strong>
        <span>Market Regime</span>
      </div>
    </div>
  )
}

function SnapshotCard({ card }) {
  return (
    <article className="snapshot-card">
      <span className="snapshot-card__icon"><Icon name={card.icon} /></span>
      <div>
        <p>{card.label}</p>
        <strong>{card.value}</strong>
        <span>{card.subtext}</span>
      </div>
      <i className={`status-dot status-dot--${card.tone}`} />
      <Icon name="chevron" />
    </article>
  )
}

function TrendRadarRow({ row }) {
  return (
    <div className="trend-radar-row">
      <span className="trend-radar-row__icon"><Icon name={trendIcon(row.key)} /></span>
      <strong>{row.label}</strong>
      <b>{row.value}</b>
      <Sparkline values={row.series} />
      <Badge tone={statusTone(row.status)}>{row.status}</Badge>
      <p>{row.note}</p>
    </div>
  )
}
