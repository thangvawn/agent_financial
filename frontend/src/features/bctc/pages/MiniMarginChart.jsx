import { marginChartData } from '../utils/marginChartData'

function formatMargin(value) {
  return value === null ? '—' : `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(value)}%`
}

function lineSegments(values, min, max) {
  const span = max - min || 1
  const segments = []
  let segment = []
  values.forEach((value, index) => {
    if (value === null) { if (segment.length) segments.push(segment); segment = []; return }
    const x = values.length === 1 ? 190 : 4 + index / (values.length - 1) * 372
    const y = 128 - ((value - min) / span) * 116
    segment.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  })
  if (segment.length) segments.push(segment)
  return segments
}

export default function MiniMarginChart({ workspace }) {
  const { periods, lines } = marginChartData(workspace)
  const finite = lines.flatMap((line) => line.values.filter((value) => value !== null))
  if (!finite.length) return <div className="bcl-chart-empty" role="status">Chưa có dữ liệu biên lợi nhuận cho các kỳ này.</div>
  const min = Math.min(...finite, 0); const max = Math.max(...finite, 1)
  return <div className="bcl-line-chart">
    <svg role="img" aria-label="Biên lợi nhuận theo kỳ; các đường cùng thang đo, khoảng trống là dữ liệu thiếu" viewBox="0 0 380 140" preserveAspectRatio="none">{lines.flatMap(({ name, label, values }) => lineSegments(values, min, max).map((points, index) => <g key={`${name}-${index}`}><polyline className={name} points={points.join(' ')} />{points.map((point, pointIndex) => { const [cx, cy] = point.split(','); return <circle className={name} key={pointIndex} cx={cx} cy={cy} r="2.5"><title>{label}</title></circle> })}</g>))}</svg>
    <div className="bcl-line-labels">{periods.map((period) => <span key={period}>{period}</span>)}</div>
    <details className="bcl-chart-data"><summary>Xem số liệu (%)</summary><table><thead><tr><th>Kỳ</th>{lines.map((line) => <th key={line.name}>{line.label}</th>)}</tr></thead><tbody>{periods.map((period, index) => <tr key={period}><th>{period}</th>{lines.map((line) => <td key={line.name}>{formatMargin(line.values[index])}</td>)}</tr>)}</tbody></table></details>
  </div>
}

