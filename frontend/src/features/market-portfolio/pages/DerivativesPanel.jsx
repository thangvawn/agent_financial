import { useEffect, useState } from 'react'
import { fetchMpDerivativesSnapshot } from '../services'

export default function DerivativesPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        const payload = await fetchMpDerivativesSnapshot()
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
    const timer = setInterval(load, 30000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  function formatChange(val) {
    if (val === null || val === undefined) return '-'
    return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
  }

  function formatNumber(val, digits = 1) {
    if (val === null || val === undefined || Number.isNaN(Number(val))) return '-'
    return Number(val).toLocaleString('vi-VN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
  }

  function getPriceClass(price, ref, ceil, floor) {
    if (!price || !ref) return ''
    if (price >= ceil) return 'is-ceil'
    if (price <= floor) return 'is-floor'
    if (price > ref) return 'is-pos'
    if (price < ref) return 'is-neg'
    return 'is-ref'
  }

  return (
    <section className="mp-panel derivatives-panel" style={{ padding: '0 clamp(16px, 2.6vw, 42px) 24px' }}>
      <div className="gt-action-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--line)', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0, color: 'var(--ink)' }}>BẢNG GIÁ PHÁI SINH</h2>
          <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(56,189,248,0.1)', color: '#38bdf8', fontWeight: '600' }}>VN30 FUTURES</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--ink-subtle)' }}>
          <span className={`gt-status-dot ${data?.freshness === 'stale' ? '' : 'is-live'}`} />
          <span>{data?.freshness === 'realtime' ? 'REALTIME' : data?.freshness === 'near_realtime' ? 'NEAR REALTIME' : data?.freshness === 'unavailable' ? 'UNAVAILABLE' : 'STALE'}</span>
          <span>•</span>
          <span>{data?.source || 'Đang tải...'}</span>
          <span>•</span>
          <span>Cập nhật: {data?.as_of ? new Date(data.as_of).toLocaleTimeString('vi-VN') : 'Đang tải...'}</span>
        </div>
      </div>

      {loading && !data ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--ink-muted)' }}>Đang tải dữ liệu phái sinh...</div>
      ) : error ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--neg)' }}>Lỗi: {error}</div>
      ) : data?.freshness === 'unavailable' ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--ink-muted)' }}>
          Chưa nhận được quote phái sinh từ nguồn dữ liệu. Backend sẽ tự thử lại ở lần cập nhật tiếp theo.
          {data?.errors?.length ? <div style={{ fontSize: '11px', marginTop: '8px', color: 'var(--neg)' }}>Nguồn hiện không kết nối được.</div> : null}
        </div>
      ) : (
        <div className="gt-priceboard-container" style={{ overflowX: 'auto', border: '1px solid var(--line)', borderRadius: '12px', background: 'rgba(255,255,255,0.01)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '900px' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--line-strong)', textAlign: 'right' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Mã HĐ</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Giá Khớp</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>+/-</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>%</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Lệch (Basis)</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Mở Cửa</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Cao Nhất</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Thấp Nhất</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Tổng KL</th>
                <th style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>HĐ Mở (OI)</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((row) => {
                const priceClass = getPriceClass(row.price, row.ref, row.ceil, row.floor)
                const changeClass = row.change == null ? '' : row.change >= 0 ? 'is-pos' : 'is-neg'
                const basisClass = row.basis == null ? '' : row.basis >= 0 ? 'is-pos' : 'is-neg'

                return (
                  <tr key={row.symbol} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', textAlign: 'right' }} className="gt-priceboard-row">
                    <td style={{ padding: '14px 16px', textAlign: 'left', fontWeight: '700', fontSize: '13px', color: 'var(--ink)' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span>{row.symbol}</span>
                        <span style={{ fontSize: '10px', color: 'var(--ink-subtle)', fontWeight: '400' }}>{row.name}</span>
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', fontWeight: '700' }} className={`num ${priceClass}`}>
                      {formatNumber(row.price)}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', fontWeight: '600' }} className={`num ${changeClass}`}>
                      {row.change == null ? '-' : `${row.change >= 0 ? '+' : ''}${formatNumber(row.change)}`}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', fontWeight: '600' }} className={`num ${changeClass}`}>
                      {formatChange(row.change_pct)}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', fontWeight: '600' }} className={`num ${basisClass}`}>
                      {row.basis == null ? '-' : `${row.basis >= 0 ? '+' : ''}${formatNumber(row.basis)}`}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', color: 'var(--ink-muted)' }} className="num">
                      {formatNumber(row.open)}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', color: 'var(--ink-muted)' }} className="num">
                      {formatNumber(row.high)}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', color: 'var(--ink-muted)' }} className="num">
                      {formatNumber(row.low)}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', color: 'var(--ink)' }} className="num">
                      {row.volume == null ? '-' : Number(row.volume).toLocaleString('vi-VN')}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: '13px', color: 'var(--gt-accent)', fontWeight: '600' }} className="num">
                      {row.open_interest == null ? '-' : Number(row.open_interest).toLocaleString('vi-VN')}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
