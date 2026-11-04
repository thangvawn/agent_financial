import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { platformLabel } from '../socialLabels'

function SourceSwitch({ source, busy, onToggle }) {
  const [checked, setChecked] = useState(Boolean(source.enabled))
  async function toggle(event) {
    const enabled = event.target.checked
    setChecked(enabled)
    if (!await onToggle(source.id, enabled)) setChecked(Boolean(source.enabled))
  }
  return <input type="checkbox" checked={checked} onChange={toggle} disabled={busy} />
}

export default function SocialSources({ status, onToggle, onAdd, onDelete, busy }) {
  const [adding, setAdding] = useState(false)
  const [label, setLabel] = useState('')
  const [query, setQuery] = useState('')
  const [platform, setPlatform] = useState('youtube')
  const [market, setMarket] = useState('vietnam')
  async function submit(event) {
    event.preventDefault()
    if (await onAdd({ label, query, platform, market })) { setLabel(''); setQuery(''); setAdding(false) }
  }
  return <section className="social-sources" aria-label="Quản lý nguồn theo dõi">
    <div className="social-section-heading"><div><h2>Nguồn đang theo dõi</h2><p>Tìm bài công khai theo chủ đề. Tắt nguồn để dừng thu thập và ẩn khỏi dòng tin.</p></div>
      <button type="button" onClick={() => setAdding(v => !v)} aria-expanded={adding}><Plus size={15} /> Thêm nguồn</button></div>
    <div className="social-source-list">{(status?.sources || []).map(source => <div key={source.id} className="social-source-row">
      <label><SourceSwitch key={source.enabled} source={source} busy={busy} onToggle={onToggle} />
        <span><strong>{source.label}</strong><small>{platformLabel(source.platform)} · {source.market === 'vietnam' ? 'Việt Nam' : 'Quốc tế'} · {source.query}</small></span></label>
      <div className="social-source-health"><span>{source.error_message || (source.last_success_at ? `Đã cập nhật ${new Date(source.last_success_at * 1000).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}` : 'Chưa thu thập')}
        {source.partial_count > 0 && <small>{source.partial_count} mục chưa đọc đủ nội dung</small>}</span>
        {!source.id.startsWith('youtube-') && !source.id.startsWith('reddit-') && <button type="button" disabled={busy} onClick={() => onDelete(source.id)} aria-label={`Bỏ nguồn ${source.label}`}><Trash2 size={15} /></button>}
      </div>
    </div>)}</div>
    {adding && <form className="social-source-form" onSubmit={submit}>
      <label>Tên nguồn<input required minLength={3} maxLength={80} value={label} onChange={e => setLabel(e.target.value)} placeholder="Ví dụ: Công nghệ Việt Nam" /></label>
      <label>Chủ đề tìm kiếm<input required minLength={3} maxLength={120} value={query} onChange={e => setQuery(e.target.value)} placeholder="FPT kết quả kinh doanh" /></label>
      <label>Nền tảng<select value={platform} onChange={e => setPlatform(e.target.value)}><option value="youtube">YouTube</option><option value="reddit">Reddit</option></select></label>
      <label>Thị trường<select value={market} onChange={e => setMarket(e.target.value)}><option value="vietnam">Việt Nam</option><option value="global">Quốc tế</option></select></label>
      <button type="submit" className="social-primary" disabled={busy}>Theo dõi nguồn</button>
    </form>}
  </section>
}
