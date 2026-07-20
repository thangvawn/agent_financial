export default function SimLabAnalyticsPage({ lastRun, workspace, onOpenReplay }) {
  const metrics = extractMetrics(lastRun?.payload)

  return (
    <div className="grid gap-6">
      <section>
        <p className="text-xs font-bold text-[#7fb3a7]">Đọc kết quả</p>
        <h2 className="text-lg font-bold text-white mt-1">Đánh giá hiệu quả và rủi ro</h2>
        <p className="text-sm text-[#a6c1c8] mt-2 max-w-2xl leading-relaxed">
          Không nhìn lợi nhuận riêng lẻ. Hãy đọc tỷ lệ thắng cùng mức sụt giảm để hiểu cái giá của chiến lược.
        </p>
      </section>

      {!lastRun ? (
        <section className="p-5 rounded-2xl border border-[#88aab8]/15 bg-[#101d26]/60 flex flex-col gap-3">
          <p className="text-sm text-[#a6c1c8]">Chưa có dữ liệu để phân tích. Hãy chạy lại một giai đoạn thị trường trước.</p>
          <button type="button" className="self-start px-4 py-2 rounded-lg text-sm font-bold bg-[#4fd1b4] text-[#071016] cursor-pointer" onClick={onOpenReplay}>
            Bắt đầu tua lại thị trường
          </button>
        </section>
      ) : (
        <section className="p-5 rounded-2xl border border-[#88aab8]/15 bg-[#101d26]/60 grid gap-4">
          <div className="flex flex-wrap justify-between gap-2">
            <div>
              <p className="text-xs font-bold text-[#7fb3a7]">Lần chạy gần nhất</p>
              <h3 className="text-sm font-bold text-white mt-1">{lastRun.label || lastRun.type}</h3>
              {lastRun.start && lastRun.end ? (
                <p className="text-xs text-[#88aab8] mt-1">{lastRun.start} → {lastRun.end}</p>
              ) : null}
            </div>
            <button type="button" className="text-sm font-semibold text-[#4fd1b4] bg-transparent border-0 cursor-pointer" onClick={onOpenReplay}>
              Mở lại phần tua dữ liệu
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <MetricCard label="Tỷ lệ thắng" value={formatPct(metrics.winRatePct)} help="Tỷ lệ giao dịch có lãi, không phản ánh mức lãi hoặc lỗ mỗi lần." />
            <MetricCard label="Sụt giảm lớn nhất" value={formatPct(metrics.maxDrawdownPct)} tone="down" help="Mức giảm sâu nhất từ đỉnh đến đáy trong giai đoạn thử nghiệm." />
            <MetricCard label="Tổng lợi nhuận" value={formatPct(metrics.totalReturnPct)} tone={metrics.totalReturnPct >= 0 ? 'up' : 'down'} help="Kết quả của giai đoạn đã chọn, chưa bảo đảm sẽ lặp lại." />
          </div>
        </section>
      )}

      <section className="p-5 rounded-2xl border border-[#88aab8]/15 bg-[#101d26]/60">
        <p className="text-xs font-bold text-[#7fb3a7]">Nhật ký thực hành</p>
        <p className="text-sm text-[#a6c1c8] mt-2">
          Đang có {workspace?.blueprints?.length || 0} chiến lược và {workspace?.experiments?.length || 0} lần thử nghiệm đã lưu.
        </p>
      </section>
    </div>
  )
}

function MetricCard({ label, value, help, tone = '' }) {
  const toneClass = tone === 'up' ? 'text-emerald-400' : tone === 'down' ? 'text-rose-400' : 'text-white'
  return (
    <article className="p-4 rounded-xl bg-[#0c1720]/50 border border-[#88aab8]/10">
      <h3 className="text-xs font-bold text-[#7fb3a7]">{label}</h3>
      <p className={`text-2xl font-extrabold mt-2 ${toneClass}`}>{value}</p>
      <p className="text-xs text-[#a6c1c8] mt-2 leading-relaxed">{help}</p>
    </article>
  )
}

function extractMetrics(payload) {
  const engine = payload?.output_payload || payload?.engine || payload || {}
  const metrics = engine.metrics || engine.strategy?.metrics || {}
  return {
    winRatePct: Number(metrics.win_rate_pct || metrics.winRatePct || 0),
    maxDrawdownPct: Number(metrics.max_drawdown_pct || metrics.maxDrawdownPct || 0),
    totalReturnPct: Number(metrics.total_return_pct || metrics.totalReturnPct || 0),
  }
}

function formatPct(value) {
  if (value == null || Number.isNaN(Number(value))) return '--'
  return `${Number(value).toFixed(2)}%`
}
