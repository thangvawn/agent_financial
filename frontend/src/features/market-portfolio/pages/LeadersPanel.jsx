import { useEffect, useState } from 'react'
import { fetchMpLeaders } from '../services'

export default function LeadersPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        const payload = await fetchMpLeaders()
        if (!cancelled) {
          setData(payload)
          setError('')
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
  }, [])

  const filtered = data?.items.filter(item => {
    const needle = search.trim().toLowerCase()
    if (!needle) return true
    return (
      item.name.toLowerCase().includes(needle) ||
      item.company.toLowerCase().includes(needle) ||
      item.company_name.toLowerCase().includes(needle)
    )
  }) || []

  return (
    <section className="mp-panel leaders-panel" style={{ padding: '0 clamp(16px, 2.6vw, 42px) 24px' }}>
      <div className="gt-action-bar" style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px', borderBottom: '1px solid var(--line)', paddingBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0, color: 'var(--ink)' }}>DANH NHÂN & LÃNH ĐẠO</h2>
            <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(245,158,11,0.1)', color: '#f59e0b', fontWeight: '600' }}>INFLUENTIAL LEADERS</span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--ink-subtle)' }}>Cập nhật: Mới nhất</span>
        </div>

        {/* Search bar */}
        <div style={{ position: 'relative', width: '100%', maxWidth: '360px' }}>
          <input
            type="text"
            placeholder="Tìm theo tên doanh nhân hoặc mã cổ phiếu..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid var(--line)',
              background: 'rgba(255,255,255,0.02)',
              color: 'var(--ink)',
              fontSize: '13px',
              outline: 'none',
              transition: 'border-color 0.2s'
            }}
          />
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--ink-muted)' }}>Đang tải danh sách doanh nhân...</div>
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--neg)' }}>Lỗi: {error}</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {filtered.length === 0 ? (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '32px', color: 'var(--ink-muted)' }}>Không tìm thấy doanh nhân nào khớp với từ khóa.</div>
          ) : (
            filtered.map((item) => (
              <div
                key={item.id}
                style={{
                  background: 'rgba(255,255,255,0.015)',
                  border: '1px solid var(--line)',
                  borderRadius: '16px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  transition: 'transform 0.2s, border-color 0.2s',
                  position: 'relative',
                  overflow: 'hidden'
                }}
                className="leader-card"
              >
                {/* Header profile row */}
                <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, var(--gt-accent), #f59e0b)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                      fontWeight: '800',
                      color: '#ffffff',
                      boxShadow: '0 4px 12px rgba(245,158,11,0.2)'
                    }}
                  >
                    {item.avatar_char}
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', color: 'var(--ink)' }}>{item.name}</h3>
                    <span style={{ fontSize: '11px', color: 'var(--gt-accent)', fontWeight: '600' }}>
                      {item.company} • {item.company_name}
                    </span>
                  </div>
                </div>

                {/* Info values */}
                <div style={{ fontSize: '13px', color: 'var(--ink-subtle)', lineHeight: '1.4' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.03)', padding: '6px 0' }}>
                    <span>Chức vụ:</span>
                    <span style={{ fontWeight: '600', color: 'var(--ink)' }}>{item.position}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.03)', padding: '6px 0' }}>
                    <span>Sinh năm / Quê quán:</span>
                    <span style={{ fontWeight: '500' }}>{item.birth_year} ({item.hometown})</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.03)', padding: '6px 0' }}>
                    <span>Giá trị tài sản sở hữu (Ước tính):</span>
                    <span style={{ fontWeight: '800', color: '#fbbf24' }}>{item.shares_value_vnd_b.toLocaleString('vi-VN')} tỷ VNĐ</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                    <span>Giao dịch nội bộ (12 tháng):</span>
                    <span style={{ fontWeight: '600', color: 'var(--pos)' }}>{item.insider_transactions_count} lệnh</span>
                  </div>
                </div>

                {/* Bio text */}
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--ink-muted)', lineHeight: '1.5', borderTop: '1px solid var(--line)', paddingTop: '10px', fontStyle: 'italic' }}>
                  "{item.bio}"
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </section>
  )
}
