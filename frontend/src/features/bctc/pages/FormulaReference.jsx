import { useRef, useState } from 'react'
import { BookOpen, ArrowRight, X } from 'lucide-react'
import { FIELDS, METRICS } from '../utils/financialMetrics'

const REFERENCE_GROUPS = [
  { title: 'Công thức nền tảng', entries: [
    ['Phương trình kế toán', 'Tổng tài sản = Nợ phải trả + Vốn chủ sở hữu'],
    ['Giá trị bình quân', '(Giá trị đầu kỳ + Giá trị cuối kỳ) / 2'],
  ] },
  { title: 'Phân tích DuPont', entries: [
    ['ROA', 'Biên lợi nhuận ròng × Vòng quay tổng tài sản'],
    ['ROE', 'Biên lợi nhuận ròng × Vòng quay tổng tài sản × (Tổng tài sản bình quân / Vốn chủ sở hữu bình quân)'],
  ], note: 'Các tỷ số thành phần cần dùng cùng kỳ, cùng cơ sở lợi nhuận và số dư bình quân.' },
  { title: 'Đòn bẩy hoạt động và tài chính', entries: [
    ['DOL · Đòn bẩy hoạt động', '% thay đổi EBIT / % thay đổi sản lượng'],
    ['DFL · Đòn bẩy tài chính', '% thay đổi EPS / % thay đổi EBIT'],
    ['DTL · Đòn bẩy tổng hợp', 'DOL × DFL'],
  ], note: 'Các công thức độ nhạy này dùng dữ liệu so sánh tương ứng; chưa được tính tự động trong bộ tính.' },
]

function FormulaExpression({ formula }) {
  // Use a fraction only for an unambiguous single division; preserve every other expression verbatim.
  const parts = formula.split(' / ')
  const balanced = (part) => { let depth = 0; for (const char of part) { if (char === '(') depth += 1; if (char === ')') depth -= 1; if (depth < 0) return false } return depth === 0 }
  if (parts.length !== 2 || !parts.every(balanced)) return <span className="bcl-reference-expression">{formula}</span>
  const match = parts[1].match(/^(.*?)( × 100)$/)
  const denominator = match ? match[1] : parts[1]
  return <span className="bcl-reference-expression"><span className="bcl-reference-fraction"><span>{parts[0]}</span><span>{denominator}</span></span>{match && <span>{match[2]}</span>}</span>
}

export default function FormulaReference({ onSelectMetric }) {
  const dialogRef = useRef(null)
  const groups = [...new Set(METRICS.map((metric) => metric.group))]
  const [activeGroup, setActiveGroup] = useState(groups[0])
  const selectedReference = REFERENCE_GROUPS.find((group) => group.title === activeGroup)
  const metrics = METRICS.filter((metric) => metric.group === activeGroup)
  return <div className="bcl-reference">
    <button className="bcl-reference-trigger" type="button" onClick={() => dialogRef.current?.showModal()}><BookOpen size={17} aria-hidden="true" /><span><strong>Thư viện công thức</strong><small>Mở bảng công thức và các trường cần dùng</small></span><ArrowRight size={17} aria-hidden="true" /></button>
    <dialog ref={dialogRef} className="bcl-reference-dialog" aria-labelledby="bcl-reference-title" onClick={(event) => { if (event.target === dialogRef.current) dialogRef.current.close() }}>
      <div className="bcl-reference-dialog-head"><div><h2 id="bcl-reference-title">Thư viện công thức</h2><p>Chọn nhóm để tra cứu công thức và dữ liệu đầu vào.</p></div><button type="button" onClick={() => dialogRef.current?.close()} aria-label="Đóng thư viện công thức"><X size={20} /></button></div>
      <div className="bcl-reference-dialog-content"><nav className="bcl-reference-nav" aria-label="Nhóm công thức">{[...groups, ...REFERENCE_GROUPS.map((group) => group.title)].map((group) => <button key={group} type="button" className={activeGroup === group ? 'is-active' : ''} aria-pressed={activeGroup === group} onClick={() => setActiveGroup(group)}>{group}</button>)}</nav>
        <div className="bcl-reference-body"><h3>{activeGroup}</h3><div className="bcl-reference-entries">
        {metrics.map((metric) => <article key={metric.id}><h4>{metric.label}</h4><FormulaExpression formula={metric.formula} /><p>Đầu vào: {metric.deps.map((key) => FIELDS.find(([field]) => field === key)?.[1] || key).join(' · ')}</p>{metric.note && <small>{metric.note}</small>}<button type="button" onClick={() => { dialogRef.current?.close(); onSelectMetric(metric.id) }}>Mở trong bộ tính <ArrowRight size={14} aria-hidden="true" /></button></article>)}
        {selectedReference?.entries.map(([label, formula]) => <article key={label}><h4>{label}</h4><FormulaExpression formula={formula} /></article>)}
        {selectedReference?.note && <p>{selectedReference.note}</p>}</div></div>
      </div>
    </dialog>
  </div>
}
