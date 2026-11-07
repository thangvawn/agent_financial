import { useMemo, useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { periodKey, readCalculatorReport } from '../utils/calculatorReport'
import { FIELDS, METRICS, calculateMetric } from '../utils/financialMetrics'
import FormulaReference from './FormulaReference'

function fmt(value, unit, moneyLabel) {
  return value === null ? '—' : `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(value)} ${unit === 'money' ? moneyLabel : unit}`
}
function MetricChart({ metric, points, moneyLabel }) {
  const finite = points.filter((item) => item.value !== null)
  const magnitude = Math.max(1e-12, ...finite.map((item) => Math.abs(item.value)))
  return <section className="bcl-metric-chart" aria-label={`Biểu đồ ${metric.label}`}>
    <div><h3>{metric.label} theo kỳ</h3><p>Kỳ đang chọn dùng số bạn đã nhập; các kỳ khác dùng báo cáo. Kỳ thiếu đầu vào không có cột.</p></div>
    {finite.length ? <div className="bcl-metric-chart-scroll"><div className="bcl-metric-plot" style={{ minWidth: `${Math.max(360, points.length * 70)}px` }}>
      {points.map(({ period, value }) => <div className="bcl-metric-column" key={period} title={`${period}: ${fmt(value, metric.unit, moneyLabel)}`}><div className="bcl-metric-positive">{value !== null && value >= 0 && <i style={{ height: `${value / magnitude * 100}%` }} />}</div><div className="bcl-metric-negative">{value !== null && value < 0 && <i style={{ height: `${-value / magnitude * 100}%` }} />}</div><strong>{fmt(value, metric.unit, moneyLabel)}</strong><span>{period}</span></div>)}
    </div></div> : <p role="status">Chưa đủ dữ liệu để vẽ. Hãy nhập các đầu vào của chỉ số.</p>}
    <details><summary>Xem dữ liệu biểu đồ</summary><table><thead><tr><th>Kỳ</th><th>Giá trị</th></tr></thead><tbody>{points.map(({ period, value }) => <tr key={period}><th>{period}</th><td>{fmt(value, metric.unit, moneyLabel)}</td></tr>)}</tbody></table></details>
  </section>
}
export default function FinancialCalculator({ workspace, unit }) {
  const periods = useMemo(() => [...new Set(Object.values(workspace?.statements || {}).flatMap((item) => item?.periods || []))].sort((a, b) => periodKey(b).localeCompare(periodKey(a))), [workspace])
  const [period, setPeriod] = useState(() => periods[0] || '')
  const divisor = unit === 'million' ? 1e6 : unit === 'raw' ? 1 : 1e9
  const [report, setReport] = useState(() => readCalculatorReport(workspace, periods[0] || '', divisor))
  const { values, sources } = report
  const [source, setSource] = useState('report')
  const [group, setGroup] = useState('Tất cả')
  const [metricId, setMetricId] = useState('gross_margin')
  const [query, setQuery] = useState('')
  const selectedRef = useRef(null)
  const moneyLabel = unit === 'million' ? 'triệu VND' : unit === 'raw' ? 'VND' : 'tỷ VND'
  const groups = [...new Set(METRICS.map((metric) => metric.group))]
  const visible = METRICS.filter((metric) => (group === 'Tất cả' || metric.group === group) && `${metric.label} ${metric.formula}`.toLocaleLowerCase('vi').includes(query.trim().toLocaleLowerCase('vi')))
  const metric = METRICS.find((item) => item.id === metricId) || METRICS[0]
  const points = [...periods].reverse().map((item) => ({ period: item, value: calculateMetric(metric, item === period ? values : readCalculatorReport(workspace, item, divisor).values) }))
  if (!periods.length) points.push({ period: 'Nhập tay', value: calculateMetric(metric, values) })
  const fields = FIELDS.filter(([key]) => metric.deps.includes(key))
  function changeGroup(value) { setGroup(value); setQuery('') }
  return <section className="bcl-calculator" aria-labelledby="bcl-calculator-title">
    <div className="bcl-calc-heading"><div><h2 id="bcl-calculator-title">Bộ tính chỉ số tài chính</h2><p>Chọn một chỉ số bên dưới để xem công thức và nhập số. Các khoản mục có sẵn được tự điền theo kỳ; bạn có thể sửa để tính thử.</p></div><label>Kỳ báo cáo <span className="bcl-select-wrap"><select value={period} onChange={(event) => { setPeriod(event.target.value); setReport(readCalculatorReport(workspace, event.target.value, divisor)); setSource('report') }}><option value="">Chọn kỳ</option>{periods.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={16} aria-hidden="true" /></span></label><button type="button" disabled={!period} onClick={() => { setReport(readCalculatorReport(workspace, period, divisor)); setSource('report') }}>Tự điền từ báo cáo</button><button type="button" onClick={() => { setReport({ values: {}, sources: {} }); setSource('manual') }}>Xóa đầu vào</button></div>
    <p className="bcl-calc-hint">Đơn vị khoản mục: {moneyLabel}; số trên mỗi cổ phiếu tính bằng VND. {source === 'report' ? 'Đã lấy các khoản mục có sẵn; có thể chỉnh sửa.' : 'Nhập thủ công.'} Đổi kỳ hoặc đơn vị sẽ thay số nhập bằng dữ liệu báo cáo. Thiếu số hoặc mẫu số bằng 0 sẽ không tính.</p>
    <FormulaReference onSelectMetric={(id) => { setMetricId(id); setGroup('Tất cả'); setQuery(''); selectedRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }} />
    <div className="bcl-metric-controls"><label>Nhóm chỉ số<span className="bcl-select-wrap"><select value={group} onChange={(event) => changeGroup(event.target.value)}><option>Tất cả</option>{groups.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={16} aria-hidden="true" /></span></label><label>Tìm chỉ số<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tên hoặc công thức" /></label></div>
    <div className="bcl-metric-list" aria-label="Danh mục chỉ số">{visible.length ? groups.map((groupName) => {
      const items = visible.filter((item) => item.group === groupName)
      return items.length ? <section className="bcl-metric-group" key={groupName}><h3>{groupName}</h3><div>{items.map((item) => <button type="button" key={item.id} className={item.id === metricId ? 'is-active' : ''} aria-pressed={item.id === metricId} onClick={() => setMetricId(item.id)}><span>{item.label}</span><strong>{fmt(calculateMetric(item, values), item.unit, moneyLabel)}</strong></button>)}</div></section> : null
    }) : <p>Không tìm thấy chỉ số phù hợp.</p>}</div>
    <div ref={selectedRef} className="bcl-calc-selected" aria-live="polite"><div><span>{metric.group} · Công thức chỉ số đang chọn</span><h3>{metric.label}</h3><code>{metric.formula}</code>{metric.note && <p>{metric.note}</p>}</div><strong>{fmt(calculateMetric(metric, values), metric.unit, moneyLabel)}</strong></div>
    <p className="bcl-calc-hint">Nhập hoặc sửa các khoản mục dưới đây để cập nhật kết quả và biểu đồ ngay.</p>
    <div className="bcl-calc-fields">{fields.map(([key, label]) => <label key={key}><span>{label}</span><input type="number" step="any" value={values[key] ?? ''} onChange={(event) => { const value = event.target.value; setReport((current) => ({ values: { ...current.values, [key]: value }, sources: { ...current.sources, [key]: value === '' ? '' : 'Nhập thủ công' } })) }} placeholder="Chưa có số" /><small>{sources[key] || (['manual', 'market'].includes(FIELDS.find((field) => field[0] === key)?.[2]) ? 'Cần nhập thủ công nếu nguồn không cung cấp' : `Không có trong báo cáo cho kỳ tương ứng`)}</small></label>)}</div>
    <MetricChart metric={metric} points={points} moneyLabel={moneyLabel} />
    <p className="bcl-calc-hint">Các công thức tổng quát phù hợp chủ yếu với doanh nghiệp phi tài chính; ngân hàng, bảo hiểm và chứng khoán cần chỉ số chuyên ngành. <a href="https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/financial-analysis-techniques" target="_blank" rel="noreferrer">Tham khảo CFA Institute</a>.</p>
  </section>
}
