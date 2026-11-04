import { PRESET_PACKS } from '../services/filterPresetData'
import './screener-results.css'

const REASONS = {
  history_missing: 'Chưa có lịch sử chuẩn hóa', adjustment_unverified: 'Chưa xác minh điều chỉnh giá',
  volume_basis_unverified: 'Chưa xác minh khối lượng qua ngày quyền', provenance_missing: 'Thiếu nguồn dữ liệu',
  price_unit_unknown: 'Chưa xác định đơn vị giá', history_quality_flag: 'Lịch sử cần kiểm tra chất lượng',
  calendar_missing: 'Chưa có lịch phiên đã xác nhận', history_stale: 'Lịch sử chưa đến phiên chốt',
  not_common_stock: 'Chưa xác nhận là cổ phiếu phổ thông', not_trading: 'Không có giao dịch hoặc bị đình chỉ',
  missing_sessions: 'Thiếu phiên lịch sử', turnover_history_missing: 'Thiếu lịch sử giá trị khớp lệnh',
  insufficient_liquidity: 'Chưa đạt ngưỡng thanh khoản', insufficient_history: 'Chưa đủ số phiên tính toán',
  indicator_missing: 'Thiếu chỉ báo hoặc dữ liệu so sánh', fundamentals_missing_or_not_public: 'Thiếu BCTC đã công bố',
  financial_sector_profile_pending: 'Chưa có bộ chỉ tiêu riêng cho ngành tài chính', fundamentals_stale: 'BCTC đã cũ',
  dividend_events_missing: 'Thiếu lịch sử cổ tức đã xác nhận', foreign_history_missing: 'Thiếu lịch sử khối ngoại',
  foreign_history_incomplete: 'Chưa đủ 20 phiên khối ngoại', foreign_values_invalid: 'Dữ liệu khối ngoại không hợp lệ',
  invalid_ohlcv: 'Giá/khối lượng không hợp lệ', synthetic_or_flagged_bar: 'Nến có dữ liệu thay thế',
}
const fmt = value => value == null ? '—' : Number(value).toLocaleString('vi-VN', { maximumFractionDigits: 3 })
const day = value => value ? value.split('-').reverse().join('/') : 'chưa xác định'

export function ScreenerResults({ data, loading, error, preset, page, onNext, onPrevious, onRefresh }) {
  const pack = data?.catalog?.find(p => p.id === preset) || PRESET_PACKS.find(p => p.id === preset)
  return <section className="quant-screen" aria-label="Kết quả bộ lọc định lượng" aria-busy={loading}>
    <div className="quant-screen__summary" role="status">
      <strong>{pack?.label || 'Bộ lọc toàn thị trường'}</strong>
      {loading ? <span>Đang đánh giá điều kiện…</span> : error ? <span role="alert">{error}</span> : data && <>
        <span>{data.evaluated} mã đã đánh giá / {data.scope_total} mã trong phạm vi</span>
        <span className="quant-screen__matches">{data.matched} mã đạt</span>
        <span>{data.unknown} thiếu dữ liệu · {data.stale} dữ liệu cũ · {data.not_eligible} chưa đủ điều kiện</span>
      </>}
      <button type="button" onClick={onRefresh} disabled={loading}>Tải lại</button>
    </div>
    {data && <div className="quant-screen__context">
      <span>Tín hiệu cuối ngày · {data.session_verified ? `Phiên ${day(data.as_of)}` : 'Chưa xác nhận phiên dữ liệu'}</span>
      {data.freshness === 'stale' && <span>Dữ liệu chốt cần cập nhật</span>}
      <span>Điểm là xếp hạng theo tiêu chí, không phải xác suất tăng giá.</span>
    </div>}
    {pack && <details className="quant-screen__method"><summary>Xem điều kiện{pack.experimental ? ' · Thử nghiệm' : ''}</summary>
      <p>{pack.description || pack.desc}</p>
      <p>Ngưỡng thanh khoản: trung vị giá trị khớp 20 phiên trước ≥5 tỷ đồng, giao dịch ít nhất 18/20 phiên. Các ngưỡng chưa được xác nhận hiệu quả đầu tư bằng backtest.</p>
    </details>}
    {data && Object.keys(data.missing_reasons || {}).length > 0 && <details className="quant-screen__missing"><summary>Vì sao một số mã chưa được đánh giá?</summary>
      <ul>{Object.entries(data.missing_reasons).map(([code, count]) => <li key={code}>{REASONS[code] || 'Dữ liệu cần bổ sung'}: {count} mã</li>)}</ul>
      {data.collection?.status === 'provider_unavailable' && <p>Nguồn hiện tại chưa cung cấp đủ lịch sử chuẩn hóa. Kết quả sẽ được tính khi dữ liệu được bổ sung.</p>}
    </details>}
    {data?.matched > 0 && <nav className="quant-screen__pagination" aria-label="Phân trang tín hiệu">
      <span>Hiển thị {data.offset + 1}–{data.offset + data.returned} / {data.matched} mã</span>
      <button type="button" onClick={onPrevious} disabled={page <= 1 || loading}>Trước</button>
      <span>Trang {page}</span><button type="button" onClick={onNext} disabled={!data.next_cursor || loading}>Tiếp</button>
    </nav>}
  </section>
}

export function StockSignalDetails({ signal }) {
  if (!signal?.conditions) return null
  return <details className="quant-signal" onClick={event => event.stopPropagation()} onKeyDown={event => event.stopPropagation()}>
    <summary>{signal.score == null ? 'Chưa đủ mẫu xếp hạng' : `${fmt(signal.score)}/100`} <span>Chi tiết</span></summary>
    <div className="quant-signal__content">
      <small>Chốt phiên {day(signal.as_of)} · {signal.source || 'Nguồn chưa xác định'}</small>
      {Object.entries(signal.signals || {}).map(([id, item]) => <div key={id}>
        <strong>{PRESET_PACKS.find(p => p.id === id)?.label || 'Chỉ báo kỹ thuật'}</strong>
        <ul>{item.conditions.map(c => <li key={c.id} className={c.passed ? 'is-pass' : 'is-missing'}>
          <span>{c.passed === null ? 'Thiếu dữ liệu' : c.passed ? 'Đạt' : 'Chưa đạt'} — {c.label}</span>
          <small>{Object.values(c.values).map(fmt).join(' · ')}</small>
        </li>)}</ul>
      </div>)}
      <small>Điểm thể hiện mức độ nổi bật của tín hiệu. {signal.formula_version}</small>
    </div>
  </details>
}
