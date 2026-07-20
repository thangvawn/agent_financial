import { useCallback, useEffect, useState } from 'react'

import { cancelMpOrder, fetchMpOrders, placeMpOrder } from '../services/marketPortfolioApi'
import { formatVnd } from './formatMoney'
import './market-portfolio-panels.css'

export default function TradePanel({ sessionId }) {
  const [orders, setOrders] = useState([])
  const [form, setForm] = useState({ symbol: 'FPT', side: 'BUY', orderType: 'MP', quantity: 100, limitPrice: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = useCallback(async () => {
    const data = await fetchMpOrders(sessionId)
    setOrders(data.orders || [])
  }, [sessionId])

  useEffect(() => {
    let cancelled = false
    reload().catch((err) => {
      if (!cancelled) setError(err.message)
    })
    return () => {
      cancelled = true
    }
  }, [reload])

  async function onSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await placeMpOrder(sessionId, form)
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function onCancel(orderId) {
    setBusy(true)
    setError('')
    try {
      await cancelMpOrder(sessionId, orderId)
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mp-panel">
      <header className="mp-panel__head">
        <h2>Luyện đặt lệnh</h2>
        <p>MP mô phỏng khớp theo giá hiện tại. LO chỉ khớp khi giá đạt mức bạn đặt.</p>
      </header>
      <p className="edu-inline-note">
        <strong>Trước khi đặt:</strong> xác định lý do, số lượng và mức lỗ có thể chấp nhận. Đây là lệnh giấy, không dùng tiền thật.
      </p>
      <form className="mp-trade-form" onSubmit={onSubmit} aria-busy={busy} aria-label="Đặt lệnh giấy">
        <label>
          Mã cổ phiếu
          <input
            aria-label="Mã cổ phiếu"
            value={form.symbol}
            onChange={(e) => setForm((f) => ({ ...f, symbol: e.target.value.toUpperCase() }))}
            maxLength={12}
          />
        </label>
        <label>
          Hành động
          <select value={form.side} onChange={(e) => setForm((f) => ({ ...f, side: e.target.value }))}>
            <option value="BUY">Mua</option>
            <option value="SELL">Bán</option>
          </select>
        </label>
        <label>
          Loại lệnh
          <select value={form.orderType} onChange={(e) => setForm((f) => ({ ...f, orderType: e.target.value }))}>
            <option value="MP">MP - theo giá thị trường</option>
            <option value="LO">LO - có giá giới hạn</option>
          </select>
        </label>
        <label>
          Số lượng
          <input
            type="number"
            min="1"
            value={form.quantity}
            onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
          />
        </label>
        {form.orderType === 'LO' ? (
          <label>
            Giá giới hạn (VND)
            <input
              type="number"
              min="0"
              step="100"
              value={form.limitPrice}
              onChange={(e) => setForm((f) => ({ ...f, limitPrice: e.target.value }))}
            />
          </label>
        ) : null}
        <button type="submit" disabled={busy}>
          {busy ? 'Đang xử lý…' : 'Đặt lệnh giấy'}
        </button>
      </form>
      {error ? <p className="mp-error" role="alert">{error}. Hãy kiểm tra dữ liệu và thử lại.</p> : null}
      <div className="mp-table-wrap">
        <table className="mp-table">
          <caption className="sr-only">Lịch sử lệnh mô phỏng</caption>
          <thead>
            <tr>
              <th>Mã</th>
              <th>Hành động</th>
              <th>Loại</th>
              <th>Số lượng</th>
              <th>Trạng thái</th>
              <th>Giá khớp</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.order_id}>
                <td>{order.symbol}</td>
                <td>{order.side}</td>
                <td>{order.order_type}</td>
                <td className="num">{order.quantity}</td>
                <td>{order.status}</td>
                <td className="num">{formatVnd(order.filled_price)}</td>
                <td>
                  {order.status === 'OPEN' ? (
                    <button type="button" onClick={() => onCancel(order.order_id)} disabled={busy}>
                      Hủy
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!orders.length ? <p className="mp-empty">Chưa có lệnh. Bắt đầu với số lượng nhỏ để quan sát cách MP và LO hoạt động.</p> : null}
      </div>
    </section>
  )
}
