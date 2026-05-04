import React, { useState } from "react";
import "./journal-report.css";

const JOURNAL_ENTRIES = [
  {
    action: "Long NVDA @ 945.30",
    details: { Buy: "5.35", R: "1.8", Thesis: "Breakout above resistance on volume" },
    tag: "Plan Followed",
    tagColor: "green",
    dot: "",
  },
  {
    action: "Added NVDA @ 951.10",
    details: { Size: "+2 contracts", Note: "Scaled in after confirmation candle" },
    tag: "Oversize",
    tagColor: "yellow",
    dot: "warn",
  },
  {
    action: "Short TSLA @ 178.40",
    details: { Sell: "3.20", R: "1.2", Thesis: "Breakdown below 180 support" },
    tag: "Rule Break",
    tagColor: "red",
    dot: "danger",
  },
  {
    action: "Closed NVDA @ 961.75",
    details: { P_L: "+$1,645", Duration: "2h 15m" },
    tag: "Plan Followed",
    tagColor: "green",
    dot: "",
  },
  {
    action: "Closed TSLA @ 175.90",
    details: { P_L: "+$529", Duration: "45m" },
    tag: "Rule Break",
    tagColor: "red",
    dot: "danger",
  },
];

const DETECTED_ISSUES = [
  { name: "FOMO Entry", count: 14, icon: "✗", severity: "red" },
  { name: "Oversize Position", count: 9, icon: "⚠", severity: "yellow" },
  { name: "Early Exit", count: 7, icon: "✗", severity: "red" },
  { name: "Revenge Trade", count: 4, icon: "⚠", severity: "yellow" },
];

const OUTLINE_SECTIONS = [
  { num: 1, title: "Hypothesis" },
  { num: 2, title: "Experiment Setup" },
  { num: 3, title: "Results" },
  { num: 4, title: "Caveats" },
  { num: 5, title: "Next Steps" },
];

const REPORT_CONTENT = [
  {
    title: "1. Hypothesis",
    text: "Mean reversion strategies should outperform momentum strategies during elevated volatility regimes (VIX > 25). The hypothesis rests on the observation that during high-volatility periods, overreactions create larger dislocations from fair value, which subsequently revert faster than during low-volatility environments.",
  },
  {
    title: "2. Experiment Setup",
    text: "Universe: S&P 500 constituents. Period: 2018–2025. Signal: 5-day z-score of returns. Entry: z-score < −2.0 (long) or > 2.0 (short). Exit: z-score returns to ±0.5 band or 10-day holding cap. Risk: max 2% per position, 15% gross exposure. Regime filter: VIX > 25 = active, VIX ≤ 25 = inactive (flat).",
  },
  {
    title: "3. Results",
    text: "Annualized return: 14.2% (vs. 9.8% for momentum baseline). Sharpe ratio: 1.42 (vs. 0.87). Max drawdown: −8.7% (vs. −16.3%). Win rate: 62.4%. The strategy was active for approximately 28% of trading days, concentrated in Q4 2018, Q1 2020, and Q2–Q3 2022.",
  },
  {
    title: "4. Caveats",
    text: "Backtest uses close-to-close returns, not intraday. Transaction costs modeled at 5 bps, which may understate slippage during high-vol periods. Survivorship bias partially mitigated via point-in-time constituent lists but not fully eliminated. Regime classification is binary and may miss transition periods.",
  },
  {
    title: "5. Next Steps",
    text: "Run walk-forward analysis on 2023–2025 out-of-sample data. Test non-binary regime filters (e.g., VIX percentile buckets). Explore sector-level mean reversion for higher granularity. Paper trade for 30 days before any capital allocation.",
  },
];

const SOURCE_ATTACHMENTS = [
  { name: "mean_reversion_backtest.csv", size: "241 KB", icon: "📊" },
  { name: "volatility_regime_analysis.pdf", size: "1.8 MB", icon: "📄" },
  { name: "sp500_constituents_pit.xlsx", size: "512 KB", icon: "📋" },
  { name: "strategy_comparison_chart.png", size: "89 KB", icon: "🖼" },
];

const DISCIPLINE_CHART_POINTS = [
  65, 68, 62, 70, 72, 69, 74, 71, 75, 73,
  70, 68, 72, 76, 74, 71, 78, 75, 73, 77,
  72, 74, 70, 68, 73, 76, 80, 78, 74, 72,
];

function DisciplineChart() {
  const pts = DISCIPLINE_CHART_POINTS;
  const max = Math.max(...pts);
  const min = Math.min(...pts);
  const range = max - min || 1;
  const w = 100;
  const h = 100;
  const pad = 4;

  const polyline = pts
    .map((v, i) => {
      const x = pad + (i / (pts.length - 1)) * (w - 2 * pad);
      const y = h - pad - ((v - min) / range) * (h - 2 * pad);
      return `${x},${y}`;
    })
    .join(" ");

  const areaPath =
    `M ${pad},${h - pad} ` +
    pts
      .map((v, i) => {
        const x = pad + (i / (pts.length - 1)) * (w - 2 * pad);
        const y = h - pad - ((v - min) / range) * (h - 2 * pad);
        return `L ${x},${y}`;
      })
      .join(" ") +
    ` L ${w - pad},${h - pad} Z`;

  return (
    <div className="jr-chart">
      <h4 className="jr-chart__title">Discipline Score Over Time (30D)</h4>
      <div className="jr-chart__canvas">
        <svg className="jr-chart__svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="jr-area-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(79,209,180,0.25)" />
              <stop offset="100%" stopColor="rgba(79,209,180,0.02)" />
            </linearGradient>
          </defs>
          {[0, 25, 50, 75, 100].map((pct) => {
            const y = h - pad - (pct / 100) * (h - 2 * pad) * (range / (max - min + range * 0.1));
            return (
              <line
                key={pct}
                x1={pad}
                x2={w - pad}
                y1={y}
                y2={y}
                stroke="rgba(79,209,180,0.06)"
                strokeWidth="0.3"
              />
            );
          })}
          <path d={areaPath} fill="url(#jr-area-grad)" />
          <polyline
            points={polyline}
            fill="none"
            stroke="#4fd1b4"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>
      <div className="jr-chart__labels">
        <span>Apr 3</span>
        <span>Apr 17</span>
        <span>May 2</span>
      </div>
    </div>
  );
}

export default function JournalReportPage({ onBack }) {
  const [bookmarked, setBookmarked] = useState(false);
  const [activeOutline, setActiveOutline] = useState(0);
  const [notesContent] = useState(
    "Good day overall. Followed my plan on NVDA very well — entered at the right level, managed size properly on the add, and took profit at target. The TSLA short was more impulsive, entered before the setup fully confirmed. Need to be more disciplined on waiting for confirmation before pulling the trigger on counter-trend plays."
  );

  return (
    <div className="jr">
      {/* Header */}
      <header className="jr-header">
        <nav className="jr-breadcrumb">
          <button className="jr-breadcrumb__link" onClick={onBack}>
            Pro Lab
          </button>
          <span className="jr-breadcrumb__sep">›</span>
          <span className="jr-breadcrumb__current">
            Journal Lab + Report Builder
          </span>
        </nav>
        <button
          className={`jr-bookmark${bookmarked ? " is-active" : ""}`}
          onClick={() => setBookmarked((b) => !b)}
          title="Bookmark"
        >
          {bookmarked ? "★" : "☆"}
        </button>
      </header>

      {/* Two-column layout */}
      <div className="jr-layout">
        {/* ═══ LEFT — Journal Lab ═══ */}
        <div className="jr-col">
          <div className="jr-card">
            {/* Section header */}
            <div className="jr-section-header">
              <div className="jr-section-header__left">
                <span className="jr-section-icon">📓</span>
                <div>
                  <h2 className="jr-card__title">Journal Lab</h2>
                  <p className="jr-card__sub">
                    Trade journal &amp; shadow account review
                  </p>
                </div>
              </div>
              <div className="jr-section-header__right">
                <select className="jr-select">
                  <option>Shadow Account A</option>
                  <option>Shadow Account B</option>
                  <option>Shadow Account C</option>
                </select>
                <button className="jr-icon-btn" title="Filter">
                  🔍
                </button>
              </div>
            </div>

            {/* Metric Cards */}
            <div className="jr-metrics-grid">
              <div className="jr-metric">
                <p className="jr-metric__label">Discipline Score (30D)</p>
                <p className="jr-metric__value">
                  72/100{" "}
                  <span
                    className="jr-badge jr-badge--green"
                    style={{ fontSize: "0.6rem", verticalAlign: "middle", marginLeft: "0.4rem" }}
                  >
                    Good
                  </span>
                </p>
                <p className="jr-metric__detail jr-metric__detail--up">
                  ↑ 8.4 vs prior 30D
                </p>
              </div>

              <div className="jr-metric">
                <p className="jr-metric__label">Tagged Events (30D)</p>
                <p className="jr-metric__value">42</p>
                <div className="jr-dots">
                  <span className="jr-dot">
                    <span className="jr-dot__circle" style={{ background: "#10b981" }} />
                    12
                  </span>
                  <span className="jr-dot">
                    <span className="jr-dot__circle" style={{ background: "#f59e0b" }} />
                    14
                  </span>
                  <span className="jr-dot">
                    <span className="jr-dot__circle" style={{ background: "#f97316" }} />
                    3
                  </span>
                  <span className="jr-dot">
                    <span className="jr-dot__circle" style={{ background: "#ef4444" }} />
                    9
                  </span>
                  <span className="jr-dot">
                    <span className="jr-dot__circle" style={{ background: "#6b7280" }} />
                    7
                  </span>
                </div>
              </div>

              <div className="jr-metric">
                <p className="jr-metric__label">Best Day (P&amp;L)</p>
                <p className="jr-metric__value">$2,174</p>
                <p className="jr-metric__detail">May 9, 2025</p>
              </div>

              <div className="jr-metric">
                <p className="jr-metric__label">Total Trades</p>
                <p className="jr-metric__value">87</p>
                <p className="jr-metric__detail">Win Rate: 54.0%</p>
              </div>
            </div>
          </div>

          {/* Journal Timeline */}
          <div className="jr-card">
            <h3 className="jr-card__title" style={{ marginBottom: "0.75rem" }}>
              Journal Timeline
            </h3>
            <div className="jr-timeline">
              {JOURNAL_ENTRIES.map((entry, i) => (
                <div key={i} className="jr-timeline__item">
                  <div
                    className={`jr-timeline__dot${
                      entry.dot ? ` jr-timeline__dot--${entry.dot}` : ""
                    }`}
                  />
                  <p className="jr-timeline__action">{entry.action}</p>
                  <div className="jr-timeline__details">
                    {Object.entries(entry.details).map(([k, v]) => (
                      <span key={k}>
                        <span className="jr-muted">{k.replace("_", "/")}:</span> {v}
                      </span>
                    ))}
                    <span
                      className={`jr-timeline__tag jr-timeline__tag--${entry.tagColor}`}
                    >
                      {entry.tag}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <button className="jr-timeline__link">+ View full journal →</button>
          </div>

          {/* Discipline Chart */}
          <DisciplineChart />

          {/* Detected Issues */}
          <div className="jr-card">
            <div className="jr-issues__header">
              <h3 className="jr-issues__title">Detected Issues (30D)</h3>
              <button className="jr-link">View all Issues →</button>
            </div>
            <div className="jr-issues">
              {DETECTED_ISSUES.map((issue) => (
                <div key={issue.name} className="jr-issue">
                  <div className="jr-issue__left">
                    <span
                      className={`jr-issue__icon jr-issue__icon--${issue.severity}`}
                    >
                      {issue.icon}
                    </span>
                    <span className="jr-issue__name">{issue.name}</span>
                  </div>
                  <span className="jr-issue__count">
                    {issue.count} occurrences
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Reflective Notes */}
          <div className="jr-card jr-notes">
            <div className="jr-card__head">
              <h3 className="jr-card__title">Reflective Notes</h3>
              <select className="jr-select" style={{ fontSize: "0.72rem" }}>
                <option>Templates</option>
                <option>Daily Review</option>
                <option>Weekly Summary</option>
                <option>Trade Debrief</option>
              </select>
            </div>
            <div className="jr-notes__toolbar">
              <button className="jr-notes__toolbar-btn"><b>B</b></button>
              <button className="jr-notes__toolbar-btn"><i>I</i></button>
              <button className="jr-notes__toolbar-btn"><u>U</u></button>
              <span className="jr-notes__toolbar-sep" />
              <button className="jr-notes__toolbar-btn">≡</button>
              <button className="jr-notes__toolbar-btn">☰</button>
              <span className="jr-notes__toolbar-sep" />
              <button className="jr-notes__toolbar-btn">🔗</button>
              <button className="jr-notes__toolbar-btn">📎</button>
            </div>
            <div className="jr-notes__body" contentEditable suppressContentEditableWarning>
              {notesContent}
            </div>
            <div className="jr-notes__footer">
              <span>Auto-saved | 10:32 AM</span>
              <span>{notesContent.length} characters</span>
            </div>
          </div>
        </div>

        {/* ═══ RIGHT — Report Builder ═══ */}
        <div className="jr-col">
          <div className="jr-card">
            {/* Report Header */}
            <div className="jr-section-header">
              <div>
                <h2 className="jr-card__title">Report Builder</h2>
                <p className="jr-card__sub">
                  Structured research memo builder
                </p>
              </div>
              <div className="jr-report-actions">
                <button className="jr-btn jr-btn--ghost jr-btn--sm">
                  Save Memo
                </button>
                <button className="jr-btn jr-btn--primary jr-btn--sm">
                  Generate Report
                </button>
                <button className="jr-btn jr-btn--purple jr-btn--sm">
                  Publish Internal Note ▶
                </button>
              </div>
            </div>

            {/* Memo Title */}
            <div className="jr-report-meta">
              <h3 className="jr-report-title">
                Memo: Mean Reversion in High Volatility Regimes
                <button className="jr-icon-btn" style={{ marginLeft: "0.4rem" }}>✏️</button>
              </h3>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "1rem" }}>
              <span className="jr-report-saved">Last saved: 10:32 AM</span>
              <span className="jr-badge jr-badge--draft">Draft</span>
            </div>

            {/* Outline + Content */}
            <div className="jr-report-body">
              <div className="jr-outline">
                {OUTLINE_SECTIONS.map((sec, i) => (
                  <div
                    key={sec.num}
                    className={`jr-outline__item${activeOutline === i ? " is-active" : ""}`}
                    onClick={() => setActiveOutline(i)}
                  >
                    <span>
                      <span className="jr-outline__num">{sec.num}.</span>
                      {sec.title}
                    </span>
                    <button className="jr-outline__edit">Edit</button>
                  </div>
                ))}
              </div>

              <div className="jr-content-sections">
                {REPORT_CONTENT.map((section) => (
                  <div key={section.title} className="jr-content-section">
                    <h4 className="jr-content-section__title">
                      {section.title}
                    </h4>
                    <p className="jr-content-section__text">{section.text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Source Attachments */}
            <div className="jr-attachments">
              <h4 className="jr-attachments__title">Source Attachments</h4>
              {SOURCE_ATTACHMENTS.map((file) => (
                <div key={file.name} className="jr-attachment">
                  <div className="jr-attachment__left">
                    <span className="jr-attachment__icon">{file.icon}</span>
                    <span className="jr-attachment__name">{file.name}</span>
                  </div>
                  <span className="jr-attachment__size">{file.size}</span>
                </div>
              ))}
            </div>

            {/* Generated Executive Summary */}
            <div className="jr-exec-summary">
              <h4 className="jr-exec-summary__title">
                ✨ Generated Executive Summary
              </h4>
              <p className="jr-exec-summary__text">
                This memo examines the performance of mean reversion strategies during elevated
                volatility regimes (VIX &gt; 25) across S&amp;P 500 constituents from 2018 to 2025.
                The analysis demonstrates that mean reversion significantly outperforms momentum
                approaches during high-vol periods, achieving a 14.2% annualized return with a
                Sharpe ratio of 1.42 versus the momentum baseline of 9.8% and 0.87 respectively.
                The strategy was active for approximately 28% of all trading days, concentrated
                in known volatility events.
              </p>
              <ul className="jr-exec-summary__bullets">
                <li>Annualized return: 14.2% (vs. 9.8% momentum baseline)</li>
                <li>Sharpe ratio: 1.42 (vs. 0.87)</li>
                <li>Max drawdown: −8.7% (vs. −16.3%)</li>
                <li>Win rate: 62.4% across 847 round-trip trades</li>
                <li>Active 28% of trading days during VIX &gt; 25 regimes</li>
              </ul>
            </div>

            {/* Conclusion */}
            <div className="jr-conclusion">
              <span className="jr-conclusion__icon">✓</span>
              <p className="jr-conclusion__text">
                Mean reversion should be favored in elevated volatility regimes with strict
                risk controls. The strategy demonstrates statistically significant alpha during
                VIX &gt; 25 periods while maintaining manageable drawdown characteristics.
                Recommended for paper trading validation before live deployment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
