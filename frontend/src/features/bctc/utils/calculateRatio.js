export function calculateRatio(numerator, denominator, multiplier = 1) {
  if (numerator === undefined || numerator === null || numerator === '' || denominator === undefined || denominator === null || denominator === '') return null
  const a = Number(numerator); const b = Number(denominator)
  return Number.isFinite(a) && Number.isFinite(b) && b !== 0 ? a / b * multiplier : null
}
