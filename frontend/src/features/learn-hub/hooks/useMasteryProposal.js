export function resolveMasteryThreshold(options = {}) {
  const tier = (options?.tier || '').toLowerCase().trim()
  const role = (options?.role || '').toLowerCase().trim()

  if (['community', 'free', 'starter'].includes(tier) || role === 'retail') {
    return 75
  }
  if (['pro', 'enterprise'].includes(tier) || ['institutional', 'pro'].includes(role)) {
    return 85
  }
  return 80
}
