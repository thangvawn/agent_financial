function formatVnd(value) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return new Intl.NumberFormat('vi-VN').format(Math.round(Number(value)))
}

export { formatVnd }
