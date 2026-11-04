import { useEffect, useRef, useState } from 'react'
import { Link2, RefreshCw, Search, SlidersHorizontal } from 'lucide-react'
import NewsWorkspaceTabs from './components/NewsWorkspaceTabs'
import SocialFeed from './components/SocialFeed'
import SocialReader from './components/SocialReader'
import SocialSources from './components/SocialSources'
import useSocialFeed from './hooks/useSocialFeed'
import { socialRequest } from '../services/socialApi'
import './news.css'
import './social.css'

export default function SocialPage({ sessionId, onOpenNews }) {
  const feed = useSocialFeed(sessionId)
  const [selected, setSelected] = useState('')
  const [detail, setDetail] = useState(null)
  const [detailError, setDetailError] = useState('')
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailVersion, setDetailVersion] = useState(0)
  const [mobileReader, setMobileReader] = useState(false)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [importMarket, setImportMarket] = useState('vietnam')
  const [busy, setBusy] = useState(false)
  const [saving, setSaving] = useState('')
  const [notice, setNotice] = useState('')
  const [actionError, setActionError] = useState('')
  const readerRef = useRef(null)
  const activeId = feed.data?.topics.some(t => t.id === selected) ? selected : feed.data?.topics[0]?.id || ''
  const topic = detail?.scopeId === activeId ? detail : null
  const activeJobs = feed.sourceData?.jobs.filter(j => ['queued', 'running'].includes(j.status)) || []

  useEffect(() => {
    if (!activeId) return
    const controller = new AbortController()
    setDetailLoading(true); setDetailError('')
    socialRequest(`/topics/${encodeURIComponent(activeId)}`, sessionId, { signal: controller.signal })
      .then(result => setDetail({ ...result, scopeId: activeId }))
      .catch(e => { if (e.name !== 'AbortError') setDetailError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setDetailLoading(false) })
    return () => controller.abort()
  }, [sessionId, activeId, detailVersion, feed.data?.as_of])

  useEffect(() => {
    if (mobileReader && window.matchMedia('(max-width: 899px)').matches) readerRef.current?.scrollIntoView({ block: 'start' })
  }, [mobileReader, activeId])

  async function mutate(path, method = 'POST', body, success = '') {
    if (busy) return false
    setBusy(true); setActionError(''); setNotice('')
    try {
      await socialRequest(path, sessionId, { method, body })
      setNotice(success); feed.refresh(); return true
    } catch (e) { setActionError(e.message); return false }
    finally { setBusy(false) }
  }
  const collect = () => mutate('/refresh', 'POST', null, 'Đã xếp lịch thu thập. Bạn có thể tiếp tục đọc trong lúc chờ.')
  async function importLink(e) {
    e.preventDefault()
    if (await mutate('/imports', 'POST', { url, market: importMarket }, 'Đã nhận liên kết. Bài đọc được sẽ xuất hiện trong Đã lưu.')) {
      setUrl(''); setImportOpen(false); feed.updateFilters({ scope: 'saved', market: 'all', platform: 'all', q: '' })
    }
  }
  async function save(post) {
    if (saving) return
    setSaving(post.id); setActionError('')
    try {
      await socialRequest(`/posts/${post.id}/save`, sessionId, { method: post.saved ? 'DELETE' : 'POST' })
      setDetail(previous => previous && ({ ...previous, posts: previous.posts.map(p => p.id === post.id ? { ...p, saved: !p.saved } : p) }))
      setNotice(post.saved ? 'Đã bỏ lưu bài.' : 'Đã lưu bài vào tài khoản của bạn.'); feed.refresh()
    } catch (e) { setActionError(e.message) }
    finally { setSaving('') }
  }
  const filters = patch => { setSelected(''); setMobileReader(false); feed.updateFilters(patch) }

  return <section className="news-desk social-desk">
    <NewsWorkspaceTabs active="news_social" onNews={onOpenNews} />
    <header className="social-header"><div><h1>Thảo luận thị trường</h1><p>Góc nhìn từ cộng đồng Việt Nam và quốc tế, cùng nguồn gốc để đối chiếu.</p></div>
      <div className="social-header-actions">
        <button onClick={() => setImportOpen(v => !v)} aria-expanded={importOpen}><Link2 size={16} />Thêm liên kết</button>
        <button onClick={() => setSourcesOpen(v => !v)} aria-expanded={sourcesOpen}><SlidersHorizontal size={16} />Nguồn theo dõi</button>
        <button className="social-primary" disabled={busy || activeJobs.length > 0} onClick={collect}><RefreshCw size={15} />{busy ? 'Đang gửi…' : activeJobs.length ? 'Đang thu thập' : 'Cập nhật'}</button>
      </div>
    </header>
    {importOpen && <form className="social-import" onSubmit={importLink}>
      <label>Liên kết công khai<input type="url" required maxLength={2048} value={url} onChange={e => setUrl(e.target.value)} placeholder="https://www.youtube.com/watch?v=… hoặc bài Reddit" /></label>
      <label>Phạm vi<select aria-label="Phạm vi của liên kết" value={importMarket} onChange={e => setImportMarket(e.target.value)}><option value="vietnam">Việt Nam</option><option value="global">Quốc tế</option></select></label>
      <button className="social-primary" disabled={busy} type="submit">Thêm vào Đã lưu</button>
    </form>}
    {actionError && <p role="alert" className="social-error">{actionError}</p>}
    {notice && <p role="status" className="social-notice">{notice}</p>}
    {sourcesOpen && <SocialSources status={feed.sourceData} busy={busy}
      onToggle={(id, enabled) => mutate(`/subscriptions/${id}`, 'PATCH', { enabled })}
      onAdd={body => mutate('/subscriptions', 'POST', body, 'Đã thêm nguồn. Chọn Cập nhật để thu thập.')}
      onDelete={id => mutate(`/subscriptions/${id}`, 'DELETE', null, 'Đã bỏ nguồn theo dõi.')} />}
    <div className="social-toolbar">
      <div className="social-segment" role="group" aria-label="Phạm vi thị trường">
        {[['all', 'Tất cả'], ['vietnam', 'Việt Nam'], ['global', 'Quốc tế']].map(([value, label]) => <button key={value} aria-pressed={feed.filters.market === value} onClick={() => filters({ market: value })}>{label}</button>)}
      </div>
      <label className="social-search"><Search size={16} aria-hidden="true" /><span className="sr-only">Tìm mã hoặc chủ đề</span><input value={feed.filters.q} maxLength={120} placeholder="Tìm mã hoặc chủ đề…" onChange={e => filters({ q: e.target.value })} /></label>
      <label><span className="sr-only">Lọc nền tảng</span><select aria-label="Lọc nền tảng" value={feed.filters.platform} onChange={e => filters({ platform: e.target.value })}><option value="all">Mọi nền tảng</option><option value="youtube">YouTube</option><option value="reddit">Reddit</option></select></label>
      <label><span className="sr-only">Khoảng thời gian</span><select aria-label="Khoảng thời gian" disabled={feed.filters.scope === 'saved'} value={feed.filters.hours} onChange={e => filters({ hours: e.target.value })}><option value="24">24 giờ</option><option value="168">7 ngày</option></select></label>
    </div>
    <div className="social-scope-bar"><div className="social-scopes" role="group" aria-label="Danh sách bài">
      {[['all', 'Khám phá'], ['watchlist', 'Theo watchlist'], ['saved', 'Đã lưu']].map(([value, label]) => <button key={value} aria-pressed={feed.filters.scope === value} onClick={() => filters({ scope: value })}>{label}</button>)}
    </div><span>{activeJobs.length ? `${activeJobs.length} lượt đang chờ / đang chạy` : 'Mẫu từ các nguồn theo dõi · Chưa đại diện toàn thị trường'}</span></div>
    {feed.sourceError && <p role="alert" className="social-error">Không đọc được trạng thái nguồn. {feed.sourceError}</p>}
    {feed.sourceData && !feed.sourceData.collector_configured && <p className="social-notice">Bộ thu thập chưa được kết nối. Các bài đã lưu vẫn có thể đọc.</p>}
    {feed.sourceData?.collector_configured && !feed.sourceData.worker_active && activeJobs.length > 0 && <p role="status" className="social-notice">Lượt thu thập đã được lưu, đang chờ tiến trình thu thập hoạt động.</p>}
    {feed.sourceData?.jobs[0]?.status === 'failed' && <p role="status" className="social-notice">{feed.sourceData.jobs[0].message}</p>}
    <div className={`social-grid${mobileReader && activeId ? ' is-reading' : ''}`}>
      <div className="social-stream"><SocialFeed {...feed} selected={activeId} scope={feed.filters.scope}
        onSelect={id => { setSelected(id); setMobileReader(true) }} onMore={feed.loadMore} onRetry={feed.refresh} onCollect={collect} /></div>
      <div className="social-detail" ref={readerRef}><SocialReader topic={topic} loading={Boolean(activeId) && detailLoading} error={activeId ? detailError : ''}
        onSave={save} saving={saving} onBack={() => setMobileReader(false)} onRetry={() => setDetailVersion(v => v + 1)} /></div>
    </div>
  </section>
}
