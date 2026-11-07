import { periodKey, readCalculatorReport } from './calculatorReport'
import { METRICS, calculateMetric } from './financialMetrics'

export function marginChartData(workspace) {
  const periods = [...(workspace?.trend?.periods || [])]
  const ratios = new Map((workspace?.ratio_groups || []).flatMap((group) => (group.metrics || []).map((metric) => [metric.key, metric])))
  const specs = [['is-gross', 'gross_margin_pct', 'gross_margin', 'Biên gộp'], ['is-operating', 'operating_margin_pct', 'operating_margin', 'Biên hoạt động'], ['is-net', 'net_margin_pct', 'net_margin', 'Biên ròng']]
  const lines = specs.map(([name, ratioKey, metricId, label]) => {
    const metric = METRICS.find((item) => item.id === metricId)
    const values = periods.map((period) => {
      const raw = ratios.get(ratioKey)?.series?.find((item) => periodKey(item.period) === periodKey(period))?.value
      const number = raw === null || raw === undefined || raw === '' ? null : Number(raw)
      return number !== null && Number.isFinite(number) ? number : calculateMetric(metric, readCalculatorReport(workspace, period, 1).values)
    })
    return { name, label, values }
  })
  return { periods, lines }
}
