import { useState, useMemo } from 'react'
import {
  AnalysisTable,
  PeerTable,
  BalanceStatementTable,
  CashFlowStatementTable,
  RatioStatementTable,
  SimplizeDataTable,
  SimplizeDataViewToggle,
  StudentNotePanel,
  IncomeAssistantCard,
  BalanceAssistantCard,
  CashFlowAssistantCard,
  RatioAssistantCard,
  EvidenceBadge,
  formatCompactNumber,
  formatPercent,
  formatMaybeNumber,
  formatSignedPercent,
  growthPercent,
} from './BctcTables'
import {
  BalanceAssetStackChart,
  BalanceFundingDonut,
  BalanceLiquidityChart,
  CashWaterfallChart,
  CashFlowTrendChart,
  CashQualityLineChart,
  RatioTrendChart,
  RatioGroupCard,
} from './BctcCharts'
import { MetricTrendChart } from './BctcOverview'

const BCTC_TABS = [
  { key: 'overview', label: 'Tổng quan' },
  { key: 'income', label: 'Kết quả kinh doanh' },
  { key: 'balance', label: 'Bảng cân đối kế toán' },
  { key: 'cash-flow', label: 'Lưu chuyển tiền tệ' },
  { key: 'ratios', label: 'Chỉ số tài chính' },
  { key: 'horizontal', label: 'Phân tích ngang' },
  { key: 'vertical', label: 'Phân tích dọc' },
  { key: 'risk', label: 'Cảnh báo rủi ro' },
  { key: 'report', label: 'Báo cáo' },
]

const REVENUE_INCOME_METRICS = [
  { key: 'revenue', label: 'Doanh thu thuần', color: '#16a16f', type: 'bar', scale: 'left', formatValue: formatCompactNumber },
  { key: 'net_income', label: 'LNST', color: '#1f4e79', type: 'bar', scale: 'left', formatValue: formatCompactNumber },
  { key: 'net_margin', label: 'Biên lợi nhuận ròng', color: '#f0a202', type: 'line', scale: 'right', formatValue: formatPercent },
]

const MARGIN_METRICS = [
  { key: 'gross_margin', label: 'Biên gộp', color: '#16a16f', type: 'line', formatValue: formatPercent },
  { key: 'operating_margin', label: 'Biên HĐKD', color: '#2f74d0', type: 'line', formatValue: formatPercent },
  { key: 'net_margin', label: 'Biên ròng', color: '#7b61d9', type: 'line', formatValue: formatPercent },
]

export default function BctcSectionPanel({
  section,
  analysis,
  dashboard,
  trendRows,
  healthRows,
  mode,
  onChangeMode,
  comparisonMode,
  onChangeComparisonMode,
  peerLoading,
  onRowClick,
  cockpit,
  extractionResult,
}) {
  const [dataViewMode, setDataViewMode] = useState('absolute')
  const tab = BCTC_TABS.find((item) => item.key === section) || BCTC_TABS[0]
  const latest = latestPeriod(analysis) || {}

  if (section === 'income') {
    const incomeCards = buildIncomeKpiCards(dashboard, latest, analysis?.summary)
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

        <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {incomeCards.map((item, idx) => (
            <article key={idx} className="p-4.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 flex items-center justify-center font-bold text-sm shrink-0">{item.icon}</div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] text-slate-500 dark:text-zinc-450 uppercase font-bold truncate">{item.label}</p>
                <h3 className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5 leading-none">{item.value}</h3>
                <span className="block text-[10px] text-teal-650 dark:text-teal-450 mt-1 truncate">{item.delta}</span>
              </div>
              <Sparkline tone={item.tone} values={item.sparkValues} />
            </article>
          ))}
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
          <div className="flex flex-col gap-6">
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-zinc-850">
                <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Xu hướng doanh thu, giá vốn, lợi nhuận gộp và LNST</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400">{modeLabel(mode)}</span>
              </header>
              <MetricTrendChart rows={trendRows} metrics={REVENUE_INCOME_METRICS} formatValue={formatCompactNumber} height={250} showEndpointLabels />
            </article>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-zinc-850">
                <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Xu hướng biên lợi nhuận (%)</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400">{analysis?.latest_period || 'Latest'}</span>
              </header>
              <MetricTrendChart rows={dashboard.marginRows} metrics={MARGIN_METRICS} formatValue={formatPercent} height={250} showEndpointLabels />
            </article>

            <div className="flex flex-col gap-3">
              <SimplizeDataViewToggle viewMode={dataViewMode} onChange={setDataViewMode} />
              <SimplizeDataTable
                title="Báo cáo kết quả kinh doanh"
                data={analysis}
                lines={[
                  { key: 'revenue', label: 'Doanh thu thuần', isEmphasis: true, ratioBaseKey: 'revenue' },
                  { key: 'cogs', label: 'Giá vốn hàng bán', ratioBaseKey: 'revenue' },
                  { key: 'grossProfit', label: 'Lợi nhuận gộp', isEmphasis: true, ratioBaseKey: 'revenue' },
                  { key: 'grossMarginPct', label: 'Biên gộp (%)', format: (val) => formatPercent(val) },
                  { key: 'ebit', label: 'EBIT', ratioBaseKey: 'revenue' },
                  { key: 'netIncome', label: 'LNST', isEmphasis: true, ratioBaseKey: 'revenue' },
                  { key: 'netMarginPct', label: 'Biên ròng (%)', format: (val) => formatPercent(val) },
                ]}
                viewMode={dataViewMode}
                onRowClick={onRowClick}
              />
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <IncomeAssistantCard dashboard={dashboard} />
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">Điểm nhấn</h2>
                <p className="text-xs text-slate-500 mt-0.5">Những tín hiệu đáng chú ý từ kỳ gần nhất.</p>
              </div>
              <ul className="flex flex-col gap-3">
                {dashboard.summaryBullets.slice(0, 3).map((item, idx) => (
                  <li key={idx} className={`p-3 rounded-xl border flex gap-3 items-start text-xs ${
                    item.tone === 'warn'
                      ? 'bg-amber-50/50 dark:bg-amber-950/10 border-amber-200 dark:border-amber-900/20 text-amber-800'
                      : 'bg-slate-50 dark:bg-zinc-950/20 border-slate-200/50 text-slate-650'
                  }`}>
                    <span className="font-extrabold text-sm">{item.tone === 'warn' ? '!' : '↗'}</span>
                    <p className="leading-relaxed">{item.text}</p>
                  </li>
                ))}
              </ul>
            </article>
            <WhatIfSimulator analysis={analysis} />
            <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Kết quả kinh doanh" />
          </div>
        </section>
      </section>
    )
  }

  if (section === 'balance') {
    const balanceCards = buildBalanceKpiCards(dashboard, latest, analysis)
    const balanceRows = buildBalancePeriodRows(analysis)
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

        <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {balanceCards.map((item, idx) => (
            <article key={idx} className="p-4.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-teal-50 dark:bg-teal-950/20 text-teal-650 dark:text-teal-400 flex items-center justify-center font-bold text-sm shrink-0">{item.icon}</div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] text-slate-500 dark:text-zinc-450 uppercase font-bold truncate">{item.label}</p>
                <h3 className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5 leading-none">{item.value}</h3>
                <span className="block text-[10px] text-teal-650 dark:text-teal-455 mt-1 truncate">{item.delta}</span>
              </div>
            </article>
          ))}
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
                <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                  <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Cơ cấu nguồn vốn</h2>
                </header>
                <BalanceFundingDonut rows={balanceRows} latest={latest} />
              </article>

              <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
                <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                  <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Cấu trúc tài sản (TTT)</h2>
                </header>
                <BalanceAssetStackChart rows={balanceRows} />
              </article>
            </div>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Khả năng thanh khoản & Vốn lưu động</h2>
              </header>
              <BalanceLiquidityChart rows={balanceRows} />
            </article>

            <BalanceStatementTable rows={balanceRows} onRowClick={onRowClick} />
          </div>

          <div className="flex flex-col gap-6">
            <BalanceAssistantCard dashboard={dashboard} />
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">Điểm nhấn Bảng cân đối</h2>
                <p className="text-xs text-slate-500 mt-0.5">Phân tích nhanh cấu trúc tài sản & nguồn vốn.</p>
              </div>
              <ul className="flex flex-col gap-3">
                {buildBalanceHighlights(dashboard, latest).map((item, idx) => (
                  <li key={idx} className={`p-3 rounded-xl border flex gap-3 items-start text-xs ${
                    item.tone === 'warn'
                      ? 'bg-amber-50/50 dark:bg-amber-950/10 border-amber-200 dark:border-amber-900/20 text-amber-800'
                      : 'bg-slate-50 dark:bg-zinc-950/20 border-slate-200/50 text-slate-655'
                  }`}>
                    <span className="font-extrabold text-sm">{item.icon}</span>
                    <p className="leading-relaxed">{item.text}</p>
                  </li>
                ))}
              </ul>
            </article>
            <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Bảng cân đối kế toán" />
          </div>
        </section>
      </section>
    )
  }

  if (section === 'cash-flow') {
    const cashRows = buildCashFlowPeriodRows(analysis, dashboard.cashFlow)
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
                <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                  <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Biến động tiền mặt (Thác tiền kỳ gần nhất)</h2>
                </header>
                <CashWaterfallChart rows={cashRows} />
              </article>

              <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
                <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                  <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Biến động dòng tiền (CFO, CFI, CFF, FCF)</h2>
                </header>
                <CashFlowTrendChart rows={cashRows} />
              </article>
            </div>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Chỉ tiêu chuyển hóa & Capex</h2>
              </header>
              <CashQualityLineChart rows={cashRows} />
            </article>

            <CashFlowStatementTable rows={cashRows} />
          </div>

          <div className="flex flex-col gap-6">
            <CashFlowAssistantCard />
            <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Lưu chuyển tiền tệ" />
          </div>
        </section>
      </section>
    )
  }

  if (section === 'ratios') {
    const ratioRows = buildBalancePeriodRows(analysis)
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {dashboard.ratioGroups?.map((group) => (
                <RatioGroupCard key={group.title} group={group} />
              ))}
            </div>

            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
                <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Xu hướng chỉ số tài chính</h2>
              </header>
              <RatioTrendChart rows={ratioRows} />
            </article>

            <RatioStatementTable rows={ratioRows} />
          </div>

          <div className="flex flex-col gap-6">
            <RatioAssistantCard />
            <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Chỉ số tài chính" />
          </div>
        </section>
      </section>
    )
  }

  if (section === 'horizontal') {
    const horizontalData = buildHorizontalAnalysisRows(analysis)
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />
        <AnalysisTable
          title="Phân tích ngang (Tăng trưởng các kỳ)"
          columns={['Chỉ tiêu', 'Kỳ trước', 'Kỳ hiện tại', 'Thay đổi', 'Tỷ lệ %']}
          rows={horizontalData}
          onRowClick={onRowClick}
        />
        <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Phân tích ngang" />
      </section>
    )
  }

  if (section === 'vertical') {
    const verticalData = buildVerticalAnalysisRows(analysis, latest, dashboard.summary)
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />
        <AnalysisTable
          title="Phân tích dọc (Common-size)"
          columns={['Chỉ tiêu', 'Số tiền', 'Tỷ lệ % doanh thu / nguồn vốn']}
          rows={verticalData}
          onRowClick={onRowClick}
        />
        <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Phân tích dọc" />
      </section>
    )
  }

  if (section === 'risk') {
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
          <div className="flex flex-col gap-6">
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">Kiểm tra dấu hiệu bất thường (Red Flags)</h2>
                <p className="text-xs text-slate-500 mt-0.5">Phát hiện tự động từ cấu trúc tài chính và dòng tiền.</p>
              </div>
              <ul className="flex flex-col gap-3">
                {analysis.flags?.map((flag, idx) => (
                  <li key={idx} className={`p-4 rounded-xl border flex flex-col gap-1.5 ${
                    flag.level === 'high' || flag.level === 'danger'
                      ? 'bg-red-50/50 dark:bg-red-950/10 border-red-200 dark:border-red-900/20 text-red-800 dark:text-red-400'
                      : 'bg-amber-50/50 dark:bg-amber-950/10 border-amber-200 dark:border-amber-900/20 text-amber-800 dark:text-amber-400'
                  }`}>
                    <strong className="text-xs font-bold uppercase tracking-wide flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-current" />
                      {flag.title}
                    </strong>
                    <p className="text-xs leading-relaxed opacity-90">{flag.detail}</p>
                  </li>
                ))}
                {!analysis.flags?.length && <p className="text-xs text-slate-550 italic text-center py-6">Chưa phát hiện dấu hiệu bất thường nghiêm trọng nào.</p>}
              </ul>
            </article>

            {peerLoading ? (
              <p className="text-xs text-slate-450 italic py-4 text-center">Đang so sánh peer...</p>
            ) : dashboard.peerCompareRows?.length > 0 ? (
              <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">So sánh cùng nhóm ngành (Peers Compare)</h2>
                  <p className="text-xs text-slate-550 mt-0.5">So sánh hiệu quả hoạt động với các doanh nghiệp cùng ngành.</p>
                </div>
                <PeerTable rows={dashboard.peerCompareRows} />
              </article>
            ) : null}
          </div>

          <div className="flex flex-col gap-6">
            <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
              <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Mức độ rủi ro tổng thể</h3>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 flex flex-col gap-2">
                <span className="text-[10px] text-slate-450 uppercase font-bold">Risk classification</span>
                <strong className="text-lg font-extrabold text-teal-605 dark:text-teal-400">{analysis.risk_level || 'Hợp lý'}</strong>
                <p className="text-[11px] text-slate-550 leading-relaxed mt-1">{analysis.risk_summary || 'Các chỉ số tài chính cơ bản đang nằm trong vùng an toàn.'}</p>
              </div>
            </article>
            <StudentNotePanel companyId={analysis?.ticker || ''} period={analysis?.latest_period} sectionName="Cảnh báo rủi ro" />
          </div>
        </section>
      </section>
    )
  }

  if (section === 'report') {
    return (
      <section className="flex flex-col gap-6" aria-label={tab.label}>
        <BctcSectionControlBand
          analysis={analysis}
          dashboard={dashboard}
          mode={mode}
          onChangeMode={onChangeMode}
          comparisonMode={comparisonMode}
          onChangeComparisonMode={onChangeComparisonMode}
        />
        <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
          <header className="pb-2 border-b border-slate-100 dark:border-zinc-850">
            <h2 className="text-sm font-bold text-slate-805 dark:text-white">Bảng BCTC nguồn</h2>
          </header>
          <BctcSourceStatementPreview analysis={analysis} cockpit={cockpit} extractionResult={extractionResult} />
        </article>
      </section>
    )
  }

  return <p className="text-xs text-slate-450 py-4">Chưa phát triển view này.</p>
}

function BctcSectionControlBand({ analysis, dashboard, mode, onChangeMode, comparisonMode, onChangeComparisonMode }) {
  return (
    <section className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div className="flex items-center gap-3.5 min-w-0">
        <div className="w-11 h-11 rounded-xl bg-teal-50 dark:bg-teal-950/20 text-teal-605 dark:text-teal-400 border border-teal-100 dark:border-teal-900/30 flex items-center justify-center font-extrabold text-base shrink-0">{(analysis?.ticker || 'FPT').slice(0, 3)}</div>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            {dashboard.companyName}
            {analysis?.source?.startsWith('upload') && (
              <span className="inline-block px-2 py-0.5 rounded bg-yellow-100 dark:bg-yellow-950/30 text-yellow-800 dark:text-yellow-405 text-[9px] font-bold">
                Mô phỏng BCTC
              </span>
            )}
          </h2>
          <p className="text-[10px] text-slate-500 mt-1">{analysis?.source?.startsWith('upload') ? 'Dữ liệu học tập/thực hành' : `Ngành: ${analysis?.industry || 'Công nghệ thông tin'} · ${dashboard.exchange}`}: {analysis?.ticker || 'FPT'}</p>
        </div>
      </div>
      <div className="flex gap-4 flex-wrap text-xs">
        <label className="flex items-center gap-2 font-semibold text-slate-500">
          <span>Kỳ báo cáo</span>
          <select className="rounded border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 outline-none text-xs font-bold" value={mode === 'quarter' ? 'quarter' : 'year'} onChange={(event) => onChangeMode(event.target.value)}>
            <option value="quarter">Quý</option>
            <option value="year">Năm</option>
          </select>
        </label>
        <label className="flex items-center gap-2 font-semibold text-slate-500">
          <span>So sánh với</span>
          <select className="rounded border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-2 py-1 outline-none text-xs font-bold" value={comparisonMode} onChange={(event) => onChangeComparisonMode(event.target.value)}>
            <option value="same-period">Cùng kỳ năm trước</option>
            <option value="previous-period">Kỳ liền trước</option>
          </select>
        </label>
      </div>
    </section>
  )
}

function WhatIfSimulator({ analysis }) {
  const [revenueChange, setRevenueChange] = useState(0)
  const [marginChange, setMarginChange] = useState(0)

  const latest = analysis?.periods?.[0] || {}
  const currentRev = Number(latest.revenue) || 0
  const currentNetMargin = Number(latest.net_margin_pct) || 0
  const currentNetIncome = Number(latest.net_income) || 0

  const simRev = currentRev * (1 + revenueChange / 100)
  const simNetMargin = currentNetMargin + marginChange
  const simNetIncome = simRev * (simNetMargin / 100)
  const diff = simNetIncome - currentNetIncome

  return (
    <article className="p-5 rounded-2xl border border-dashed border-slate-250 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-950/20 flex flex-col gap-4 mt-2">
      <h3 className="text-sm font-bold text-slate-900 dark:text-white">Mô phỏng tác động (What-If)</h3>
      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-1.5 text-xs text-slate-500 font-semibold">
          <span>Tăng/giảm Doanh thu: <strong className="text-teal-650 dark:text-teal-400 font-extrabold">{revenueChange > 0 ? '+' : ''}{revenueChange}%</strong></span>
          <input className="w-full h-1.5 bg-slate-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer" type="range" min="-50" max="50" step="5" value={revenueChange} onChange={(e) => setRevenueChange(Number(e.target.value))} />
        </label>
        <label className="flex flex-col gap-1.5 text-xs text-slate-500 font-semibold">
          <span>Tăng/giảm Biên gộp: <strong className="text-teal-650 dark:text-teal-400 font-extrabold">{marginChange > 0 ? '+' : ''}{marginChange}%</strong></span>
          <input className="w-full h-1.5 bg-slate-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer" type="range" min="-20" max="20" step="1" value={marginChange} onChange={(e) => setMarginChange(Number(e.target.value))} />
        </label>
        <div className="p-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-slate-200/80 dark:border-zinc-800 flex flex-col text-xs leading-relaxed">
          <span className="text-[10px] text-slate-500 uppercase font-bold">LNST Dự phóng:</span>
          <strong className="text-base font-extrabold text-slate-900 dark:text-white mt-1">{formatCompactNumber(simNetIncome)}</strong>
          <p className={`text-[10px] font-bold mt-2 ${diff >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
             {diff >= 0 ? '▲' : '▼'} {formatCompactNumber(Math.abs(diff))} so với hiện tại
          </p>
        </div>
      </div>
    </article>
  )
}

function roundSvg(val) {
  return Math.round(val * 10) / 10
}

function Sparkline({ tone, values = [] }) {
  const clean = values.map((value) => Number(value)).filter(Number.isFinite).slice(-10)
  const fallback = [12, 13, 12.5, 15, 14.4, 17, 16.2, 18, 17.4, 19]
  const series = clean.length >= 2 ? clean : fallback
  const min = Math.min(...series)
  const max = Math.max(...series)
  const span = max - min || Math.max(Math.abs(max), 1)
  const width = 86
  const height = 26
  const left = 2
  const top = 4
  const step = width / Math.max(1, series.length - 1)
  const nodes = series.map((value, index) => ({
    x: left + step * index,
    y: top + height - ((value - min) / span) * height,
    latest: index === series.length - 1,
  }))
  const points = nodes.map((node) => `${roundSvg(node.x)},${roundSvg(node.y)}`).join(' ')

  return (
    <svg className="w-16 h-8 bg-transparent" viewBox="0 0 90 34" aria-hidden="true">
      <polyline points={points} fill="none" className={`stroke-2 ${
        tone === 'good' ? 'stroke-emerald-500' :
        tone === 'warn' ? 'stroke-red-500' : 'stroke-slate-400'
      }`} />
      {nodes.map((node, idx) => (
        <circle key={idx} cx={node.x} cy={node.y} r={node.latest ? 2.5 : 1.5} className={
          tone === 'good' ? 'fill-emerald-500' :
          tone === 'warn' ? 'fill-red-500' : 'fill-slate-400'
        } />
      ))}
    </svg>
  )
}

function BctcSourceStatementPreview({ analysis, cockpit, extractionResult }) {
  const report = buildSourceStatementReport(analysis, cockpit, extractionResult)
  return (
    <article className="flex flex-col gap-4">
      <div>
        <span className="text-[10px] text-slate-450 uppercase font-bold">{report.hasData ? 'BCTC đã đọc' : 'Chưa có bảng nguồn'}</span>
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">{report.title}</h3>
        <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{report.subtitle}</p>
      </div>

      {report.hasData ? (
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse text-[11px] md:text-xs">
            <thead>
              <tr className="border-b border-slate-200 dark:border-zinc-800">
                {report.columns.map((column) => (
                  <th className="p-2.5 font-semibold text-slate-500 dark:text-zinc-450 text-right first:text-left" key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {report.rows.map((row, idx) => (
                row.type === 'section' ? (
                  <tr key={row.key} className="border-b border-slate-205 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950/40">
                    <th colSpan={report.columns.length} className="p-2 text-left font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[10px]">{row.label}</th>
                  </tr>
                ) : (
                  <tr key={row.key} className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${row.isTotal ? 'font-bold bg-slate-50/50 dark:bg-zinc-900' : ''}`}>
                    <td className="p-2.5 text-slate-900 dark:text-white font-medium">
                      <span>{row.label}</span>
                      {row.note && <small className="block text-[9px] text-slate-550 mt-0.5 font-normal">{row.note}</small>}
                    </td>
                    <td className="p-2.5 text-right font-semibold text-slate-700 dark:text-zinc-350">{formatCompactNumber(row.current)}</td>
                    <td className="p-2.5 text-right font-semibold text-slate-700 dark:text-zinc-355">{formatCompactNumber(row.compare)}</td>
                    <td className="p-2.5 text-right font-semibold text-teal-605 dark:text-teal-400">{formatSignedPercent(row.changePct)}</td>
                    <td className="p-2.5 text-right font-semibold text-slate-700 dark:text-zinc-350">{formatCompactNumber(row.ytdCurrent)}</td>
                    <td className="p-2.5 text-right font-semibold text-slate-700 dark:text-zinc-355">{formatCompactNumber(row.ytdCompare)}</td>
                    <td className="p-2.5 text-right font-semibold text-teal-605 dark:text-teal-400">{formatSignedPercent(row.ytdChangePct)}</td>
                    <td className="p-2.5 text-right"><EvidenceBadge evidence={row.evidence} derived={row.derived} /></td>
                    <td className="p-2.5 text-right text-slate-500 dark:text-zinc-450 italic">{row.chart}</td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-6 rounded-xl border border-dashed border-slate-200 dark:border-zinc-800 text-center flex flex-col gap-1.5" role="status">
          <strong className="text-xs font-bold text-slate-805 dark:text-white">Chưa đọc được các dòng BCTC nguồn.</strong>
          <span className="text-[10px] text-slate-500 max-w-md mx-auto">Hãy bấm “Phân tích BCTC” hoặc kiểm tra pipeline dữ liệu; chart sẽ chỉ có ý nghĩa khi các dòng doanh thu, LNST, CFO và bảng cân đối được nạp vào đây.</span>
        </div>
      )}
    </article>
  )
}

function latestPeriod(analysis) {
  return analysis?.periods?.[0] || null
}

function modeLabel(mode) {
  if (mode === 'quarter') return 'Theo quý'
  if (mode === 'month') return 'Theo tháng'
  if (mode === 'period') return 'Theo kỳ'
  return 'Theo năm'
}

function trendTone(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  if (numeric < 0) return 'warn'
  if (numeric >= 10) return 'good'
  return 'caution'
}

function scoreTone(value, warnThreshold, goodThreshold) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  if (numeric < warnThreshold) return 'warn'
  if (numeric >= goodThreshold) return 'good'
  return 'caution'
}

function buildIncomeStatementTableRows(analysis, dashboard) {
  const latestRows = [...(analysis?.periods || [])].slice(-4)
  const summary = analysis?.summary || {}
  const latest = latestRows.at(-1) || latestPeriod(analysis) || {}
  const revenue = firstNumber(latest.revenue, summary.revenue)
  const netIncome = firstNumber(latest.net_income, summary.net_income)
  const grossMargin = firstNumber(latest.gross_margin_pct, summary.gross_margin_pct)
  const grossProfit = Number.isFinite(revenue) && Number.isFinite(grossMargin) ? revenue * grossMargin / 100 : null
  const cogs = Number.isFinite(revenue) && Number.isFinite(grossProfit) ? revenue - grossProfit : null
  const ebit = firstNumber(latest.ebit, latest.operating_income, summary.ebit)

  return [
    ['Doanh thu thuần', formatCompactNumber(revenue), `${formatPercent(summary.revenue_growth_yoy_pct)} YoY`],
    ['Giá vốn hàng bán', formatCompactNumber(cogs), 'Ước tính từ biên gộp nếu dữ liệu thiếu'],
    ['Lợi nhuận gộp', formatCompactNumber(grossProfit), `${formatPercent(grossMargin)} biên gộp`],
    ['EBIT', formatCompactNumber(ebit), 'Lợi nhuận trước lãi vay và thuế'],
    ['LNST', formatCompactNumber(netIncome), `${formatPercent(summary.net_income_growth_yoy_pct)} YoY`],
    ['Biên ròng', formatPercent(firstNumber(latest.net_margin_pct, summary.net_margin_pct)), 'LNST / Doanh thu thuần'],
    ['Quality read', `${dashboard.healthScore}/100`, 'Đọc cùng dòng tiền và bảng cân đối'],
  ]
}

function buildSourceStatementReport(analysis, cockpit, extractionResult) {
  const periods = [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      return Number(a.quarter || 0) - Number(b.quarter || 0)
    })
  const latest = periods.at(-1) || null
  const compare = latest ? sameQuarterPreviousYear(periods, latest) || periods.at(-2) || null : null
  const latestLabel = normalizePeriodLabel(latest || {})
  const compareLabel = normalizePeriodLabel(compare || {})
  const ytdLabels = buildYtdLabels(latest, compare)
  const columns = [
    { key: 'line_item', label: 'Khoản mục BCTC' },
    { key: 'current', label: latestLabel || 'Kỳ hiện tại' },
    { key: 'compare', label: compareLabel || 'Kỳ so sánh' },
    { key: 'change', label: 'Thay đổi' },
    { key: 'ytd_current', label: ytdLabels.current },
    { key: 'ytd_compare', label: ytdLabels.compare },
    { key: 'ytd_change', label: 'Thay đổi' },
    { key: 'source', label: 'Nguồn' },
    { key: 'chart', label: 'Chart dùng' },
  ]
  const evidenceByMetric = buildExtractionEvidenceMap(extractionResult)
  const rowGroups = [
    {
      key: 'income',
      label: 'Kết quả kinh doanh',
      rows: [
        { key: 'revenue', label: 'Doanh thu thuần', chart: 'Tăng trưởng', tone: 'income', total: true },
        { key: 'cogs', label: 'Giá vốn hàng bán', note: 'Ước tính = Doanh thu - Lợi nhuận gộp nếu BCTC thiếu dòng gốc', chart: 'Biên gộp', tone: 'income', derived: true },
        { key: 'gross_profit', label: 'Lợi nhuận gộp', chart: 'Biên gộp', tone: 'income' },
        { key: 'operating_profit', fallback: 'ebit', label: 'Lợi nhuận HĐKD / EBIT', chart: 'Biên HĐKD', tone: 'income' },
        { key: 'net_income', label: 'LNST', chart: 'Lợi nhuận', tone: 'income', total: true },
      ],
    },
    {
      key: 'balance',
      label: 'Bảng cân đối kế toán',
      rows: [
        { key: 'cash', label: 'Tiền & tương đương tiền', chart: 'Thanh khoản', tone: 'balance' },
        { key: 'receivables', label: 'Phải thu khách hàng', chart: 'Chất lượng tài sản', tone: 'balance' },
        { key: 'inventory', label: 'Hàng tồn kho', chart: 'Hiệu quả vốn lưu động', tone: 'balance' },
        { key: 'current_assets', label: 'Tài sản ngắn hạn', chart: 'Thanh khoản', tone: 'balance' },
        { key: 'fixed_assets', label: 'Tài sản cố định', chart: 'Cấu trúc tài sản', tone: 'balance' },
        { key: 'total_assets', fallback: 'assets', label: 'Tổng tài sản', chart: 'Bảng cân đối', tone: 'balance', total: true },
        { key: 'current_liabilities', label: 'Nợ ngắn hạn', chart: 'Rủi ro thanh khoản', tone: 'balance' },
        { key: 'non_current_liabilities', label: 'Nợ dài hạn', chart: 'Cấu trúc vốn', tone: 'balance' },
        { key: 'total_liabilities', fallback: 'liabilities', label: 'Nợ phải trả', chart: 'Rủi ro', tone: 'balance', total: true },
        { key: 'equity', label: 'Vốn chủ sở hữu', chart: 'Đòn bẩy', tone: 'balance', total: true },
      ],
    },
    {
      key: 'cashflow',
      label: 'Lưu chuyển tiền tệ',
      rows: [
        { key: 'operating_cash_flow', label: 'CFO - Dòng tiền HĐKD', chart: 'Dòng tiền', tone: 'cashflow', total: true },
        { key: 'investing_cash_flow', label: 'CFI - Dòng tiền đầu tư', chart: 'Dòng tiền', tone: 'cashflow' },
        { key: 'financing_cash_flow', label: 'CFF - Dòng tiền tài chính', chart: 'Dòng tiền', tone: 'cashflow' },
        { key: 'capex', label: 'CAPEX', chart: 'FCF', tone: 'cashflow' },
        { key: 'free_cash_flow', label: 'FCF', note: 'Ước tính = CFO - |CAPEX| nếu provider chưa có sẵn', chart: 'Chất lượng lợi nhuận', tone: 'cashflow', total: true },
      ],
    },
  ]
  const reportRows = rowGroups.flatMap((group) => [
    { type: 'section', key: `section-${group.key}`, label: group.label },
    ...group.rows.map((line) => buildStatementReportRow(line, periods, latest, compare, evidenceByMetric)),
  ])
  const cockpitRows = Object.values(cockpit?.statement_tables || {}).flatMap((table) => table?.rows || [])
  const hasData = reportRows.some((row) => row.type !== 'section' && [
    row.current,
    row.compare,
    row.ytdCurrent,
    row.ytdCompare,
  ].some((value) => Number.isFinite(value))) || cockpitRows.some((row) => Number.isFinite(firstNumber(...(row.values || []))))
  return {
    title: `Bảng BCTC nguồn ${analysis?.ticker || cockpit?.ticker || ''}`.trim(),
    subtitle: 'Parse từ Word/PDF/scan/provider về dạng bảng có cấu trúc, để chart lấy đúng dòng số liệu thay vì tự “đoán”.',
    unit: normalizeUnitLabel(analysis?.unit || cockpit?.unit),
    columns,
    rows: reportRows,
    hasData,
  }
}

function buildStatementReportRow(line, periods, latest, compare, evidenceByMetric = new Map()) {
  const current = statementValue(latest, line)
  const compareValue = statementValue(compare, line)
  const ytdCurrent = ytdStatementValue(periods, latest, line)
  const ytdCompare = ytdStatementValue(periods, compare, line)
  return {
    type: 'line',
    key: line.key,
    label: line.label,
    note: line.note,
    chart: line.chart,
    tone: line.tone,
    isTotal: line.total,
    current,
    compare: compareValue,
    changePct: growthPct(current, compareValue),
    ytdCurrent,
    ytdCompare,
    ytdChangePct: growthPct(ytdCurrent, ytdCompare),
    evidence: evidenceByMetric.get(line.key) || (line.fallback ? evidenceByMetric.get(line.fallback) : null),
    derived: line.derived,
  }
}

function buildExtractionEvidenceMap(extractionResult) {
  const rows = (extractionResult?.raw_tables || []).flatMap((table) => table?.rows || [])
  const evidence = new Map()
  rows.forEach((row) => {
    const metric = row?.metric
    if (!metric || evidence.has(metric)) return
    evidence.set(metric, {
      page: row.page,
      confidence: row.confidence,
      label: row.label,
      code: row.code,
    })
  })
  return evidence
}

function statementValue(period, line) {
  if (!period) return null
  if (line.key === 'cogs') {
    const revenue = firstNumber(period.revenue)
    const grossProfit = firstNumber(period.gross_profit)
    return Number.isFinite(revenue) && Number.isFinite(grossProfit) ? revenue - grossProfit : null
  }
  if (line.key === 'free_cash_flow') {
    const cfo = firstNumber(period.operating_cash_flow, period.cfo)
    const capex = firstNumber(period.capex)
    return Number.isFinite(cfo) && Number.isFinite(capex) ? cfo - Math.abs(capex) : null
  }
  return firstNumber(period[line.key], line.fallback ? period[line.fallback] : null)
}

function ytdStatementValue(periods, anchor, line) {
  if (!anchor?.year) return null
  const quarter = Number(anchor.quarter)
  const yearlyRows = periods.filter((item) => Number(item.year) === Number(anchor.year))
  const rows = Number.isFinite(quarter) && quarter > 0
    ? yearlyRows.filter((item) => Number(item.quarter || 0) > 0 && Number(item.quarter) <= quarter)
    : yearlyRows
  if (!rows.length) return null
  const flowKeys = new Set(['revenue', 'cogs', 'gross_profit', 'operating_profit', 'ebit', 'net_income', 'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'capex', 'free_cash_flow'])
  if (!flowKeys.has(line.key)) return statementValue(anchor, line)
  const values = rows.map((item) => statementValue(item, line)).filter((value) => Number.isFinite(value))
  if (!values.length) return null
  return values.reduce((total, value) => total + value, 0)
}

function sameQuarterPreviousYear(periods, anchor) {
  if (!anchor?.year) return null
  const targetYear = Number(anchor.year) - 1
  const targetQuarter = Number(anchor.quarter || 0)
  return periods.find((item) => Number(item.year) === targetYear && Number(item.quarter || 0) === targetQuarter) || null
}

function buildYtdLabels(latest, compare) {
  const latestQuarter = Number(latest?.quarter || 0)
  const compareQuarter = Number(compare?.quarter || latestQuarter || 0)
  if (latest?.year && latestQuarter > 0) {
    return {
      current: `${latestQuarter * 3}T${latest.year}`,
      compare: compare?.year ? `${(compareQuarter || latestQuarter) * 3}T${compare.year}` : 'Lũy kế so sánh',
    }
  }
  return { current: 'Lũy kế hiện tại', compare: 'Lũy kế so sánh' }
}

function growthPct(current, base) {
  const currentNumber = Number(current)
  const baseNumber = Number(base)
  if (!Number.isFinite(currentNumber) || !Number.isFinite(baseNumber) || baseNumber === 0) return null
  return ((currentNumber - baseNumber) / Math.abs(baseNumber)) * 100
}

function normalizeUnitLabel(unit) {
  const normalized = String(unit || '').trim().toLowerCase()
  if (!normalized || normalized === 'ty_vnd' || normalized === 'billion_vnd') return 'tỷ VND'
  return unit
}

function normalizePeriodLabel(item) {
  if (!item?.year) return ''
  return item.quarter ? `Q${item.quarter}/${item.year}` : String(item.year)
}

function buildBalancePeriodRows(analysis) {
  return [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => {
      const ay = Number(a.year || 0)
      const by = Number(b.year || 0)
      if (ay !== by) return ay - by
      return Number(a.quarter || 0) - Number(b.quarter || 0)
    })
    .map((item) => {
      const totalAssets = firstNumber(item.total_assets, item.assets)
      const currentAssets = firstNumber(item.current_assets, totalAssets ? totalAssets * 0.55 : null)
      const currentLiabilities = firstNumber(item.current_liabilities, item.short_term_debt, item.total_liabilities ? item.total_liabilities * 0.58 : null)
      const inventory = firstNumber(item.inventory, currentAssets ? currentAssets * 0.1 : null)
      const cash = firstNumber(item.cash, currentAssets ? currentAssets * 0.28 : null)
      const receivables = firstNumber(item.receivables, currentAssets ? currentAssets * 0.34 : null)
      const fixedAssets = firstNumber(item.fixed_assets, totalAssets && currentAssets ? Math.max(0, (totalAssets - currentAssets) * 0.68) : null)
      const totalLiabilities = firstNumber(item.total_liabilities, item.liabilities)
      const equity = firstNumber(item.equity)
      const shortTermDebt = firstNumber(item.short_term_debt, currentLiabilities)
      const longTermDebt = firstNumber(item.long_term_debt, totalLiabilities && shortTermDebt ? totalLiabilities - shortTermDebt : null)
      const workingCapital = Number.isFinite(currentAssets) && Number.isFinite(currentLiabilities) ? currentAssets - currentLiabilities : null
      const currentRatio = Number.isFinite(currentAssets) && Number.isFinite(currentLiabilities) && currentLiabilities !== 0 ? currentAssets / currentLiabilities : null
      const quickRatio = Number.isFinite(currentAssets) && Number.isFinite(inventory) && Number.isFinite(currentLiabilities) && currentLiabilities !== 0
        ? (currentAssets - inventory) / currentLiabilities
        : null
      return {
        period: normalizePeriodLabel(item),
        rawPeriod: item.period,
        year: item.year,
        quarter: item.quarter,
        cash,
        receivables,
        inventory,
        currentAssets,
        fixedAssets,
        otherAssets: totalAssets && currentAssets && fixedAssets ? Math.max(0, totalAssets - currentAssets - fixedAssets) : null,
        totalAssets,
        shortTermDebt,
        longTermDebt,
        totalLiabilities,
        equity,
        workingCapital,
        currentRatio,
        quickRatio,
        debtToEquity: Number.isFinite(totalLiabilities) && Number.isFinite(equity) && equity !== 0 ? totalLiabilities / equity : null,
      }
    })
    .filter((item) => Number.isFinite(item.totalAssets) || Number.isFinite(item.equity) || Number.isFinite(item.totalLiabilities))
}

function buildBalanceHighlights(dashboard, latest) {
  const assets = firstNumber(latest.total_assets, latest.assets)
  const cash = firstNumber(latest.cash)
  const equity = firstNumber(latest.equity)
  return [
    {
      icon: '↗',
      tone: 'good',
      text: `Tiền & tương đương tiền ở mức ${formatCompactNumber(cash)}, cần đọc cùng nợ ngắn hạn để đánh giá thanh khoản.`,
    },
    {
      icon: '⚖',
      tone: Number(dashboard.leverageMetrics[2]?.value) > 1 ? 'warn' : 'good',
      text: `Debt/Equity hiện ${dashboard.leverageMetrics[2]?.value || 'n/a'}, dùng để đánh giá mức độ đòn bẩy tài chính.`,
    },
    {
      icon: '★',
      tone: 'good',
      text: `Vốn chủ sở hữu ${formatCompactNumber(equity)} trên tổng tài sản ${formatCompactNumber(assets)} cho biết nền tảng vốn của doanh nghiệp.`,
    },
  ]
}

function buildCashFlowPeriodRows(analysis, cashFlow = {}) {
  const qualityPoints = cashFlow?.backend?.points || []
  const pointByPeriod = new Map(qualityPoints.map((item) => [String(item.period || ''), item]))
  const sorted = [...(analysis?.periods || [])].sort((a, b) => String(a.period || '').localeCompare(String(b.period || '')))
  return sorted
    .map((item) => {
      const pLabel = normalizePeriodLabel(item)
      const qPoint = pointByPeriod.get(pLabel) || pointByPeriod.get(item.period) || {}
      const cfo = firstNumber(item.operating_cash_flow, item.cfo, qPoint.cfo)
      const cfi = firstNumber(item.investing_cash_flow, item.cfi, qPoint.cfi)
      const cff = firstNumber(item.financing_cash_flow, item.cff, qPoint.cff)
      const capex = firstNumber(item.capex, qPoint.capex)
      const cash = firstNumber(item.cash, item.cash_and_equivalents)
      const netIncome = firstNumber(item.net_income)
      const depreciation = firstNumber(item.depreciation_and_amortization, item.depreciation)
      const workingCapitalChange = firstNumber(item.working_capital_change, item.change_in_working_capital)
      return {
        period: pLabel,
        rawPeriod: item.period,
        year: item.year,
        quarter: item.quarter,
        cfo,
        cfi,
        cff,
        capex,
        fcf: Number.isFinite(cfo) && Number.isFinite(capex) ? cfo - Math.abs(capex) : firstNumber(item.free_cash_flow, qPoint.fcf),
        cash,
        netIncome,
        depreciation,
        workingCapitalChange,
        dividends: firstNumber(item.dividends_paid, item.dividends),
        netBorrowing: firstNumber(item.net_borrowing),
        openingCash: firstNumber(item.opening_cash),
        fxOther: firstNumber(item.fx_other, item.effect_of_forex),
        ocfToNetIncome: Number.isFinite(cfo) && Number.isFinite(netIncome) && netIncome !== 0 ? cfo / netIncome : null,
        capexRatio: Number.isFinite(capex) && Number.isFinite(cfo) && cfo > 0 ? (Math.abs(capex) / cfo) * 100 : null,
        cashConversion: Number.isFinite(cfo) && Number.isFinite(netIncome) && netIncome > 0 ? (cfo / netIncome) * 100 : null,
      }
    })
    .filter((item) => Number.isFinite(item.cfo) || Number.isFinite(item.cash))
}

function buildHorizontalAnalysisRows(analysis) {
  const periods = [...(analysis?.periods || [])].sort((a, b) => Number(a.year) - Number(b.year) || Number(a.quarter) - Number(b.quarter))
  if (periods.length < 2) return []
  const latest = periods.at(-1)
  const prev = periods.at(-2)
  const lines = [
    ['revenue', 'Doanh thu thuần'],
    ['gross_profit', 'Lợi nhuận gộp'],
    ['operating_profit', 'Lợi nhuận HĐKD'],
    ['net_income', 'LNST'],
    ['operating_cash_flow', 'Dòng tiền HĐKD (CFO)'],
    ['total_assets', 'Tổng tài sản'],
    ['total_liabilities', 'Tổng nợ phải trả'],
    ['equity', 'Vốn chủ sở hữu'],
  ]
  return lines.map(([key, label]) => {
    const prevVal = prev[key] ?? null
    const curVal = latest[key] ?? null
    const diff = Number.isFinite(curVal) && Number.isFinite(prevVal) ? curVal - prevVal : null
    const pct = Number.isFinite(curVal) && Number.isFinite(prevVal) && prevVal !== 0 ? (diff / Math.abs(prevVal)) * 100 : null
    return [
      label,
      formatCompactNumber(prevVal),
      formatCompactNumber(curVal),
      diff >= 0 ? `+${formatCompactNumber(diff)}` : formatCompactNumber(diff),
      pct !== null ? formatSignedPercent(pct) : '—',
    ]
  })
}

function buildVerticalAnalysisRows(analysis, latest, summary = {}) {
  const revenue = firstNumber(latest.revenue, summary.revenue, 1)
  const assets = firstNumber(latest.total_assets, latest.assets, 1)
  const commonSize = (val, base) => (Number.isFinite(val) && Number(base) > 0 ? (val / base) * 100 : null)
  return [
    ['Doanh thu thuần', formatCompactNumber(revenue), '100%'],
    ['Giá vốn hàng bán', formatCompactNumber(firstNumber(latest.cogs, revenue - latest.gross_profit)), formatPercent(commonSize(firstNumber(latest.cogs, revenue - latest.gross_profit), revenue))],
    ['Lợi nhuận gộp', formatCompactNumber(latest.gross_profit), formatPercent(commonSize(latest.gross_profit, revenue))],
    ['LNST', formatCompactNumber(latest.net_income), formatPercent(commonSize(latest.net_income, revenue))],
    ['CFO', formatCompactNumber(latest.operating_cash_flow), formatPercent(commonSize(latest.operating_cash_flow, revenue))],
    ['Tổng tài sản', formatCompactNumber(assets), '100%'],
    ['Nợ phải trả', formatCompactNumber(latest.total_liabilities), formatPercent(commonSize(latest.total_liabilities, assets))],
    ['Vốn chủ sở hữu', formatCompactNumber(latest.equity), formatPercent(commonSize(latest.equity, assets))],
  ]
}

function buildIncomePeriodRows(analysis) {
  return [...(analysis?.periods || [])]
    .slice()
    .sort((a, b) => Number(a.year) - Number(b.year) || Number(a.quarter) - Number(b.quarter))
    .map((item) => {
      const revenue = firstNumber(item.revenue)
      const netIncome = firstNumber(item.net_income)
      const grossMarginPct = firstNumber(item.gross_margin_pct)
      const grossProfit = Number.isFinite(revenue) && Number.isFinite(grossMarginPct) ? (revenue * grossMarginPct) / 100 : firstNumber(item.gross_profit)
      const cogs = Number.isFinite(revenue) && Number.isFinite(grossProfit) ? revenue - grossProfit : null
      const ebit = firstNumber(item.ebit, item.operating_income)
      const netMarginPct = firstNumber(item.net_margin_pct, revenue ? (netIncome / revenue) * 100 : null)
      return {
        year: item.year,
        quarter: item.quarter,
        values: {
          revenue,
          cogs,
          grossProfit,
          grossMarginPct,
          ebit,
          netIncome,
          netMarginPct,
        },
      }
    })
}

function AnalysisStepper() {
  return (
    <div className="flex gap-2.5 items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0">
      <span className="text-teal-605">1. Map</span>
      <span>→</span>
      <span className="text-teal-605">2. Chart</span>
      <span>→</span>
      <span className="text-teal-605">3. Insight</span>
    </div>
  )
}

function buildIncomeKpiCards(dashboard, latest, summary) {
  const revenue = firstNumber(latest?.revenue, summary?.revenue)
  const netIncome = firstNumber(latest?.net_income, summary?.net_income)
  const grossMargin = firstNumber(latest?.gross_margin_pct, summary?.gross_margin_pct)
  const netMargin = firstNumber(latest?.net_margin_pct, summary?.net_margin_pct)
  
  return [
    {
      icon: '💵',
      label: 'Doanh thu',
      value: formatCompactNumber(revenue),
      delta: `${formatPercent(summary?.revenue_growth_yoy_pct)} YoY`,
      tone: trendTone(summary?.revenue_growth_yoy_pct),
      sparkValues: dashboard?.kpis?.[0]?.sparkValues || []
    },
    {
      icon: '📈',
      label: 'LNST',
      value: formatCompactNumber(netIncome),
      delta: `${formatPercent(summary?.net_income_growth_yoy_pct)} YoY`,
      tone: trendTone(summary?.net_income_growth_yoy_pct),
      sparkValues: dashboard?.kpis?.[1]?.sparkValues || []
    },
    {
      icon: '📊',
      label: 'Biên gộp',
      value: formatPercent(grossMargin),
      delta: 'Biên LN gộp',
      tone: scoreTone(grossMargin, 10, 20),
      sparkValues: []
    },
    {
      icon: '📉',
      label: 'Biên ròng',
      value: formatPercent(netMargin),
      delta: 'Biên LN ròng',
      tone: scoreTone(netMargin, 5, 12),
      sparkValues: dashboard?.kpis?.[2]?.sparkValues || []
    },
    {
      icon: '🎯',
      label: 'ROE',
      value: formatPercent(dashboard?.dupont?.roe),
      delta: 'Hiệu quả sử dụng vốn',
      tone: scoreTone(dashboard?.dupont?.roe, 10, 15),
      sparkValues: dashboard?.kpis?.[3]?.sparkValues || []
    },
    {
      icon: '⚡',
      label: 'Health Score',
      value: `${dashboard?.healthScore}/100`,
      delta: 'Điểm sức khỏe',
      tone: dashboard?.healthTone,
      sparkValues: []
    }
  ]
}

function buildBalanceKpiCards(dashboard, latest, analysis) {
  const summary = analysis?.summary || {}
  const totalAssets = firstNumber(summary.total_assets, latest?.total_assets, latest?.assets)
  const equity = firstNumber(summary.equity, latest?.equity)
  const cash = firstNumber(summary.cash, latest?.cash, latest?.cash_and_equivalents)
  const liabilities = firstNumber(summary.total_liabilities, latest?.total_liabilities, latest?.liabilities)
  
  return [
    {
      icon: '🏛️',
      label: 'Tổng tài sản',
      value: formatCompactNumber(totalAssets),
      delta: 'Quy mô doanh nghiệp'
    },
    {
      icon: '💎',
      label: 'Vốn chủ sở hữu',
      value: formatCompactNumber(equity),
      delta: 'Vốn tự có'
    },
    {
      icon: '💵',
      label: 'Tiền mặt',
      value: formatCompactNumber(cash),
      delta: `${formatPercent(totalAssets ? (cash / totalAssets) * 100 : null)} / Tổng tài sản`
    },
    {
      icon: '🛡️',
      label: 'Nợ phải trả',
      value: formatCompactNumber(liabilities),
      delta: `D/E: ${formatMaybeNumber(summary.debt_to_equity)}`
    },
    {
      icon: '⚖️',
      label: 'Current Ratio',
      value: formatMaybeNumber(summary.current_ratio),
      delta: `Quick Ratio: ${formatMaybeNumber(summary.quick_ratio)}`
    }
  ]
}

function firstNumber(...args) {
  for (const val of args) {
    if (val !== null && val !== undefined && val !== '') {
      const num = Number(val)
      if (Number.isFinite(num)) return num
    }
  }
  return null
}
