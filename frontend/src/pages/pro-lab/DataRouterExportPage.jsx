import { useState } from 'react'

const SOURCES = [
  { id: 'polygon', name: 'Polygon', domain: 'Prices', status: 'healthy', primary: 'Polygon WebSocket', fallback: 'Alpha Vantage', latency: '89ms', freshness: '< 1s', cache: '82%', errorRate: '0.02%' },
  { id: 'fmp', name: 'FinancialModelingPro', domain: 'Fundamentals', status: 'healthy', primary: 'FMP REST', fallback: 'SEC Edgar', latency: '340ms', freshness: '6h', cache: '91%', errorRate: '0.05%' },
  { id: 'alpha', name: 'Alpha Vantage', domain: 'News', status: 'fallback', primary: 'Alpha Vantage', fallback: 'NewsAPI', latency: '720ms', freshness: '45s', cache: '56%', errorRate: '0.31%' },
  { id: 'worldbank', name: 'World Bank', domain: 'Macro', status: 'healthy', primary: 'World Bank API', fallback: 'FRED', latency: '510ms', freshness: '24h', cache: '95%', errorRate: '0.01%' },
  { id: 'quandl', name: 'Quandl', domain: 'Alternative', status: 'degraded', primary: 'Quandl v3', fallback: 'Tiingo', latency: '1.2s', freshness: '4h', cache: '48%', errorRate: '0.89%' },
]

const ROUTED_TO = [
  { label: 'Prices', detail: 'Real-time & EOD' },
  { label: 'Financial Statements', detail: 'Daily' },
  { label: 'News', detail: 'Near Real-time' },
  { label: 'Macro', detail: 'Daily' },
  { label: 'Alternative Data', detail: 'EOD/Intraday' },
]

const EXPORT_FORMATS = [
  { id: 'markdown', label: 'Markdown Blueprint', ext: '.md', icon: '📄' },
  { id: 'python', label: 'Python Strategy Skeleton', ext: '.py', icon: '🐍' },
  { id: 'pine', label: 'Pine Script Skeleton', ext: '.pine', icon: '🌲' },
  { id: 'runbook', label: 'Runbook/Checklist', ext: '.md', icon: '📋' },
  { id: 'csv-json', label: 'CSV/JSON Package', ext: '.zip', icon: '📦' },
  { id: 'full', label: 'Full Export Bundle', ext: '.zip', icon: '🗂️' },
]

const CONFIG_ITEMS = [
  { id: 'params', label: 'Include Strategy Parameters', checked: true },
  { id: 'risk', label: 'Include Risk & Position Sizing', checked: true },
  { id: 'backtest', label: 'Include Backtest Results', checked: true },
  { id: 'visuals', label: 'Include Visuals & Charts', checked: true },
  { id: 'schema', label: 'Include Data Schema', checked: true },
  { id: 'citations', label: 'Include Citations & Links', checked: true },
]

const FILE_PREVIEW = [
  { name: 'strategy_blueprint.md', size: '21 KB' },
  { name: 'parameters.yaml', size: '8 KB' },
  { name: 'backtest_summary.md', size: '34 KB' },
  { name: 'equity_curve.png', size: '156 KB' },
]

export default function DataRouterExportPage({ onBack }) {
  const [selectedFormat, setSelectedFormat] = useState('markdown')
  const [configChecks, setConfigChecks] = useState(
    CONFIG_ITEMS.reduce((acc, item) => ({ ...acc, [item.id]: item.checked }), {})
  )

  const toggleConfig = (id) => {
    setConfigChecks((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const statusBadge = (status) => {
    const map = {
      healthy: { bg: 'rgba(16,185,129,0.15)', color: '#10b981', text: 'Healthy' },
      fallback: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', text: 'Fallback' },
      degraded: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444', text: 'Degraded' },
    }
    const s = map[status] || map.healthy
    return <span className="de-badge" style={{ background: s.bg, color: s.color }}>{s.text}</span>
  }

  return (
    <div className="de-page">
      {/* Breadcrumb */}
      <nav className="de-breadcrumb">
        <button className="de-breadcrumb__link" onClick={onBack}>Pro Lab</button>
        <span className="de-breadcrumb__sep">›</span>
        <span className="de-breadcrumb__current">Data Router + Export Lab</span>
      </nav>

      {/* Two-column layout */}
      <div className="de-columns">
        {/* LEFT — Data Router */}
        <section className="de-panel de-panel--router">
          <header className="de-panel__header">
            <div className="de-panel__icon">⚡</div>
            <div className="de-panel__titles">
              <h2 className="de-panel__title">Data Router</h2>
              <p className="de-panel__subtitle">Route, monitor, and validate your data pipeline across all domains.</p>
            </div>
            <span className="de-badge de-badge--operational">● All Systems Operational</span>
          </header>

          {/* Routing Map */}
          <div className="de-routing-map">
            <div className="de-routing-map__col de-routing-map__sources">
              <div className="de-routing-map__label">SOURCES</div>
              {SOURCES.map((s) => (
                <div key={s.id} className={`de-routing-map__node de-routing-map__node--${s.status}`}>
                  <span className="de-routing-map__node-name">{s.name}</span>
                  <span className="de-routing-map__node-domain">{s.domain}</span>
                </div>
              ))}
            </div>

            <div className="de-routing-map__col de-routing-map__center">
              <div className="de-routing-map__hub">
                <div className="de-routing-map__hub-title">Data Router</div>
                <div className="de-routing-map__hub-sub">Smart Routing</div>
                <div className="de-routing-map__hub-meta">Health + Latency + Cost</div>
              </div>
              {/* Connection lines (visual) */}
              <div className="de-routing-map__lines">
                {SOURCES.map((s, i) => (
                  <div key={i} className={`de-routing-map__line de-routing-map__line--${s.status === 'healthy' ? 'primary' : s.status === 'fallback' ? 'fallback' : 'degraded'}`} />
                ))}
              </div>
            </div>

            <div className="de-routing-map__col de-routing-map__targets">
              <div className="de-routing-map__label">ROUTED TO</div>
              {ROUTED_TO.map((t, i) => (
                <div key={i} className="de-routing-map__node de-routing-map__node--target">
                  <span className="de-routing-map__node-name">{t.label}</span>
                  <span className="de-routing-map__node-domain">{t.detail}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="de-legend">
            <span className="de-legend__item"><span className="de-legend__line de-legend__line--primary" /> Primary Route</span>
            <span className="de-legend__item"><span className="de-legend__line de-legend__line--fallback" /> Fallback Route</span>
            <span className="de-legend__item"><span className="de-legend__dot de-legend__dot--cache" /> Cache</span>
            <span className="de-legend__item"><span className="de-legend__dot de-legend__dot--degraded" /> Degraded</span>
          </div>

          {/* Source Status Table */}
          <div className="de-table-wrap">
            <table className="de-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Domain</th>
                  <th>Status</th>
                  <th>Primary</th>
                  <th>Fallback</th>
                  <th>Latency</th>
                  <th>Freshness</th>
                  <th>Cache</th>
                  <th>Error Rate</th>
                </tr>
              </thead>
              <tbody>
                {SOURCES.map((s) => (
                  <tr key={s.id}>
                    <td className="de-table__source">{s.name}</td>
                    <td>{s.domain}</td>
                    <td>{statusBadge(s.status)}</td>
                    <td>{s.primary}</td>
                    <td>{s.fallback}</td>
                    <td>{s.latency}</td>
                    <td>{s.freshness}</td>
                    <td>{s.cache}</td>
                    <td>{s.errorRate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Bottom Metrics */}
          <div className="de-metrics">
            <div className="de-metric">
              <span className="de-metric__value">98.6%</span>
              <span className="de-metric__label">Routing Health</span>
            </div>
            <div className="de-metric">
              <span className="de-metric__value">412ms</span>
              <span className="de-metric__label">Avg Latency</span>
            </div>
            <div className="de-metric">
              <span className="de-metric__value">12s</span>
              <span className="de-metric__label">Data Freshness</span>
            </div>
            <div className="de-metric">
              <span className="de-metric__value">74%</span>
              <span className="de-metric__label">Cache Hit Rate</span>
            </div>
            <div className="de-metric">
              <span className="de-metric__value">0.15%</span>
              <span className="de-metric__label">Error Rate</span>
            </div>
          </div>
        </section>

        {/* RIGHT — Export Lab */}
        <section className="de-panel de-panel--export">
          <header className="de-panel__header">
            <div className="de-panel__icon">📦</div>
            <div className="de-panel__titles">
              <h2 className="de-panel__title">Export Lab</h2>
              <p className="de-panel__subtitle">Package strategies, blueprints, and data into portable formats.</p>
            </div>
            <span className="de-badge de-badge--version">Template v2.4</span>
          </header>

          {/* Export Options */}
          <div className="de-export-options">
            <div className="de-export-options__label">Export Format</div>
            <div className="de-export-options__grid">
              {EXPORT_FORMATS.map((f) => (
                <button
                  key={f.id}
                  className={`de-format-card ${selectedFormat === f.id ? 'de-format-card--active' : ''}`}
                  onClick={() => setSelectedFormat(f.id)}
                >
                  <span className="de-format-card__icon">{f.icon}</span>
                  <span className="de-format-card__label">{f.label}</span>
                  <span className="de-format-card__ext">{f.ext}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Export Configuration */}
          <div className="de-export-config">
            <div className="de-export-config__label">Export Configuration</div>
            <div className="de-export-config__list">
              {CONFIG_ITEMS.map((item) => (
                <label key={item.id} className="de-check-item">
                  <span className={`de-check-item__circle ${configChecks[item.id] ? 'de-check-item__circle--checked' : ''}`}>
                    {configChecks[item.id] && '✓'}
                  </span>
                  <input
                    type="checkbox"
                    checked={configChecks[item.id]}
                    onChange={() => toggleConfig(item.id)}
                    className="de-check-item__input"
                  />
                  <span className="de-check-item__text">{item.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Package Summary */}
          <div className="de-summary">
            <div className="de-summary__title">Package Summary</div>
            <div className="de-summary__grid">
              <div className="de-summary__item"><span className="de-summary__key">Files</span><span className="de-summary__val">12</span></div>
              <div className="de-summary__item"><span className="de-summary__key">Size</span><span className="de-summary__val">1.42 MB</span></div>
              <div className="de-summary__item"><span className="de-summary__key">Format</span><span className="de-summary__val">Markdown Blueprint</span></div>
              <div className="de-summary__item de-summary__item--full">
                <span className="de-summary__key">Includes</span>
                <span className="de-summary__val">
                  {Object.entries(configChecks).filter(([, v]) => v).length} of {CONFIG_ITEMS.length} modules
                </span>
              </div>
            </div>
          </div>

          {/* File Preview */}
          <div className="de-file-preview">
            <div className="de-file-preview__label">File Preview</div>
            <div className="de-file-preview__list">
              {FILE_PREVIEW.map((f, i) => (
                <div key={i} className="de-file-card">
                  <span className="de-file-card__icon">📄</span>
                  <span className="de-file-card__name">{f.name}</span>
                  <span className="de-file-card__size">{f.size}</span>
                </div>
              ))}
              <div className="de-file-card de-file-card--more">
                <span className="de-file-card__icon">＋</span>
                <span className="de-file-card__name">8 more files</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="de-actions">
            <button className="de-btn de-btn--primary">
              <span className="de-btn__icon">⬇</span>
              Export Package
              <span className="de-btn__hint">Build and download</span>
            </button>
            <button className="de-btn de-btn--outline">
              <span className="de-btn__icon">📋</span>
              Copy Template
              <span className="de-btn__hint">Copy to clipboard</span>
            </button>
            <button className="de-btn de-btn--outline">
              <span className="de-btn__icon">🔗</span>
              Share to Report Builder
            </button>
          </div>
        </section>
      </div>

      <style>{`
        /* ═══════════════════════════════════════════════════════════
           Data Router + Export Lab — Dark Theme (de- prefix)
           ═══════════════════════════════════════════════════════════ */

        .de-page {
          min-height: 100vh;
          padding: clamp(1.2rem, 2.5vw, 2rem) clamp(1rem, 2vw, 1.6rem);
          color: #c8d6d2;
          background:
            radial-gradient(ellipse at 15% 0%, rgba(16, 70, 60, 0.3), transparent 55%),
            radial-gradient(ellipse at 85% 100%, rgba(8, 35, 45, 0.25), transparent 55%),
            #091210;
          font-family: "Avenir Next", "Inter", system-ui, sans-serif;
        }

        /* Breadcrumb */
        .de-breadcrumb {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1.5rem;
          font-size: 0.82rem;
        }
        .de-breadcrumb__link {
          background: none;
          border: none;
          color: #4fd1b4;
          cursor: pointer;
          padding: 0;
          font: inherit;
        }
        .de-breadcrumb__link:hover { text-decoration: underline; }
        .de-breadcrumb__sep { color: #3a5248; }
        .de-breadcrumb__current { color: #8fa8a0; }

        /* Two-column layout */
        .de-columns {
          display: grid;
          grid-template-columns: 1.1fr 0.9fr;
          gap: 1.5rem;
          max-width: 1720px;
          margin: 0 auto;
        }
        @media (max-width: 1100px) {
          .de-columns { grid-template-columns: 1fr; }
        }

        /* Panel */
        .de-panel {
          background: rgba(13, 25, 22, 0.85);
          border: 1px solid rgba(79, 209, 180, 0.08);
          border-radius: 14px;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }
        .de-panel__header {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          flex-wrap: wrap;
        }
        .de-panel__icon {
          font-size: 1.5rem;
          line-height: 1;
          margin-top: 0.1rem;
        }
        .de-panel__titles { flex: 1; min-width: 180px; }
        .de-panel__title {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 700;
          color: #ecf4f0;
        }
        .de-panel__subtitle {
          margin: 0.25rem 0 0;
          font-size: 0.78rem;
          color: #5e7a72;
          line-height: 1.4;
        }

        /* Badges */
        .de-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.2rem 0.6rem;
          border-radius: 20px;
          font-size: 0.7rem;
          font-weight: 600;
          white-space: nowrap;
        }
        .de-badge--operational {
          background: rgba(16, 185, 129, 0.12);
          color: #10b981;
        }
        .de-badge--version {
          background: rgba(99, 102, 241, 0.12);
          color: #a5b4fc;
        }

        /* Routing Map */
        .de-routing-map {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          gap: 1rem;
          align-items: center;
          padding: 1rem;
          background: rgba(0, 0, 0, 0.25);
          border-radius: 10px;
          border: 1px solid rgba(79, 209, 180, 0.06);
        }
        .de-routing-map__col {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .de-routing-map__label {
          font-size: 0.65rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #5e7a72;
          margin-bottom: 0.25rem;
        }
        .de-routing-map__node {
          display: flex;
          flex-direction: column;
          padding: 0.4rem 0.7rem;
          border-radius: 6px;
          background: rgba(79, 209, 180, 0.04);
          border: 1px solid rgba(79, 209, 180, 0.1);
        }
        .de-routing-map__node--healthy { border-color: rgba(16, 185, 129, 0.3); }
        .de-routing-map__node--fallback { border-color: rgba(245, 158, 11, 0.3); }
        .de-routing-map__node--degraded { border-color: rgba(239, 68, 68, 0.3); }
        .de-routing-map__node--target { border-color: rgba(99, 102, 241, 0.2); }
        .de-routing-map__node-name {
          font-size: 0.75rem;
          font-weight: 600;
          color: #d4e4de;
        }
        .de-routing-map__node-domain {
          font-size: 0.65rem;
          color: #5e7a72;
        }
        .de-routing-map__center {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }
        .de-routing-map__hub {
          padding: 0.8rem 1.2rem;
          border-radius: 10px;
          background: linear-gradient(135deg, rgba(79, 209, 180, 0.1), rgba(99, 102, 241, 0.08));
          border: 1px solid rgba(79, 209, 180, 0.2);
          text-align: center;
        }
        .de-routing-map__hub-title {
          font-size: 0.85rem;
          font-weight: 700;
          color: #4fd1b4;
        }
        .de-routing-map__hub-sub {
          font-size: 0.7rem;
          color: #8fa8a0;
          margin-top: 0.15rem;
        }
        .de-routing-map__hub-meta {
          font-size: 0.6rem;
          color: #5e7a72;
          margin-top: 0.1rem;
        }
        .de-routing-map__lines {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
          width: 60px;
        }
        .de-routing-map__line {
          height: 2px;
          border-radius: 1px;
        }
        .de-routing-map__line--primary { background: #10b981; }
        .de-routing-map__line--fallback { background: repeating-linear-gradient(90deg, #f59e0b 0 6px, transparent 6px 10px); }
        .de-routing-map__line--degraded { background: repeating-linear-gradient(90deg, #ef4444 0 4px, transparent 4px 8px); }

        /* Legend */
        .de-legend {
          display: flex;
          gap: 1.2rem;
          flex-wrap: wrap;
          font-size: 0.68rem;
          color: #5e7a72;
        }
        .de-legend__item {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
        }
        .de-legend__line {
          display: inline-block;
          width: 20px;
          height: 2px;
          border-radius: 1px;
        }
        .de-legend__line--primary { background: #10b981; }
        .de-legend__line--fallback { background: repeating-linear-gradient(90deg, #f59e0b 0 4px, transparent 4px 7px); }
        .de-legend__dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .de-legend__dot--cache { background: #6366f1; }
        .de-legend__dot--degraded { background: #ef4444; }

        /* Table */
        .de-table-wrap {
          overflow-x: auto;
          border-radius: 8px;
          border: 1px solid rgba(79, 209, 180, 0.06);
        }
        .de-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.72rem;
        }
        .de-table th {
          padding: 0.55rem 0.6rem;
          text-align: left;
          font-weight: 600;
          color: #5e7a72;
          background: rgba(0, 0, 0, 0.3);
          border-bottom: 1px solid rgba(79, 209, 180, 0.06);
          white-space: nowrap;
        }
        .de-table td {
          padding: 0.5rem 0.6rem;
          border-bottom: 1px solid rgba(79, 209, 180, 0.04);
          color: #a0b8b0;
          white-space: nowrap;
        }
        .de-table__source { color: #d4e4de; font-weight: 600; }
        .de-table tbody tr:hover { background: rgba(79, 209, 180, 0.03); }

        /* Metrics */
        .de-metrics {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
          gap: 0.75rem;
        }
        .de-metric {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 0.7rem 0.5rem;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 8px;
          border: 1px solid rgba(79, 209, 180, 0.06);
        }
        .de-metric__value {
          font-size: 1.1rem;
          font-weight: 700;
          color: #4fd1b4;
        }
        .de-metric__label {
          font-size: 0.65rem;
          color: #5e7a72;
          margin-top: 0.2rem;
        }

        /* Export Options */
        .de-export-options__label,
        .de-export-config__label,
        .de-summary__title,
        .de-file-preview__label {
          font-size: 0.75rem;
          font-weight: 600;
          color: #8fa8a0;
          margin-bottom: 0.6rem;
        }
        .de-export-options__grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
          gap: 0.5rem;
        }
        .de-format-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.3rem;
          padding: 0.7rem 0.5rem;
          border-radius: 8px;
          border: 1px solid rgba(79, 209, 180, 0.08);
          background: rgba(0, 0, 0, 0.2);
          cursor: pointer;
          transition: all 0.15s;
          font: inherit;
          color: inherit;
        }
        .de-format-card:hover {
          border-color: rgba(79, 209, 180, 0.2);
          background: rgba(79, 209, 180, 0.04);
        }
        .de-format-card--active {
          border-color: #4fd1b4;
          background: rgba(79, 209, 180, 0.08);
          box-shadow: 0 0 0 1px rgba(79, 209, 180, 0.15);
        }
        .de-format-card__icon { font-size: 1.3rem; }
        .de-format-card__label {
          font-size: 0.7rem;
          font-weight: 600;
          color: #d4e4de;
          text-align: center;
          line-height: 1.2;
        }
        .de-format-card__ext {
          font-size: 0.6rem;
          color: #5e7a72;
        }

        /* Export Config */
        .de-export-config__list {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }
        .de-check-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          font-size: 0.75rem;
          color: #a0b8b0;
        }
        .de-check-item__input {
          position: absolute;
          opacity: 0;
          pointer-events: none;
        }
        .de-check-item__circle {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          border: 1.5px solid rgba(79, 209, 180, 0.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.6rem;
          color: transparent;
          transition: all 0.15s;
          flex-shrink: 0;
        }
        .de-check-item__circle--checked {
          background: rgba(16, 185, 129, 0.15);
          border-color: #10b981;
          color: #10b981;
        }
        .de-check-item__text { line-height: 1.3; }

        /* Summary */
        .de-summary {
          padding: 0.8rem;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 8px;
          border: 1px solid rgba(79, 209, 180, 0.06);
        }
        .de-summary__grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.4rem 1rem;
        }
        .de-summary__item {
          display: flex;
          justify-content: space-between;
          font-size: 0.72rem;
        }
        .de-summary__item--full { grid-column: 1 / -1; }
        .de-summary__key { color: #5e7a72; }
        .de-summary__val { color: #d4e4de; font-weight: 600; }

        /* File Preview */
        .de-file-preview__list {
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }
        .de-file-card {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.45rem 0.6rem;
          border-radius: 6px;
          background: rgba(0, 0, 0, 0.15);
          border: 1px solid rgba(79, 209, 180, 0.05);
        }
        .de-file-card__icon { font-size: 0.9rem; }
        .de-file-card__name {
          flex: 1;
          font-size: 0.72rem;
          color: #d4e4de;
          font-family: "SF Mono", "Fira Code", monospace;
        }
        .de-file-card__size {
          font-size: 0.65rem;
          color: #5e7a72;
        }
        .de-file-card--more {
          border-style: dashed;
          border-color: rgba(79, 209, 180, 0.1);
        }
        .de-file-card--more .de-file-card__name { color: #5e7a72; }

        /* Actions */
        .de-actions {
          display: flex;
          gap: 0.6rem;
          flex-wrap: wrap;
          margin-top: auto;
          padding-top: 0.5rem;
        }
        .de-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.6rem 1rem;
          border-radius: 8px;
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          border: none;
          font: inherit;
          transition: all 0.15s;
        }
        .de-btn__icon { font-size: 0.9rem; }
        .de-btn__hint {
          font-size: 0.62rem;
          font-weight: 400;
          color: inherit;
          opacity: 0.6;
          margin-left: 0.2rem;
        }
        .de-btn--primary {
          background: linear-gradient(135deg, #10b981, #059669);
          color: #fff;
          box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
        }
        .de-btn--primary:hover {
          background: linear-gradient(135deg, #34d399, #10b981);
          box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
        }
        .de-btn--outline {
          background: transparent;
          color: #8fa8a0;
          border: 1px solid rgba(79, 209, 180, 0.15);
        }
        .de-btn--outline:hover {
          border-color: rgba(79, 209, 180, 0.35);
          color: #d4e4de;
          background: rgba(79, 209, 180, 0.04);
        }
      `}</style>
    </div>
  )
}
