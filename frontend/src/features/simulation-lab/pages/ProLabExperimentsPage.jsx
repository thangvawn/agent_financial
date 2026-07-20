const HISTORICAL_SCENARIOS = [
  {
    id: 'gfc-2008',
    title: 'Khủng hoảng tài chính 2008',
    summary: 'Thử khả năng sinh tồn tài khoản qua giai đoạn sụp đổ toàn cầu 2007–2009.',
    start: '2007-10-01',
    end: '2009-03-31',
  },
  {
    id: 'covid-2020',
    title: 'Giai đoạn Covid 2020',
    summary: 'Shock thanh khoản và phục hồi nhanh đầu 2020 — kiểm tra kỷ luật cắt lỗ.',
    start: '2020-02-01',
    end: '2020-06-30',
  },
  {
    id: 'vn-correction-2022',
    title: 'Điều chỉnh thị trường VN 2022',
    summary: 'Giai đoạn thắt chặt và điều chỉnh mạnh — đo max drawdown thực tế của chiến lược.',
    start: '2022-01-01',
    end: '2022-12-31',
  },
]

export default function ProLabExperimentsPage({
  workspace,
  selectedBlueprintId,
  onScenarioRun,
  onOpenReplay,
}) {
  if (!workspace) {
    return <p className="text-sm text-[#a6c1c8]">Mở phòng mô phỏng và chọn chiến lược trước khi chạy kịch bản lịch sử.</p>
  }

  return (
    <div className="grid gap-6">
      <section>
        <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Historical Scenarios</p>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mt-1">Gói kịch bản có sẵn</h2>
        <p className="text-xs text-[#88aab8] mt-2 max-w-2xl">
          Chọn giai đoạn khủng hoảng / biến động lớn để chạy lại chiến lược đã dựng.
          Dữ liệu tương lai ngoài khoảng chọn không dùng để ra quyết định.
        </p>
        <p className="text-xs mt-3">
          {selectedBlueprintId
            ? <span className="text-[#4fd1b4]">Đang dùng chiến lược: {selectedBlueprintId}</span>
            : <span className="text-amber-400">Hãy chọn hoặc lưu một chiến lược ở tab Strategy Builder trước.</span>}
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {HISTORICAL_SCENARIOS.map((scenario) => (
          <article key={scenario.id} className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 flex flex-col gap-3 justify-between">
            <div className="flex flex-col gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20 self-start">
                {scenario.start} → {scenario.end}
              </span>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">{scenario.title}</h3>
              <p className="text-xs text-[#88aab8] leading-relaxed">{scenario.summary}</p>
            </div>
            <button
              type="button"
              className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] disabled:opacity-50"
              disabled={!selectedBlueprintId}
              onClick={() => onScenarioRun(selectedBlueprintId, scenario.start, scenario.end, scenario.title)}
            >
              Chạy kịch bản
            </button>
          </article>
        ))}
      </section>

      <section className="p-4 rounded-xl border border-[#88aab8]/15 bg-[#0c1720]/40 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-[#88aab8]">Muốn tự chọn mốc thời gian và tua bar-by-bar?</p>
        <button type="button" className="px-3.5 py-1.5 rounded-lg text-xs font-bold border border-[#4fd1b4]/40 text-[#4fd1b4] bg-transparent cursor-pointer" onClick={onOpenReplay}>
          Mở Time Skip / Bar Replay
        </button>
      </section>
    </div>
  )
}
