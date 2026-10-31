import { useState } from 'react'
import { compileStrategy } from '../../utils/quantaStrategy'
import { extractQuantaParams, updateQuantaParamInCode } from '../../utils/quantaParamParser'

export default function SimLabAiCopilotModal({ code, bars = [], metrics, onClose, onApplyOptimizedCode }) {
  const [error, setError] = useState('')
  let validation = ''
  try {
    const strategy = compileStrategy(code, bars)
    validation = bars.length > strategy.warmup ? `Cú pháp chạy được trên ${bars.length} nến; cần ${strategy.warmup + 1} nến để khởi tạo.` : `Cần ít nhất ${strategy.warmup + 1} nến lịch sử.`
  } catch (reason) { validation = reason.message }
  const trendParams = extractQuantaParams(code).filter(p => ['fast_len','slow_len','fast_period','slow_period'].includes(p.name))
  function applyExample() {
    try {
      let candidate = code
      for (const p of trendParams) candidate = updateQuantaParamInCode(candidate,p.name,Math.min(p.max,Math.max(p.min,Math.round(p.value*1.2))))
      compileStrategy(candidate,bars)
      onApplyOptimizedCode(candidate)
    } catch (reason) { setError(reason.message) }
  }
  return <div className="simlab-modal-backdrop" onClick={onClose}>
    <section className="simlab-copilot-modal" role="dialog" aria-modal="true" aria-labelledby="copilot-title" onClick={e=>e.stopPropagation()}>
      <div className="modal-header"><h3 id="copilot-title">AI Quant Copilot & Chiến Lược Cố Vấn</h3><button type="button" aria-label="Đóng trợ lý" onClick={onClose}>✕</button></div>
      <div className="modal-body">
        <p>Chế độ kiểm tra quy tắc cục bộ. Chưa kết nối phân tích AI; các thay đổi dưới đây là thử nghiệm tham số, chưa được xác nhận là tối ưu.</p>
        <p role="status">{validation}</p>
        {metrics && <p>Kết quả hiện tại: {metrics.total_trades} giao dịch đã đóng; lợi nhuận {metrics.total_return.toFixed(2)}%; Sharpe {metrics.sharpe == null ? 'chưa xác định' : metrics.sharpe.toFixed(2)}.</p>}
        {trendParams.length > 0 && <><p>Thử tăng chu kỳ EMA đang khai báo thêm khoảng 20%, trong giới hạn tham số. Chạy lại để so sánh tác động.</p><button type="button" className="apply-suggestion-btn" onClick={applyExample}>Áp dụng thử chu kỳ dài hơn</button></>}
        {error && <p role="alert">{error}</p>}
      </div>
    </section>
  </div>
}
