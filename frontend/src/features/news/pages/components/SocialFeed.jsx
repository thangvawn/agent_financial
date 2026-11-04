import { ArrowUpRight, Bookmark, MessageSquareText } from 'lucide-react'
import { safeSocialUrl } from '../../services/socialApi'
import { platformLabel, socialDate } from '../socialLabels'

export default function SocialFeed({ data, loading, loadingMore, error, selected, onSelect, onMore, onRetry, onCollect, scope, pending }) {
  if (loading && !data) return <div className="social-loading" role="status">Đang tải thảo luận…</div>
  if (!data?.topics?.length && !error) return <div className="social-empty">
    <MessageSquareText size={30} strokeWidth={1.4} aria-hidden="true" />
    <h2>{scope === 'saved' ? 'Chưa có bài đã lưu' : scope === 'watchlist' ? 'Chưa có thảo luận khớp watchlist' : 'Chưa có thảo luận trong phạm vi này'}</h2>
    <p>{scope === 'saved' ? 'Lưu một bài hoặc thêm liên kết để quay lại đọc sau.'
      : 'Thu thập từ các nguồn đang theo dõi, hoặc thử phạm vi và khoảng thời gian khác.'}</p>
    {scope === 'all' && <button type="button" className="social-primary" onClick={onCollect}>Thu thập bài viết</button>}
  </div>
  return <div className="social-feed" aria-busy={loading}>
    <div className="social-feed-heading"><h2>Dòng thảo luận</h2><span>{data?.total ?? 0} chủ đề</span></div>
    {pending && <button className="social-update-note" onClick={onRetry}>Có dữ liệu mới — cập nhật danh sách</button>}
    {error && <div className="social-error" role="alert">{error} <button onClick={onRetry}>Thử lại</button></div>}
    <ol className="social-feed-list">
      {(data?.topics || []).map(topic => <li key={topic.id} className={selected === topic.id ? 'is-selected' : ''}>
        <button type="button" className="social-topic" onClick={() => onSelect(topic.id)} aria-pressed={selected === topic.id}>
          <span className="social-topic-meta"><span>{topic.platforms.map(platformLabel).join(' · ')}</span>
            <span>{socialDate(topic.lead)}</span></span>
          <strong>{topic.title}</strong>
          {topic.preview && <span className="social-topic-preview">{topic.preview}</span>}
          <span className="social-topic-footer"><span>{topic.lead.author || 'Chưa rõ tác giả'}</span>
            <span>{topic.post_count > 1 ? `${topic.post_count} bài liên quan` : '1 bài'}{topic.lead.saved && <Bookmark size={13} aria-label="Đã lưu" />}</span></span>
          {topic.entities.length > 0 && <span className="social-entities">{topic.entities.map(entity => <span key={entity.id}>{entity.symbol}</span>)}</span>}
        </button>
        <a className="social-topic-link" href={safeSocialUrl(topic.lead.url) || undefined} target="_blank" rel="noopener noreferrer" aria-label={`Mở nguồn: ${topic.title}`}><ArrowUpRight size={16} /></a>
      </li>)}
    </ol>
    {data?.has_more && <button type="button" className="social-load-more" disabled={loadingMore} onClick={onMore}>{loadingMore ? 'Đang tải…' : 'Xem thêm thảo luận'}</button>}
  </div>
}
