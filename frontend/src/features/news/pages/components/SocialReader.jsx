import { ArrowLeft, ArrowUpRight, Bookmark, BookmarkCheck, FileText } from 'lucide-react'
import { platformLabel, socialDate } from '../socialLabels'
import { safeSocialUrl } from '../../services/socialApi'

const contentLabel = kind => ({ description: 'Mô tả video', transcript: 'Phụ đề video', search_excerpt: 'Trích đoạn tìm kiếm', public_page: 'Nội dung trang công khai' }[kind] || 'Trích đoạn nguồn')

export default function SocialReader({ topic, loading, error, onSave, saving, onBack, onRetry, notice }) {
  if (loading) return <div className="social-loading" role="status">Đang mở thảo luận…</div>
  if (error) return <div className="social-error" role="alert">{error}<button onClick={onRetry}>Thử lại</button></div>
  if (!topic) return <div className="social-reader-placeholder"><FileText size={26} aria-hidden="true" /><h2>Đọc cùng nguồn gốc</h2><p>Chọn một thảo luận để xem trích đoạn, tác giả và bài viết liên quan.</p></div>
  return <article className="social-reader" aria-label="Chi tiết thảo luận">
    <button type="button" className="social-back" onClick={onBack}><ArrowLeft size={16} /> Trở lại danh sách</button>
    <div className="social-reader-meta"><span>{topic.posts.map(p => platformLabel(p.platform)).filter((v, i, a) => a.indexOf(v) === i).join(' · ')}</span><span>{topic.post_count} bài · {topic.author_count} tài khoản có tên</span></div>
    <h2>{topic.title}</h2>
    <div className="social-reader-method"><FileText size={15} aria-hidden="true" /><span>Tổng hợp trích đoạn · Chưa xác minh độc lập</span></div>
    {notice && <p role="status" className="social-notice">{notice}</p>}
    {topic.evidence.length > 0 && <section className="social-evidence" aria-label="Trích đoạn có nguồn">
      <h3>Nội dung được nhắc đến</h3>
      {topic.evidence.map(e => <figure key={`${e.post_id}-${e.revision}`}><blockquote>{e.excerpt}</blockquote>
        <figcaption><a href={safeSocialUrl(e.url) || undefined} target="_blank" rel="noopener noreferrer">{e.author || 'Bài gốc'} · {platformLabel(e.platform)} <ArrowUpRight size={13} aria-hidden="true" /></a>
          <span>{contentLabel(e.content_kind)}</span></figcaption></figure>)}
    </section>}
    <section className="social-originals" aria-label="Bài viết gốc"><h3>Bài viết gốc</h3>
      {topic.posts.map(post => <div className="social-original" key={post.id}>
        <div className="social-original-top"><span>{platformLabel(post.platform)} · {socialDate(post)}</span>
          <button type="button" disabled={saving === post.id} onClick={() => onSave(post)} aria-label={post.saved ? `Bỏ lưu: ${post.title}` : `Lưu: ${post.title}`}>
            {post.saved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}{post.saved ? 'Đã lưu' : 'Lưu bài'}
          </button></div>
        <a className="social-original-title" href={safeSocialUrl(post.url) || undefined} target="_blank" rel="noopener noreferrer">{post.title}<ArrowUpRight size={16} aria-hidden="true" /></a>
        <p className="social-author">{post.author || 'Chưa rõ tác giả'} · {contentLabel(post.content_kind)}</p>
        {post.text && <details><summary>Đọc nội dung đã thu thập</summary><p className="social-original-text">{post.text}</p></details>}
        {post.platform === 'youtube' && <div className="social-transcript">{post.transcript
          ? <details><summary>Đọc phụ đề</summary><p className="social-original-text">{post.transcript}</p></details>
          : <p>{post.transcript_status === 'not_requested' ? 'Thêm liên kết video để đọc phụ đề khi nguồn cung cấp.' : 'Chưa đọc được phụ đề của video này.'}</p>}</div>}
      </div>)}
    </section>
    {topic.related_news.length > 0 && <section className="social-related"><h3>Tin tức cùng tài sản</h3><p>Các bài dưới đây giúp đọc thêm bối cảnh; chưa xác nhận các nhận định trong thảo luận.</p>
      {topic.related_news.map(item => <a key={item.article_id} href={/^https:\/\//.test(item.url) ? item.url : undefined} target="_blank" rel="noopener noreferrer">{item.headline}<span>{item.source}</span></a>)}
    </section>}
  </article>
}
