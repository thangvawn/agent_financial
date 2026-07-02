import { useState } from 'react'
import { submitStudentNote } from '../../../modules/financials'

export function formatCompactNumber(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return new Intl.NumberFormat('vi-VN', {
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(numeric)
}

export function formatMaybeNumber(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(numeric)
}

export function formatPercent(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(numeric)}%`
}

export function formatSignedPercent(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  const sign = numeric > 0 ? '▲ ' : numeric < 0 ? '▼ ' : ''
  return `${sign}${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(Math.abs(numeric))}%`
}

export function growthPercent(current, previous) {
  const cur = Number(current)
  const prev = Number(previous)
  if (!Number.isFinite(cur) || !Number.isFinite(prev) || prev === 0) return null
  return ((cur - prev) / Math.abs(prev)) * 100
}

export function formatRatioPercent(value) {
  if (value === null || value === undefined || value === '') return 'n/a'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 'n/a'
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(numeric * 100)}%`
}

function scoreLabel(tone) {
  if (tone === 'good') return 'Tốt'
  if (tone === 'warn') return 'Cảnh báo'
  return 'Trung bình'
}

export function detectNumberTone(cell) {
  if (cell == null) return null
  const s = String(cell).trim()
  if (!s || s === '—' || s === '-' || s === 'n/a') return null
  if (s.startsWith('-') || s.startsWith('−')) return 'neg'
  if (s.startsWith('+') || s.startsWith('▲')) return 'pos'
  return null
}

export function EvidenceBadge({ evidence, derived }) {
  if (evidence?.page) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 dark:bg-teal-950/20 text-teal-600 dark:text-teal-400 border border-teal-150 dark:border-teal-900/20">
        P{evidence.page}
        {Number.isFinite(Number(evidence.confidence)) && <small className="opacity-80"> ({Math.round(Number(evidence.confidence))}%)</small>}
      </span>
    )
  }
  if (derived) return <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400 border border-slate-200 dark:border-zinc-700">Tính toán</span>
  return <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-405 border border-red-100 dark:border-red-900/10">Chưa đọc</span>
}

export function AnalysisTable({ title, rows, columns, onRowClick }) {
  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      {title && <h2 className="text-sm font-bold text-slate-800 dark:text-white">{title}</h2>}
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs md:text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-zinc-800">
              {columns.map((column) => <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450" key={column}>{column}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => {
              const labelCell = row[0]
              return (
                <tr
                  key={idx}
                  onClick={() => onRowClick && onRowClick(labelCell)}
                  className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                >
                  {row.map((cell, index) => {
                    const tone = index === 0 ? null : detectNumberTone(cell)
                    return (
                      <td
                        key={index}
                        className={`p-3 ${index === 0 ? 'font-bold text-slate-900 dark:text-white' : 'font-semibold text-right'} ${
                          tone === 'pos' ? 'text-emerald-600 dark:text-emerald-450' :
                          tone === 'neg' ? 'text-red-600 dark:text-red-405' :
                          index > 0 ? 'text-slate-655 dark:text-zinc-300' : ''
                        }`}
                      >
                        {cell}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export function PeerTable({ rows }) {
  if (!rows.length) return <p className="text-xs text-slate-400 dark:text-zinc-500 italic py-4">Chưa có peer compare. Bấm “So sánh peers” để tải.</p>
  return (
    <div className="w-full overflow-x-auto border border-slate-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900">
      <table className="w-full text-left border-collapse text-xs md:text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-950/20">
            <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Doanh nghiệp</th>
            <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Doanh thu</th>
            <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Biên ròng</th>
            <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">ROE</th>
            <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Debt / Equity</th>
            <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Đánh giá</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((metric, idx) => (
            <tr
              key={idx}
              className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${
                metric.selected ? 'bg-teal-50 dark:bg-teal-950/20 font-bold text-teal-700 dark:text-teal-400' : ''
              } ${
                metric.tone === 'warn' ? 'text-red-650 dark:text-red-400' :
                metric.tone === 'caution' ? 'text-amber-650 dark:text-amber-400' :
                metric.tone === 'good' ? 'text-emerald-650 dark:text-emerald-400' : ''
              }`}
            >
              <td className="p-3 font-semibold">{metric.company}</td>
              <td className="p-3">{metric.revenueGrowth}</td>
              <td className="p-3">{metric.netMargin}</td>
              <td className="p-3">{metric.roe}</td>
              <td className="p-3">{metric.debtToEquity}</td>
              <td className="p-3 text-slate-500 dark:text-zinc-400 font-medium">{metric.assessment}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function BalanceStatementTable({ rows, onRowClick }) {
  const visibleRows = rows.slice(-5)
  const lines = [
    ['cash', 'Tiền & tương đương tiền'],
    ['receivables', 'Phải thu khách hàng'],
    ['inventory', 'Hàng tồn kho'],
    ['currentAssets', 'Tài sản ngắn hạn'],
    ['fixedAssets', 'Tài sản cố định'],
    ['otherAssets', 'Tài sản khác dài hạn'],
    ['totalAssets', 'Tổng tài sản'],
    ['shortTermDebt', 'Nợ ngắn hạn'],
    ['longTermDebt', 'Nợ dài hạn'],
    ['totalLiabilities', 'Tổng nợ phải trả'],
    ['equity', 'Vốn chủ sở hữu'],
  ]
  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      <h2 className="text-sm font-bold text-slate-800 dark:text-white">Bảng cân đối kế toán</h2>
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs md:text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-zinc-800">
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Chỉ tiêu</th>
              {visibleRows.map((row) => <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right" key={row.period}>{row.period}</th>)}
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right">YoY</th>
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right">QoQ</th>
            </tr>
          </thead>
          <tbody>
            {lines.map(([key, label]) => {
              const current = visibleRows.at(-1)?.[key]
              const previous = visibleRows.at(-2)?.[key]
              const first = visibleRows[0]?.[key]
              const isEmphasis = ['currentAssets', 'totalAssets', 'totalLiabilities'].includes(key)
              return (
                <tr
                  key={key}
                  className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${
                    isEmphasis ? 'bg-slate-50 dark:bg-zinc-950 font-bold' : ''
                  } ${onRowClick ? 'cursor-pointer' : ''}`}
                  onClick={() => onRowClick && onRowClick(label)}
                >
                  <td className="p-3 text-slate-900 dark:text-white">{label}</td>
                  {visibleRows.map((row) => <td className="p-3 text-right text-slate-700 dark:text-zinc-300 font-semibold" key={`${key}-${row.period}`}>{formatCompactNumber(row[key])}</td>)}
                  <td className="p-3 text-right font-semibold text-teal-600 dark:text-teal-400">{formatSignedPercent(growthPercent(current, first))}</td>
                  <td className="p-3 text-right font-semibold text-teal-605 dark:text-teal-405">{formatSignedPercent(growthPercent(current, previous))}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export function CashFlowStatementTable({ rows }) {
  const visibleRows = rows.slice(-7)
  const lines = [
    ['netIncome', 'LNST'],
    ['depreciation', 'Khấu hao & phân bổ'],
    ['workingCapitalChange', 'Thay đổi vốn lưu động'],
    ['cfo', 'Lưu chuyển tiền từ HĐKD (CFO)'],
    ['capex', 'Chi đầu tư TSCĐ'],
    ['assetPurchase', 'Mua/bán đầu tư & góp vốn'],
    ['cfi', 'Lưu chuyển tiền từ HĐĐT (CFI)'],
    ['dividends', 'Cổ tức đã trả'],
    ['netBorrowing', 'Vay ròng'],
    ['cff', 'Lưu chuyển tiền từ HĐTC (CFF)'],
    ['fxOther', 'FX & các khoản khác'],
    ['openingCash', 'Tiền đầu kỳ'],
    ['cash', 'Tiền cuối kỳ'],
  ]
  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      <h2 className="text-sm font-bold text-slate-800 dark:text-white">Báo cáo lưu chuyển tiền tệ</h2>
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs md:text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-zinc-800">
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Chỉ tiêu</th>
              {visibleRows.map((row) => <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right" key={row.period}>{row.period}</th>)}
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right">YoY</th>
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right">QoQ</th>
            </tr>
          </thead>
          <tbody>
            {lines.map(([key, label]) => {
              const current = visibleRows.at(-1)?.[key]
              const previous = visibleRows.at(-2)?.[key]
              const first = visibleRows[0]?.[key]
              const isFlowHeader = ['cfo', 'cfi', 'cff', 'cash'].includes(key)
              return (
                <tr
                  key={key}
                  className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${
                    isFlowHeader ? 'bg-teal-50/50 dark:bg-teal-950/20 font-bold text-teal-800 dark:text-teal-400' : ''
                  }`}
                >
                  <td className="p-3 text-slate-900 dark:text-white">{label}</td>
                  {visibleRows.map((row) => <td className="p-3 text-right text-slate-700 dark:text-zinc-300 font-semibold" key={`${key}-${row.period}`}>{formatCompactNumber(row[key])}</td>)}
                  <td className="p-3 text-right font-semibold text-teal-600 dark:text-teal-400">{formatSignedPercent(growthPercent(current, first))}</td>
                  <td className="p-3 text-right font-semibold text-teal-605 dark:text-teal-405">{formatSignedPercent(growthPercent(current, previous))}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export function RatioStatementTable({ rows }) {
  const visibleRows = rows.slice(-7)
  const lines = [
    ['currentRatio', 'Current Ratio (lần)', 'ratio'],
    ['quickRatio', 'Quick Ratio (lần)', 'ratio'],
    ['cashRatio', 'Cash Ratio (lần)', 'ratio'],
    ['debtToEquity', 'Debt/Equity (lần)', 'ratio'],
    ['debtToAsset', 'Debt/Asset (lần)', 'ratio'],
    ['interestCoverage', 'Interest Coverage (lần)', 'ratio'],
    ['roa', 'ROA (%)', 'percent'],
    ['roe', 'ROE (%)', 'percent'],
    ['netMargin', 'Biên lợi nhuận ròng (%)', 'percent'],
  ]

  function ratioTone(key, value) {
    const num = Number(value)
    if (!Number.isFinite(num)) return null
    if (key === 'currentRatio') return num < 1.0 ? 'warn' : num >= 1.5 ? 'good' : 'caution'
    if (key === 'quickRatio') return num < 0.8 ? 'warn' : num >= 1.2 ? 'good' : 'caution'
    if (key === 'debtToEquity') return num > 1.5 ? 'warn' : num <= 0.6 ? 'good' : 'caution'
    if (key === 'roe') return num < 8 ? 'warn' : num >= 15 ? 'good' : 'caution'
    if (key === 'netMargin') return num < 5 ? 'warn' : num >= 15 ? 'good' : 'caution'
    return null
  }

  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      <h2 className="text-sm font-bold text-slate-805 dark:text-white">Bảng chỉ số tài chính</h2>
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs md:text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-zinc-800">
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Chỉ tiêu</th>
              {visibleRows.map((row) => <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right" key={row.period}>{row.period}</th>)}
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right">YoY</th>
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right">Đánh giá</th>
            </tr>
          </thead>
          <tbody>
            {lines.map(([key, label, type]) => {
              const current = visibleRows.at(-1)?.[key]
              const first = visibleRows[0]?.[key]
              const tone = ratioTone(key, current)
              return (
                <tr
                  key={key}
                  className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${
                    tone === 'warn' ? 'text-red-650 dark:text-red-405 font-medium' :
                    tone === 'good' ? 'text-emerald-650 dark:text-emerald-450 font-medium' : ''
                  }`}
                >
                  <td className="p-3 text-slate-900 dark:text-white">{label}</td>
                  {visibleRows.map((row) => (
                    <td className="p-3 text-right font-semibold text-slate-700 dark:text-zinc-350" key={`${key}-${row.period}`}>{type === 'percent' ? formatPercent(row[key]) : formatMaybeNumber(row[key])}</td>
                  ))}
                  <td className="p-3 text-right font-semibold text-teal-650 dark:text-teal-400">{formatSignedPercent(growthPercent(current, first))}</td>
                  <td className="p-3 text-right">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                      tone === 'good' ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/20 text-emerald-600 dark:text-emerald-400' :
                      tone === 'warn' ? 'bg-red-50 dark:bg-red-950/20 border-red-100 dark:border-red-900/20 text-red-600 dark:text-red-400' :
                      'bg-slate-50 dark:bg-zinc-800 border-slate-200 dark:border-zinc-700 text-slate-500 dark:text-zinc-400'
                    }`}>{scoreLabel(tone)}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export function SimplizeDataViewToggle({ viewMode, onChange }) {
  return (
    <div className="flex p-0.5 bg-slate-100 dark:bg-zinc-850 rounded-lg border border-slate-200 dark:border-zinc-800 shrink-0 self-start">
      {[['all', 'Bản đầy đủ'], ['simplize', 'Bản tinh giản']].map(([id, label]) => (
        <button
          key={id}
          type="button"
          className={`px-3 py-1.5 rounded-md text-xs font-semibold cursor-pointer transition-all duration-200 ${
            viewMode === id
              ? 'bg-white dark:bg-zinc-800 text-slate-900 dark:text-white shadow-sm'
              : 'text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
          }`}
          onClick={() => onChange(id)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

export function SimplizeDataTable({ title, data, lines, viewMode, onRowClick }) {
  if (!data?.periods?.length) return <p className="text-xs text-slate-450 italic py-4">Chưa có dữ liệu BCTC.</p>
  const visiblePeriods = [...data.periods].sort((a, b) => Number(a.year) - Number(b.year) || Number(a.quarter) - Number(b.quarter)).slice(-5)

  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      {title && <h2 className="text-sm font-bold text-slate-800 dark:text-white">{title}</h2>}
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs md:text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-zinc-800">
              <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450">Chỉ tiêu</th>
              {visiblePeriods.map((period) => <th className="p-3 font-semibold text-slate-500 dark:text-zinc-450 text-right" key={`${period.year}-${period.quarter}`}>{period.quarter ? `Q${period.quarter}/${period.year}` : period.year}</th>)}
            </tr>
          </thead>
          <tbody>
            {lines.map((line) => {
              const label = typeof line === 'string' ? line : line.label
              const key = typeof line === 'string' ? line : line.key
              return (
                <tr
                  key={key}
                  className={`border-b border-slate-100 dark:border-zinc-850 hover:bg-slate-50 dark:hover:bg-zinc-850/20 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                  onClick={() => onRowClick && onRowClick(label)}
                >
                  <td className="p-3 text-slate-900 dark:text-white">{label}</td>
                  {visiblePeriods.map((period) => {
                    const cellValue = period.values?.[key] ?? null
                    const displayValue = typeof line !== 'string' && line.format ? line.format(cellValue) : formatCompactNumber(cellValue)
                    return <td className="p-3 text-right text-slate-700 dark:text-zinc-300 font-semibold" key={`${period.year}-${period.quarter}`}>{displayValue}</td>
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

export function StudentNotePanel({ companyId, period, sectionName }) {
  const [note, setNote] = useState('')
  const [status, setStatus] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!note.trim()) return
    setStatus('Đang nộp...')
    try {
      await submitStudentNote({
        student_id: 'student-123',
        company_id: companyId,
        period: period || 'current',
        note_content: note,
        related_metrics: [sectionName]
      })
      setStatus('Nộp thành công!')
      setNote('')
      setTimeout(() => setStatus(''), 3000)
    } catch (err) {
      setStatus(`Lỗi: ${err.message}`)
    }
  }

  return (
    <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4 mt-6">
      <div>
        <h2 className="text-sm font-bold text-slate-900 dark:text-white">Nhật ký phân tích (Student Notes)</h2>
        <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">Ghi lại nhận định của bạn về {sectionName} để gửi cho Giảng viên.</p>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder={`Nhập nhận định của bạn về ${sectionName}...`}
          rows={4}
          className="w-full p-3 rounded-xl border border-slate-200 dark:border-zinc-850 bg-slate-50 dark:bg-zinc-950 text-xs md:text-sm text-slate-805 dark:text-zinc-200 outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
        />
        <div className="flex gap-3 items-center">
          <button type="submit" className="px-4.5 py-2 rounded-full text-xs font-semibold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer active:scale-95 transition-all" disabled={!note.trim() || status === 'Đang nộp...'}>Nộp nhận định</button>
          {status && <span className="text-xs text-slate-550 dark:text-zinc-400">{status}</span>}
        </div>
      </form>
    </article>
  )
}

export function IncomeAssistantCard({ dashboard }) {
  return (
    <div className="flex flex-col gap-4">
      <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
        <header className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-zinc-850">
          <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Trợ lý học tập <span className="text-teal-550 font-extrabold">AI</span></h2>
        </header>
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-900 dark:text-white">Giải thích nhanh</h3>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>Biên lợi nhận gộp:</strong> phản ánh hiệu quả kiểm soát giá vốn.</p>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>Biên lợi nhuận ròng:</strong> đo lường khả năng tạo lợi nhuận sau mọi chi phí.</p>
        </div>
        <div className="flex flex-col gap-1.5 text-[10px] text-teal-600 dark:text-teal-400 font-semibold">
          <span>Biên gộp = Lợi nhuận gộp / Doanh thu thuần</span>
          <span>Biên ròng = LNST / Doanh thu thuần</span>
        </div>
      </article>
      <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
        <h3 className="text-xs font-bold text-slate-900 dark:text-white">Gợi ý phân tích</h3>
        <div className="flex flex-col gap-2">
          {dashboard.summaryBullets.slice(0, 3).map((item, idx) => (
            <p key={idx} className="text-xs text-slate-655 dark:text-zinc-350 flex items-start gap-2">✓ {item.text}</p>
          ))}
        </div>
      </article>
    </div>
  )
}

export function BalanceAssistantCard({ dashboard }) {
  return (
    <div className="flex flex-col gap-4">
      <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
        <header className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-zinc-850">
          <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Trợ lý học tập <span className="text-teal-555 font-extrabold">AI</span></h2>
        </header>
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-900 dark:text-white">Giải thích nhanh</h3>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>Current Ratio:</strong> Khả năng thanh toán nợ ngắn hạn bằng tài sản ngắn hạn.</p>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>Debt/Equity:</strong> Đo lường mức độ đòn bẩy tài chính.</p>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>Working Capital:</strong> Tài sản ngắn hạn trừ nợ ngắn hạn. Dương là tốt.</p>
        </div>
        <div className="flex flex-col gap-1.5 text-[10px] text-teal-600 dark:text-teal-400 font-semibold">
          <span>Current Ratio = TSNH / NNH</span>
          <span>Debt/Equity = Nợ phải trả / Vốn CSH</span>
          <span>Working Capital = TSNH - NNH</span>
        </div>
      </article>
      <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
        <h3 className="text-xs font-bold text-slate-900 dark:text-white">Gợi ý phân tích</h3>
        <div className="flex flex-col gap-2">
          {dashboard.leverageMetrics.slice(0, 3).map((item, idx) => (
            <p key={idx} className="text-xs text-slate-655 dark:text-zinc-350 flex items-start gap-2">✓ {item.label}: {item.value} - {item.note}</p>
          ))}
        </div>
      </article>
    </div>
  )
}

export function CashFlowAssistantCard() {
  return (
    <div className="flex flex-col gap-4">
      <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
        <header className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-zinc-850">
          <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Trợ lý học tập <span className="text-teal-555 font-extrabold">AI</span></h2>
        </header>
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-900 dark:text-white">Giải thích nhanh</h3>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>CFO:</strong> tiền thuần từ hoạt động kinh doanh.</p>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>FCF:</strong> dòng tiền tự do sau khi trừ chi đầu tư tài sản cố định.</p>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed"><strong>OCF/LNST:</strong> chỉ số phản ánh chất lượng lợi nhuận.</p>
        </div>
        <div className="flex flex-col gap-1.5 text-[10px] text-teal-600 dark:text-teal-400 font-semibold">
          <span>OCF/LNST = CFO / LNST</span>
          <span>FCF = CFO - Capex</span>
          <span>Capex ratio = Capex / Doanh thu</span>
        </div>
      </article>
    </div>
  )
}

export function RatioAssistantCard() {
  return (
    <div className="flex flex-col gap-4">
      <article className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
        <header className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-zinc-850">
          <h2 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Trợ lý học tập <span className="text-teal-555 font-extrabold">AI</span></h2>
        </header>
        <div className="flex flex-col gap-3">
          <h3 className="text-xs font-bold text-slate-900 dark:text-white">Giải thích nhanh</h3>
          <p className="text-xs text-slate-600 dark:text-zinc-405 leading-relaxed">Nhóm chỉ số giúp đọc sức khỏe tài chính theo 4 khía cạnh: thanh khoản, đòn bẩy, hiệu quả và sinh lời.</p>
        </div>
        <div className="flex flex-col gap-1.5 text-[10px] text-teal-600 dark:text-teal-400 font-semibold">
          <span>ROE = LNST / Vốn CSH bình quân</span>
          <span>Current Ratio = TSNH / Nợ ngắn hạn</span>
          <span>Quick Ratio = (TSNH - Hàng tồn kho) / Nợ ngắn hạn</span>
        </div>
      </article>
    </div>
  )
}
