import { useState } from 'react'
import { Calculator, Clipboard, FileSpreadsheet, FileText, PanelRight, Plus } from 'lucide-react'
import { comparablePeriods, compareReading } from '../utils/readingHistory'
import { periodKey } from '../utils/calculatorReport'

function number(value) { if (value === null || value === undefined || value === '') return null; const n = Number(value); return Number.isFinite(n) ? n : null }
function format(value, unit, kind) {
  const n = number(value)
  if (n === null) return '—'
  if (kind === '%') return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(n)}%`
  if (kind === 'x') return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(n)} lần`
  const divisor = unit === 'million' ? 1e6 : unit === 'raw' ? 1 : 1e9
  return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: unit === 'raw' ? 0 : 1 }).format(n / divisor)} ${unit === 'billion' ? 'tỷ VND' : unit === 'million' ? 'triệu VND' : 'VND'}`
}
function differenceText(value, unit, kind) {
  const sign = value > 0 ? '+' : ''
  return kind === '%' ? `${sign}${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(value)} điểm %` : sign + format(value, unit, kind)
}
export default function ReadingPanel({ workspace, selected, activeTab, mode, periodMode, loadNonce, unit, rightTab, setRightTab, notes, onNotesChange, onOpenCalculator, onSelectHistory }) {
  const [copyStatus, setCopyStatus] = useState('')
  const valid = Boolean(selected?.period && selected?.tableTab === activeTab && selected?.tableMode === mode && selected?.periodMode === periodMode && selected?.loadNonce === loadNonce)
  const value = valid ? number(selected.value) : null
  const history = (selected?.series || []).slice().sort((a, b) => periodKey(b.period).localeCompare(periodKey(a.period)))
  const periods = comparablePeriods(selected?.period)
  const comparison = (period) => history.find((item) => periodKey(item.period) === period)?.value
  const comparisons = [['Kỳ liền trước', periods.previous], ...(periods.yearAgo ? [['Cùng kỳ năm trước', periods.yearAgo]] : [])]
  const company = workspace?.company?.ticker || workspace?.company?.name || ''
  const snippet = `${company} · ${selected?.label} · ${selected?.period}: ${format(value, unit, selected?.unit)}${selected?.formula ? `\nCông thức: ${selected.formula}` : ''}`
  async function copyValue() {
    try { if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable'); await navigator.clipboard.writeText(snippet); setCopyStatus('Đã sao chép.') }
    catch { setCopyStatus('Không thể sao chép; hãy chọn và sao chép thủ công.') }
  }
  function addToNotes() { onNotesChange(`${notes.trimEnd()}${notes.trim() ? '\n\n' : ''}${snippet}\nNhận xét: `); setRightTab('notes') }
  return <aside className="bcl-tutor" aria-label="Công cụ đọc báo cáo">
    <div className="bcl-right-tabs" role="group" aria-label="Công cụ đọc báo cáo"><button className={rightTab === 'assistant' ? 'is-active' : ''} aria-pressed={rightTab === 'assistant'} onClick={() => setRightTab('assistant')} type="button"><PanelRight size={14} /> Phân tích</button><button className={rightTab === 'notes' ? 'is-active' : ''} aria-pressed={rightTab === 'notes'} onClick={() => setRightTab('notes')} type="button"><FileText size={14} /> Ghi chú</button></div>
    {rightTab === 'assistant' && <div className="bcl-tutor-body">{!valid ? <div className="bcl-reading-empty"><FileSpreadsheet size={21} /><h2>Chọn một ô trong bảng</h2><p>Xem lịch sử, so sánh các kỳ và lưu lại bằng chứng cho chỉ tiêu đó.</p></div> : <>
      <div className="bcl-reading-heading"><span>CHỈ TIÊU ĐANG CHỌN</span><h2>{selected.label}</h2><p>{company} · {selected.period} · {mode === 'actual' ? 'Báo cáo' : 'Kịch bản'}</p></div>
      <div className="bcl-reading-value"><span>Giá trị</span><strong>{format(value, unit, selected.unit)}</strong><small>{value === null ? 'Không có số liệu cho kỳ này.' : selected.kind === 'calculated' ? 'Chỉ số tính toán' : 'Theo bảng đang xem'}</small></div>
      <div className="bcl-reading-tools"><button type="button" disabled={value === null} onClick={copyValue}><Clipboard size={14} /> Sao chép</button><button type="button" onClick={addToNotes}><Plus size={14} /> Thêm vào ghi chú</button></div><span className="bcl-reading-feedback" role="status">{copyStatus}</span>
      {mode === 'actual' && <section className="bcl-reading-section"><h3>So sánh theo kỳ</h3>{comparisons.map(([label, period]) => { const ref = comparison(period); const result = compareReading(value, ref); return <div className="bcl-comparison" key={label}><span>{label}<small>{period || '—'}</small></span><span><strong>{result ? differenceText(result.difference, unit, selected.unit) : '—'}</strong><small>{result?.relative !== null && result?.relative !== undefined && selected.unit !== '%' ? `${result.relative > 0 ? '+' : ''}${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(result.relative)}% so với kỳ gốc` : result && selected.unit === '%' ? 'Chênh lệch điểm %' : 'Không đủ số liệu hoặc kỳ gốc không dương'}</small></span></div> })}</section>}
      <section className="bcl-reading-section"><h3>Cách tính & nguồn</h3><p>{selected.formula || 'Khoản mục trong bảng báo cáo; không có công thức tính tại đây.'}</p><p>Nguồn dữ liệu: {workspace?.data_provenance?.provider || 'chưa xác định'} · {selected.kind === 'calculated' ? 'Giá trị tính toán' : 'Theo dòng báo cáo'}. Chưa có liên kết tới trang tài liệu gốc.</p></section>
      {mode === 'actual' && <section className="bcl-reading-section"><h3>Lịch sử chỉ tiêu</h3><p>Chọn một kỳ để xem lại giá trị trong bảng.</p><div className="bcl-reading-history">{history.slice(0, 8).map((item) => <button key={item.period} type="button" aria-pressed={periodKey(item.period) === periodKey(selected.period)} onClick={() => onSelectHistory(item)}><span>{item.period}</span><strong>{format(item.value, unit, selected.unit)}</strong></button>)}</div></section>}
      <button type="button" className="bcl-reading-action" onClick={onOpenCalculator}><Calculator size={15} /> Mở bộ tính chỉ số</button>
    </>}</div>}
    {rightTab === 'notes' && <div className="bcl-side-content"><h2>Ghi chú báo cáo</h2><p>Ghi lại kỳ, chỉ tiêu và nguồn đối chiếu. Bấm Lưu ở đầu trang để đồng bộ workbook.</p><textarea aria-label="Ghi chú phiên học" value={notes} onChange={(event) => onNotesChange(event.target.value)} placeholder="Nhập ghi chú…" rows={12} /></div>}
  </aside>
}
