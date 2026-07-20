import { useCallback, useEffect, useState } from 'react'

import { fetchMpPortfolio, resetMpPortfolio } from '../services/marketPortfolioApi'
import { formatVnd } from './formatMoney'
import './market-portfolio-panels.css'

export default function PortfolioPanel({ sessionId }) {
  const [portfolio, setPortfolio] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = useCallback(async () => {
    const data = await fetchMpPortfolio(sessionId)
    setPortfolio(data)
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

  async function onReset() {
    if (!window.confirm('Đặt lại danh mục mô phỏng về số dư ban đầu 100 triệu VND? Toàn bộ vị thế hiện tại sẽ bị xóa.')) return
    setBusy(true)
    setError('')
    try {
      setPortfolio(await resetMpPortfolio(sessionId))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const pnlClass = (portfolio?.total_pnl || 0) >= 0 ? 'is-pos' : 'is-neg'

  return (
    <section className="mp-panel">
      <header className="mp-panel__head">
        <div>
          <h2>Danh mục mô phỏng và lỗ/lãi</h2>
          <p>{portfolio?.disclaimer || 'Danh mục giấy phục vụ giáo dục, không dùng tiền thật.'}</p>
        </div>
        <button type="button" onClick={onReset} disabled={busy}>
          {busy ? 'Đang đặt lại…' : 'Đặt lại danh mục'}
        </button>
      </header>
      {error ? <p className="mp-error" role="alert">{error}. Hãy thử tải lại danh mục.</p> : null}
      {portfolio ? (
        <>
          <div className="mp-kpi">
            <div>
              <span>Tiền mặt</span>
              <strong className="num">{formatVnd(portfolio.cash_balance)}</strong>
            </div>
            <div>
              <span>Tổng tài sản</span>
              <strong className="num">{formatVnd(portfolio.equity)}</strong>
            </div>
            <div>
              <span>Lỗ/lãi chưa chốt</span>
              <strong className={`num ${pnlClass}`}>{formatVnd(portfolio.unrealized_pnl)}</strong>
            </div>
            <div>
              <span>Tổng lỗ/lãi</span>
              <strong className={`num ${pnlClass}`}>
                {formatVnd(portfolio.total_pnl)} ({portfolio.total_pnl_pct}%)
              </strong>
            </div>
          </div>
          <div className="mp-table-wrap">
            <table className="mp-table">
              <caption className="sr-only">Các vị thế trong danh mục mô phỏng</caption>
              <thead>
                <tr>
                  <th>Mã</th>
                  <th>Số lượng</th>
                  <th>Giá vốn</th>
                  <th>Giá hiện tại</th>
                  <th>Giá trị</th>
                  <th>Lỗ/lãi chưa chốt</th>
                </tr>
              </thead>
              <tbody>
                {(portfolio.positions || []).map((pos) => (
                  <tr key={pos.symbol}>
                    <td>{pos.symbol}</td>
                    <td className="num">{pos.quantity}</td>
                    <td className="num">{formatVnd(pos.avg_cost)}</td>
                    <td className="num">{formatVnd(pos.mark_price)}</td>
                    <td className="num">{formatVnd(pos.market_value)}</td>
                    <td className={`num ${(pos.unrealized_pnl || 0) >= 0 ? 'is-pos' : 'is-neg'}`}>
                      {formatVnd(pos.unrealized_pnl)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!portfolio.positions?.length ? <p className="mp-empty">Chưa có vị thế. Sang mục “Luyện đặt lệnh” và thử một lệnh mua nhỏ.</p> : null}
          </div>
        </>
      ) : null}
    </section>
  )
}
