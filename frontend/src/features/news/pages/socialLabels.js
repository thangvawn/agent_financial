export const platformLabel = platform => platform === 'youtube' ? 'YouTube' : 'Reddit'

export function socialDate(post) {
  if (!post.published_at) return 'Chưa rõ ngày đăng'
  const date = new Date(post.published_at)
  if (Number.isNaN(date.valueOf())) return 'Chưa rõ ngày đăng'
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric',
    ...(post.time_precision === 'day' ? { timeZone: 'UTC' } : {}) }).format(date)
}
