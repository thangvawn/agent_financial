import { useMemo, useState } from 'react'
import {
  AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, BookOpen, Calculator,
  Check, CheckCircle2, ChevronRight, ClipboardCheck, Download, FileSpreadsheet,
  GitCompare, History, Info, Lightbulb, LoaderCircle, LockKeyhole, Play, RotateCcw, Save,
  ShieldCheck, SlidersHorizontal, Sparkles, Target, XCircle,
} from 'lucide-react'

import { runBctcPracticeLab, submitStudentNote } from '../services/financialsApi'
import RawDataChallenge from './RawDataChallenge'
import './ratio-practice.css'

const STATUS_META = {
  good: { label: 'Tốt', icon: CheckCircle2, className: 'is-good' },
  watch: { label: 'Theo dõi', icon: AlertTriangle, className: 'is-watch' },
  risk: { label: 'Rủi ro', icon: XCircle, className: 'is-risk' },
  unavailable: { label: 'Thiếu dữ liệu', icon: Info, className: 'is-muted' },
}
const EMPTY_REFLECTION = { observation: '', evidence: '', limitation: '' }
const cx = (...values) => values.filter(Boolean).join(' ')

function currentStudentId() {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem('public-beta.session_id')
    || window.localStorage.getItem('session_id')
    || window.localStorage.getItem('auth.session_id')
    || ''
}

function formatValue(value, unit = '') {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—'
  const number = Number(value)
  if (unit === 'VND') {
    const absolute = Math.abs(number)
    const divisor = absolute >= 1e12 ? 1e12 : absolute >= 1e9 ? 1e9 : absolute >= 1e6 ? 1e6 : 1
    const suffix = divisor === 1e12 ? ' nghìn tỷ' : divisor === 1e9 ? ' tỷ' : divisor === 1e6 ? ' triệu' : ''
    return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: divisor === 1 ? 0 : 2 }).format(number / divisor) + suffix
  }
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: unit === '%' ? 1 : 2 }).format(number) + (unit === '%' ? '%' : unit ? ' ' + unit : '')
}

function hasCalculableFields(company) {
  return (company?.calculated_fields || []).some((item) => item.status === 'calculated' && Number.isFinite(Number(item.value)))
}

function formatDate(value) {
  if (!value) return '—'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? '—' : new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(parsed)
}

function parseTickers(value) {
  const tokens = String(value || '').split(/[;,\s]+/).map((item) => item.trim().toUpperCase()).filter(Boolean)
  const unique = [...new Set(tokens)]
  const invalid = unique.filter((item) => !/^[A-Z0-9][A-Z0-9._-]{0,19}$/.test(item))
  return { tickers: unique.filter((item) => !invalid.includes(item)), invalid, tooMany: unique.length > 8 }
}

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.unavailable
  const Icon = meta.icon
  return <span className={cx('rp-status', meta.className)}><Icon size={13} />{meta.label}</span>
}

function Workflow({ phase }) {
  const steps = [
    ['01', 'Đặt câu hỏi', 'Mục tiêu & giả thuyết', 'brief'],
    ['02', 'Khám phá', 'Raw data & công thức', 'explore'],
    ['03', 'So sánh', 'Bằng chứng giữa peers', 'compare'],
    ['04', 'Giải thích', 'Reflection & checkpoint', 'reflect'],
  ]
  const activeIndex = Math.max(0, steps.findIndex((item) => item[3] === phase))
  return <ol className="rp-workflow" aria-label="Quy trình học tập BCTC">
    {steps.map(([number, title, description, key], index) => <li key={key} className={index <= activeIndex ? 'is-complete' : ''}>
      <span className="rp-workflow-number">{index < activeIndex ? <Check size={13} /> : number}</span>
      <span><strong>{title}</strong><small>{description}</small></span>
      {index < steps.length - 1 && <ChevronRight aria-hidden="true" />}
    </li>)}
  </ol>
}

function LoadingPanel() {
  return <div className="rp-loading" role="status" aria-live="polite"><LoaderCircle className="is-spinning" size={22} /><div><strong>Đang chạy phòng thực hành</strong><span>Đọc raw data, tính trường dẫn xuất và chuẩn hóa kết quả so sánh…</span></div></div>
}

function LabBrief({ learning, hypothesis, onHypothesisChange, completed }) {
  const prompts = learning?.reflection_prompts || []
  return <aside className="rp-brief">
    <div className="rp-brief-kicker"><Target size={14} /> LAB BCTC · BÀI 01</div>
    <h2>Đọc sức khỏe tài chính bằng bằng chứng</h2>
    <p className="rp-brief-intro">Một bài thực hành ngắn: đi từ khoản mục gốc đến chỉ tiêu, rồi tự giải thích điều bạn quan sát được.</p>
    <div className="rp-brief-objective"><span>MỤC TIÊU HỌC TẬP</span><strong>{learning?.objective || 'Đọc raw data, kiểm tra công thức và so sánh chất lượng tài chính trên cùng một kỳ.'}</strong><div className="rp-brief-meta"><span>Khoảng 15 phút</span><span>Không khuyến nghị đầu tư</span></div></div>
    <label className="rp-hypothesis"><span><Lightbulb size={14} /> Giả thuyết trước khi chạy</span><textarea value={hypothesis} onChange={(event) => onHypothesisChange(event.target.value)} placeholder="Ví dụ: Tôi dự đoán doanh nghiệp A có dòng tiền tốt hơn vì…" rows={4} /><small>Viết một câu ngắn. Bạn sẽ quay lại kiểm tra giả thuyết sau khi xem kết quả.</small></label>
    <div className="rp-brief-question"><span><ClipboardCheck size={14} /> Câu hỏi dẫn đường</span><p>{learning?.prompt || 'Doanh nghiệp nào có tín hiệu cân bằng hơn trong nhóm? Hãy dùng ít nhất hai chỉ tiêu và mở raw input trước khi kết luận.'}</p></div>
    <div className={cx('rp-brief-status', completed && 'is-complete')}>{completed ? <CheckCircle2 size={16} /> : <ArrowRight size={16} />}<span>{completed ? 'Bạn đã hoàn thành phần reflection.' : 'Sau khi chạy, hãy viết observation, evidence và limitation.'}</span></div>
    <div className="rp-brief-prompts" aria-label="Các câu hỏi reflection">{prompts.map((prompt) => <span key={prompt}>{prompt}</span>)}</div>
  </aside>
}

function RunHistory({ runs, activeRunId, onSelect }) {
  if (!runs.length) return <div className="rp-history rp-history-empty"><History size={15} /><span>Lịch sử lần chạy sẽ xuất hiện ở đây sau khi bạn chạy mô phỏng.</span></div>
  return <section className="rp-history" aria-labelledby="rp-history-title">
    <div className="rp-history-heading"><span id="rp-history-title"><History size={14} /> Lịch sử lần chạy</span><small>{runs.length}/5</small></div>
    <div className="rp-history-list">{runs.map((run, index) => <button type="button" key={run.id} className={run.id === activeRunId ? 'is-active' : ''} onClick={() => onSelect(run)}><span className="rp-history-index">{String(runs.length - index).padStart(2, '0')}</span><span><strong>{run.label}</strong><small>{run.tickers.join(' · ')} · {formatDate(run.createdAt)}</small></span><ChevronRight size={14} /></button>)}</div>
  </section>
}

function DataQualityStrip({ result }) {
  const companies = result?.companies || []
  const averageCoverage = companies.length ? Math.round(companies.reduce((sum, company) => sum + (company.overall?.coverage_pct || 0), 0) / companies.length) : 0
  const period = result?.controls?.period || companies[0]?.period || 'Kỳ mới nhất'
  return <section className="rp-quality-strip" aria-label="Tóm tắt chất lượng dữ liệu">
    <div><span>KỲ ĐANG SO SÁNH</span><strong>{period}</strong><small>{result?.controls?.period_mode === 'year' ? 'Theo năm' : 'Theo quý'}</small></div>
    <div><span>ĐỘ PHỦ TRUNG BÌNH</span><strong>{averageCoverage}%</strong><small>Khoản mục có dữ liệu</small></div>
    <div><span>DOANH NGHIỆP</span><strong>{companies.length}</strong><small>Trong phiên này</small></div>
    <div className="rp-quality-note"><ShieldCheck size={16} /><span>Số liệu thiếu được giữ là “—”, không tự bù.</span></div>
  </section>
}

function RankingCard({ company, selected, onSelect }) {
  const status = company.overall?.status || 'unavailable'
  return <button type="button" className={cx('rp-ranking-card', selected && 'is-selected')} onClick={onSelect} aria-pressed={selected}><span className="rp-rank">#{company.overall?.rank || '—'}</span><span className="rp-ranking-main"><strong>{company.ticker}</strong><small>{company.company_name}</small></span><span className="rp-ranking-score"><b>{company.overall?.score ?? '—'}</b><small>/100</small></span><StatusBadge status={status} /></button>
}

function RawInputs({ company }) {
  return <section className="rp-card rp-raw-card"><div className="rp-section-heading"><div><span className="rp-eyebrow">BƯỚC 01 · RAW DATA</span><h3><FileSpreadsheet size={17} /> Khoản mục đầu vào</h3><p>Kỳ {company.period || '—'} · nguồn {company.data_quality?.source || '—'}</p></div><span className="rp-coverage">{company.data_quality?.raw_fields_available || 0}/{company.data_quality?.raw_fields_total || 0} trường có dữ liệu</span></div><div className="rp-field-grid">{(company.raw_inputs || []).map((item) => <div className={cx('rp-field', item.value === null && 'is-missing')} key={item.field}><span>{item.label}</span><b>{formatValue(item.value, item.unit)}</b>{item.value === null && <small>Thiếu trong raw data</small>}</div>)}</div></section>
}

function CalculatedFields({ company }) {
  return <section className="rp-card"><div className="rp-section-heading"><div><span className="rp-eyebrow">BƯỚC 02 · CALCULATE</span><h3><Calculator size={17} /> Trường dẫn xuất từ công thức</h3><p>Mỗi chỉ tiêu hiển thị công thức và trạng thái dữ liệu để có thể kiểm tra lại.</p></div><span className="rp-coverage">{company.data_quality?.calculated_fields_available || 0}/{company.data_quality?.calculated_fields_total || 0} chỉ tiêu tính được</span></div><div className="rp-calculated-table-wrap"><table className="rp-calculated-table"><caption className="rp-sr-only">Các trường dẫn xuất và công thức tính từ raw data</caption><thead><tr><th scope="col">Chỉ tiêu</th><th scope="col">Công thức</th><th scope="col">Phụ thuộc</th><th scope="col">Giá trị</th><th scope="col">Trạng thái</th></tr></thead><tbody>{(company.calculated_fields || []).map((item) => <tr key={item.field}><td><strong>{item.label}</strong><small>{item.field}</small></td><td><code>{item.formula}</code></td><td><span className="rp-dependencies">{item.dependencies?.join(' · ') || '—'}</span></td><td className="rp-number">{formatValue(item.value, item.unit)}</td><td><span className={cx('rp-calc-status', item.status === 'calculated' ? 'is-ready' : 'is-missing')}>{item.status === 'calculated' ? 'Đã tính' : 'Thiếu đầu vào'}</span></td></tr>)}</tbody></table></div></section>
}

function LockedAnalysis({ title, description }) {
  return <section className="rp-card rp-locked-analysis" aria-live="polite"><LockKeyhole size={19} /><div><strong>{title}</strong><p>{description}</p></div></section>
}

function InsightPanel({ company }) {
  return <section className="rp-card rp-insight-card"><div className="rp-section-heading"><div><span className="rp-eyebrow">BƯỚC 03 · INSIGHT</span><h3><Sparkles size={17} /> Tín hiệu cần đọc</h3><p>Insight được sinh từ giá trị đã tính và ngưỡng sàng lọc minh bạch.</p></div><StatusBadge status={company.overall?.status} /></div>{!company.insights?.length ? <div className="rp-empty"><Info size={18} /><span>Chưa đủ dữ liệu để tạo insight đáng tin cậy.</span></div> : <div className="rp-insight-list">{company.insights.map((item, index) => <article className={cx('rp-insight', item.kind === 'strength' ? 'is-strength' : 'is-risk')} key={item.field + '-' + index}><span className="rp-insight-icon">{item.kind === 'strength' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}</span><div><strong>{item.title}</strong><p>{item.detail}</p><small>Trường: {item.field}</small></div></article>)}</div>}<div className="rp-score-grid">{(company.categories || []).map((category) => <div className="rp-score-row" key={category.key}><span>{category.label}</span><div className="rp-score-track"><i style={{ width: (category.score ?? 0) + '%' }} /></div><b>{category.score ?? '—'}</b><StatusBadge status={category.status} /></div>)}</div></section>
}

function ComparisonTable({ result }) {
  const companies = result?.companies || []
  const metrics = result?.comparison?.metrics || []
  return <section className="rp-card rp-comparison-card"><div className="rp-section-heading"><div><span className="rp-eyebrow">BƯỚC 03 · COMPARE</span><h3><GitCompare size={17} /> So sánh bằng chứng</h3><p>Hạng chỉ có ý nghĩa trong nhóm được chọn và cùng kỳ. “—” nghĩa là raw data chưa đủ.</p></div><span className="rp-coverage">{companies.length} doanh nghiệp</span></div><div className="rp-comparison-table-wrap"><table className="rp-comparison-table"><caption className="rp-sr-only">So sánh các chỉ tiêu tài chính giữa các doanh nghiệp</caption><thead><tr><th scope="col">Chỉ tiêu</th>{companies.map((company) => <th scope="col" key={company.ticker}><span>{company.ticker}</span><small>Hạng #{company.overall?.rank || '—'}</small></th>)}</tr></thead><tbody>{metrics.map((metric) => <tr key={metric.field}><th scope="row"><strong>{metric.label}</strong><small>{metric.unit} · {metric.higher_is_better ? 'cao hơn tốt hơn' : 'thấp hơn tốt hơn'}</small><small>Trung vị nhóm: {formatValue(metric.median, metric.unit)}</small></th>{companies.map((company) => { const row = metric.rows?.find((item) => item.ticker === company.ticker); const denominator = metric.rows?.filter((item) => item.value !== null).length || 0; return <td key={company.ticker} className={row?.rank === 1 ? 'is-best' : ''}><b>{formatValue(row?.value, metric.unit)}</b><small>{row?.rank ? '#' + row.rank + '/' + denominator : 'Thiếu dữ liệu'}</small></td> })}</tr>)}</tbody></table></div></section>
}

function ReflectionPanel({ reflection, onChange, onSave, completed, onComplete, saving }) {
  const fields = [
    ['observation', '01 · Observation', 'Bạn quan sát thấy điều gì từ hai chỉ tiêu quan trọng nhất?', 'Ví dụ: Biên lợi nhuận ròng của A cao hơn, nhưng CFO/LNST lại thấp hơn…'],
    ['evidence', '02 · Evidence', 'Bằng chứng nào trong raw data hỗ trợ cho nhận định?', 'Nêu khoản mục, kỳ và giá trị bạn đã mở để kiểm tra.'],
    ['limitation', '03 · Limitation', 'Thiếu dữ liệu hoặc giới hạn nào có thể làm kết luận thay đổi?', 'Ví dụ: khác kỳ báo cáo, khác ngành, thiếu CFO hoặc heuristic chưa xét mùa vụ…'],
  ]
  const ready = fields.every(([key]) => reflection[key].trim().length >= 12)
  return <section className={cx('rp-card', 'rp-reflection', completed && 'is-complete')}><div className="rp-section-heading"><div><span className="rp-eyebrow">BƯỚC 04 · REFLECTION</span><h3><ClipboardCheck size={17} /> Viết lại điều bạn hiểu</h3><p>Đừng chỉ chọn doanh nghiệp đứng đầu. Hãy giải thích quan sát bằng dữ liệu và nêu giới hạn.</p></div>{completed ? <span className="rp-complete-badge"><CheckCircle2 size={14} /> Đã hoàn thành</span> : <span className="rp-coverage">{fields.filter(([key]) => reflection[key].trim().length >= 12).length}/3 câu</span>}</div><div className="rp-reflection-grid">{fields.map(([key, label, prompt, placeholder]) => <label key={key}><span>{label}</span><strong>{prompt}</strong><textarea value={reflection[key]} onChange={(event) => onChange(key, event.target.value)} placeholder={placeholder} rows={4} /></label>)}</div><div className="rp-reflection-actions"><span>{saving ? 'Đang lưu reflection vào kho bài làm BCTC…' : ready ? 'Bạn đã có đủ nội dung để đánh dấu hoàn thành.' : 'Mỗi ô cần tối thiểu 12 ký tự để tạo một reflection có thể đọc lại.'}</span><div><button type="button" className="rp-btn" onClick={onSave} disabled={!ready || saving}><Save size={15} /> Lưu bản nháp</button><button type="button" className="rp-btn is-primary" onClick={onComplete} disabled={!ready || completed || saving}>{saving ? <LoaderCircle className="is-spinning" size={15} /> : completed ? <Check size={15} /> : <CheckCircle2 size={15} />} {saving ? 'Đang lưu…' : completed ? 'Đã hoàn thành' : 'Đánh dấu hoàn thành'}</button></div></div></section>
}

function exportCsv(result) {
  if (!result?.companies?.length) return
  const companies = result.companies
  const lines = [['Xếp hạng', 'Mã', 'Doanh nghiệp', 'Điểm tổng hợp', 'Trạng thái', 'Độ phủ dữ liệu']]
  for (const company of result.ranking || []) lines.push([company.rank, company.ticker, company.company_name, company.score ?? '', company.status, (company.coverage_pct ?? 0) + '%'])
  lines.push([])
  lines.push(['Chỉ tiêu', ...companies.map((company) => company.ticker)])
  for (const metric of result.comparison?.metrics || []) lines.push([metric.label, ...companies.map((company) => { const row = metric.rows?.find((item) => item.ticker === company.ticker); return row?.value ?? '' })])
  const csv = String.fromCharCode(0xfeff) + lines.map((line) => line.map((cell) => '"' + String(cell).replaceAll('"', '""') + '"').join(',')).join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'bctc-practice-lab.csv'; anchor.click(); URL.revokeObjectURL(url)
}

export default function RatioPracticeLab({ workspace }) {
  const currentTicker = workspace?.company?.ticker || ''
  const defaultTickers = useMemo(() => [...new Set([currentTicker, ...(workspace?.peers?.peer_tickers || []).slice(0, 3)].filter(Boolean))], [currentTicker, workspace])
  const [tickerText, setTickerText] = useState(defaultTickers.join(', '))
  const [periodMode, setPeriodMode] = useState(workspace?.controls?.period_mode || 'quarter')
  const [period, setPeriod] = useState('')
  const [hypothesis, setHypothesis] = useState('')
  const [reflection, setReflection] = useState(EMPTY_REFLECTION)
  const [result, setResult] = useState(null)
  const [selectedTicker, setSelectedTicker] = useState(currentTicker)
  const [status, setStatus] = useState('idle')
  const [phase, setPhase] = useState('brief')
  const [error, setError] = useState('')
  const [runHistory, setRunHistory] = useState([])
  const [activeRunId, setActiveRunId] = useState(null)
  const [reflectionCompleted, setReflectionCompleted] = useState(false)
  const [draftSaved, setDraftSaved] = useState(false)
  const [reflectionSync, setReflectionSync] = useState('idle')
  const [rawChallengeCompleted, setRawChallengeCompleted] = useState(false)

  const periods = useMemo(() => {
    const values = [...(workspace?.statements?.income?.periods || []), ...(workspace?.statements?.balance?.periods || [])]
    const normalized = periodMode === 'year' ? values.map((value) => String(value).split('-Q')[0]) : values
    return [...new Set(normalized)].sort().reverse()
  }, [workspace, periodMode])

  function updateReflection(key, value) {
    setDraftSaved(false)
    setReflection((current) => ({ ...current, [key]: value }))
  }

  async function runSimulation(event) {
    event?.preventDefault()
    const parsed = parseTickers(tickerText)
    if (parsed.invalid.length) { setError('Mã không hợp lệ: ' + parsed.invalid.join(', ') + '.'); return }
    if (parsed.tooMany) { setError('Phòng thực hành nhận tối đa 8 mã trong một lần chạy.'); return }
    if (!parsed.tickers.length) { setError('Nhập ít nhất một mã cổ phiếu để bắt đầu bài lab.'); return }
    setStatus('loading'); setError(''); setDraftSaved(false); setReflectionSync('idle'); setRawChallengeCompleted(false)
    try {
      const payload = await runBctcPracticeLab({ tickers: parsed.tickers, periodMode, period, limit: 12 })
      const run = { id: 'run-' + Date.now(), createdAt: new Date().toISOString(), label: hypothesis.trim() ? hypothesis.trim().slice(0, 46) : 'Lần chạy ' + (runHistory.length + 1), tickers: parsed.tickers, result: payload }
      setRunHistory((current) => [run, ...current.filter((item) => item.id !== run.id)].slice(0, 5))
      setActiveRunId(run.id); setResult(payload); setSelectedTicker(payload.companies?.[0]?.ticker || parsed.tickers[0]); setReflectionCompleted(false); setPhase('explore'); setStatus('ready')
      const notices = [...(payload.warnings || []), ...(payload.errors || []).map((item) => item.ticker + ': ' + item.message)]
      if (notices.length) setError(notices.join(' · '))
    } catch (reason) { setError(reason.message || 'Không chạy được mô phỏng BCTC.'); setStatus('error') }
  }

  function selectRun(run) {
    setResult(run.result); setActiveRunId(run.id); setSelectedTicker(run.result.companies?.[0]?.ticker || run.tickers[0]); setStatus('ready'); setPhase('explore'); setError(''); setReflectionCompleted(false); setReflectionSync('idle'); setRawChallengeCompleted(false)
  }

  function resetCurrentLab() {
    setResult(null); setStatus('idle'); setPhase('brief'); setError(''); setReflection(EMPTY_REFLECTION); setReflectionCompleted(false); setActiveRunId(null); setDraftSaved(false); setReflectionSync('idle'); setRawChallengeCompleted(false)
  }

  function saveDraft() {
    try {
      localStorage.setItem('northstar:bctc:reflection:' + (selectedTicker || 'lab'), JSON.stringify({ reflection, hypothesis, updatedAt: new Date().toISOString() }))
      setDraftSaved(true)
    } catch { setError('Không lưu được bản nháp trên thiết bị này.') }
  }

  async function completeReflection() {
    const fields = Object.values(reflection)
    if (fields.some((value) => String(value || '').trim().length < 12) || reflectionCompleted) return

    // Keep the local completion path available for anonymous/offline learners. When a
    // session exists, also persist the reflection through the existing BCTC notes API
    // so instructors and Learn Hub progress can use the evidence later.
    const studentId = currentStudentId()
    const companyId = selectedCompany?.ticker || selectedTicker || currentTicker
    const periodValue = result?.controls?.period || selectedCompany?.period || period || 'latest'
    const content = [
      hypothesis.trim() ? `Giả thuyết: ${hypothesis.trim()}` : '',
      `Quan sát: ${reflection.observation.trim()}`,
      `Bằng chứng: ${reflection.evidence.trim()}`,
      `Giới hạn: ${reflection.limitation.trim()}`,
    ].filter(Boolean).join('\n\n')
    const relatedMetrics = [
      ...(selectedCompany?.raw_inputs || []).map((item) => item.field),
      ...(selectedCompany?.calculated_fields || []).map((item) => item.field),
    ].filter(Boolean).slice(0, 20)

    // Always keep a device-local recovery copy before attempting network sync.
    // This covers anonymous learners and a temporary API outage alike.
    try {
      localStorage.setItem('northstar:bctc:reflection:' + (selectedTicker || 'lab'), JSON.stringify({ reflection, hypothesis, updatedAt: new Date().toISOString() }))
    } catch {
      // The completion itself can still be recorded in memory when storage is unavailable.
    }
    setReflectionSync(studentId ? 'saving' : 'local')
    if (studentId && companyId) {
      try {
        await submitStudentNote({
          student_id: studentId,
          company_id: companyId,
          period: String(periodValue),
          note_content: content,
          related_metrics: relatedMetrics,
        })
        setReflectionSync('saved')
      } catch {
        // A transient API failure must not discard a student's completed work. The
        // local draft remains the recovery path and the UI explains that sync is pending.
        setReflectionSync('pending')
      }
    }
    setReflectionCompleted(true)
    setPhase('reflect')
  }

  const selectedCompany = result?.companies?.find((item) => item.ticker === selectedTicker) || result?.companies?.[0]
  const analysisUnlocked = !selectedCompany || !hasCalculableFields(selectedCompany) || rawChallengeCompleted
  const completed = reflectionCompleted

  return <div className="rp-lab">
    <Workflow phase={phase} />
    <div className="rp-lab-layout">
      <LabBrief learning={result?.learning} hypothesis={hypothesis} onHypothesisChange={setHypothesis} completed={completed} />
      <main className="rp-lab-main">
        <form className="rp-controls" onSubmit={runSimulation}><label className="rp-control-field rp-control-wide"><span><SlidersHorizontal size={14} /> Mã dùng cho thí nghiệm</span><input aria-label="Các mã cổ phiếu so sánh" value={tickerText} onChange={(event) => setTickerText(event.target.value.toUpperCase())} placeholder="FPT, HPG, VCB" /><small>Tối đa 8 mã · phân tách bằng dấu phẩy hoặc khoảng trắng</small></label><label className="rp-control-field"><span>Tần suất</span><select value={periodMode} onChange={(event) => { setPeriodMode(event.target.value); setPeriod('') }}><option value="quarter">Theo quý</option><option value="year">Theo năm</option></select><small>So sánh cùng loại kỳ</small></label><label className="rp-control-field"><span>Kỳ cụ thể <em>(tùy chọn)</em></span><select value={period} onChange={(event) => setPeriod(event.target.value)}><option value="">Mới nhất</option>{periods.map((item) => <option value={item} key={item}>{item}</option>)}</select><small>Bỏ trống để lấy kỳ mới nhất</small></label><button type="submit" className="rp-control-run" disabled={status === 'loading'}>{status === 'loading' ? <LoaderCircle className="is-spinning" size={15} /> : <Play size={15} />} Chạy lab</button></form>
        {error && <div className="rp-alert" role="alert"><AlertTriangle size={17} /><span>{error}</span></div>}
        {draftSaved && <div className="rp-saved-note" role="status"><Check size={15} /> Bản nháp reflection đã lưu trên thiết bị này.</div>}
        {status === 'loading' && <LoadingPanel />}
        {status === 'error' && <section className="rp-error-state"><div className="rp-start-icon"><AlertTriangle size={21} /></div><div><span className="rp-eyebrow">KHÔNG THỂ CHẠY PHIÊN</span><h2>Kiểm tra mã hoặc nguồn dữ liệu rồi thử lại.</h2><p>Phiên học chưa tạo kết quả. Các lần chạy trước trong lịch sử vẫn được giữ nguyên.</p><button type="button" className="rp-btn is-primary" onClick={runSimulation}><RotateCcw size={15} /> Thử lại</button></div></section>}
        {status === 'idle' && <section className="rp-start-card"><div className="rp-start-icon"><Play size={21} /></div><div><span className="rp-eyebrow">SẴN SÀNG BẮT ĐẦU</span><h2>Thiết lập giả thuyết trước khi xem kết quả</h2><p>Nhập một hoặc nhiều mã ở trên, viết dự đoán ngắn ở cột bên trái rồi chạy bài lab. Hệ thống không tự bù số thiếu.</p><button type="button" className="rp-btn is-primary" onClick={runSimulation}><Play size={15} /> Chạy phiên đầu tiên <ArrowRight size={15} /></button></div></section>}
        {status === 'ready' && result && <><DataQualityStrip result={result} /><section className="rp-card rp-ranking"><div className="rp-section-heading"><div><span className="rp-eyebrow">BƯỚC 03 · SO SÁNH</span><h3><ShieldCheck size={17} /> Chọn doanh nghiệp để đọc sâu</h3><p>Điểm tổng hợp là heuristic dùng cho bài học. Hãy ưu tiên mở raw input, công thức và coverage.</p></div><span className="rp-methodology"><Info size={14} /> {result.methodology?.score}</span></div><div className="rp-ranking-grid">{[...(result.companies || [])].sort((a, b) => (a.overall?.rank ?? 999) - (b.overall?.rank ?? 999)).map((company) => <RankingCard key={company.ticker} company={company} selected={selectedCompany?.ticker === company.ticker} onSelect={() => { setSelectedTicker(company.ticker); setRawChallengeCompleted(false); setPhase('explore') }} />)}</div></section>{selectedCompany && <><RawInputs company={selectedCompany} /><RawDataChallenge key={`${selectedCompany.ticker}-${selectedCompany.period || result.controls?.period || 'latest'}`} company={selectedCompany} onComplete={setRawChallengeCompleted} />{analysisUnlocked ? <><CalculatedFields company={selectedCompany} /><InsightPanel company={selectedCompany} /></> : <LockedAnalysis title="Phân tích dẫn xuất đang được khóa" description="Hoàn thành phần tự tính từ raw data để mở đáp án, insight và cách so sánh." />}</>}{analysisUnlocked ? <ComparisonTable result={result} /> : <LockedAnalysis title="Bảng so sánh sẽ mở sau bài tính" description="Bạn vẫn có thể xem raw input và công thức; các giá trị dẫn xuất sẽ hiện sau khi hoàn thành challenge." />}<ReflectionPanel reflection={reflection} onChange={updateReflection} onSave={saveDraft} completed={completed} saving={reflectionSync === 'saving'} onComplete={completeReflection} />{reflectionSync !== 'idle' && <div className={cx('rp-saved-note', reflectionSync === 'pending' ? 'is-warning' : '')} role="status"><Check size={15} />{reflectionSync === 'saving' ? 'Đang đồng bộ reflection lên kho bài làm BCTC…' : reflectionSync === 'saved' ? 'Reflection đã được lưu vào kho bài làm BCTC.' : reflectionSync === 'pending' ? 'Đã đánh dấu hoàn thành trên thiết bị; đồng bộ máy chủ sẽ thử lại khi bạn lưu bản nháp.' : 'Reflection đã lưu trên thiết bị này.'}</div>}<section className="rp-card rp-note"><BookOpen size={17} /><div><strong>Cách đọc kết quả</strong><p>Đọc coverage trước khi kết luận. Hạng #1 chỉ có nghĩa là tốt nhất trong nhóm đang chọn; hãy kiểm tra kỳ, ngành, raw input và giới hạn của heuristic.</p></div></section></>}
      </main>
    </div>
    <footer className="rp-lab-footer"><RunHistory runs={runHistory} activeRunId={activeRunId} onSelect={selectRun} /><div className="rp-footer-actions"><button type="button" className="rp-btn" onClick={() => exportCsv(result)} disabled={!result || !analysisUnlocked} title={analysisUnlocked ? 'Xuất kết quả phiên học' : 'Hoàn thành Raw Data Challenge để mở xuất dữ liệu'}><Download size={15} /> Xuất CSV</button><button type="button" className="rp-btn" onClick={resetCurrentLab}><RotateCcw size={15} /> Đặt lại phiên</button></div></footer>
  </div>
}
