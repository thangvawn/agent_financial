import { periodKey } from './calculatorReport'

export function comparablePeriods(period) {
  const key = periodKey(period)
  const quarter = key.match(/^(\d{4})-Q([1-4])$/)
  if (quarter) {
    const year = Number(quarter[1]); const q = Number(quarter[2])
    return { previous: q === 1 ? `${year - 1}-Q4` : `${year}-Q${q - 1}`, yearAgo: `${year - 1}-Q${q}` }
  }
  return /^\d{4}$/.test(key) ? { previous: String(Number(key) - 1), yearAgo: '' } : { previous: '', yearAgo: '' }
}
export function compareReading(value, reference) {
  if (value === null || value === undefined || reference === null || reference === undefined || !Number.isFinite(Number(value)) || !Number.isFinite(Number(reference))) return null
  const current = Number(value); const base = Number(reference)
  return { difference: current - base, relative: base > 0 ? (current - base) / base * 100 : null }
}
