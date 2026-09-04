const VIDEO_EXTENSIONS = new Set(['mp4', 'webm', 'mov', 'm4v', 'avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'flv', '3gp'])

export function filterLocal(items, search) {
  if (!items) return []
  if (!search || !search.trim()) return items
  const q = search.toLowerCase().trim()
  return items.filter((item) => `${item?.title || ''} ${item?.file_name || ''}`.toLowerCase().includes(q))
}

export function filterAssetsByType(items, targetType) {
  return (items || []).filter((item) => {
    const mime = String(item?.mime_type || '').toLowerCase()
    const extension = fileExtension(item?.file_name)
    if (targetType === 'video') return mime.startsWith('video/') || VIDEO_EXTENSIONS.has(extension)
    return true
  })
}

export function fileExtension(fileName) {
  const value = String(fileName || '')
  const index = value.lastIndexOf('.')
  return index <= -1 ? '' : value.slice(index + 1).toLowerCase()
}

export function formatBytes(bytes) {
  const value = Number(bytes)
  if (!Number.isFinite(value) || value <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  return `${(value / (1024 ** index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

