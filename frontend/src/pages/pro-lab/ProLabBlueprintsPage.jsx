export default function ProLabBlueprintsPage({
  form,
  setForm,
  selectedBlueprintId,
  setSelectedBlueprintId,
  compareRightId,
  setCompareRightId,
  compareResult,
  workspace,
  onSaveBlueprint,
  onUpdateBlueprint,
  onArchiveBlueprint,
  onCompareBlueprints,
}) {
  if (!workspace) {
    return <p className="text-xs text-[#88aab8]">Mở workspace Pro để chỉnh blueprint.</p>
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-6 items-start">
      <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4 lg:col-span-2">
        <div className="flex justify-between items-start gap-4 flex-wrap pb-2">
          <div>
            <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Blueprint Checklist</p>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider mt-1">Trước khi chạy Lab, cần rõ 4 thứ</h2>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#4fd1b4]/10 text-[#4fd1b4] border border-[#4fd1b4]/20">{selectedBlueprintId ? 'Editing saved blueprint' : 'New blueprint'}</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-2">
          <article className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-1">
            <strong className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">Thesis</strong>
            <span className="text-xs text-[#88aab8] leading-relaxed">Chiến lược đang kiểm tra điều gì?</span>
          </article>
          <article className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-1">
            <strong className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">Universe</strong>
            <span className="text-xs text-[#88aab8] leading-relaxed">Những mã/tài sản nào được phép vào sandbox?</span>
          </article>
          <article className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-1">
            <strong className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">Benchmark</strong>
            <span className="text-xs text-[#88aab8] leading-relaxed">So với chuẩn nào để không tự đánh giá cảm tính?</span>
          </article>
          <article className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-1">
            <strong className="text-xs font-bold text-[#4fd1b4] uppercase tracking-wider">Risk constraint</strong>
            <span className="text-xs text-[#88aab8] leading-relaxed">Điều kiện nào khiến strategy bị loại?</span>
          </article>
        </div>
      </section>

      <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
        <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Strategy Blueprint</p>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Blueprint editor</h2>
        <p className="text-xs text-[#88aab8]">Định nghĩa thesis, universe, benchmark và constraint trước khi chạy bất kỳ experiment nào.</p>
        
        <div className="grid gap-4 mt-2">
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Name
            <input className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition mt-1" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
          </label>
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Objective
            <textarea className="w-full p-3 rounded-xl border border-[#88aab8]/20 bg-[#0c1720]/80 text-[#edf7f5] text-xs outline-none focus:border-[#4fd1b4] transition leading-relaxed resize-none mt-1" rows={3} value={form.objective} onChange={(event) => setForm((current) => ({ ...current, objective: event.target.value }))} />
          </label>
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Universe
            <input className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition mt-1" value={form.asset_universe} onChange={(event) => setForm((current) => ({ ...current, asset_universe: event.target.value }))} />
          </label>
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Benchmark
            <input className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition mt-1" value={form.benchmark} onChange={(event) => setForm((current) => ({ ...current, benchmark: event.target.value }))} />
          </label>
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Rebalance
            <input
              className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition mt-1"
              value={form.rebalance_frequency}
              onChange={(event) => setForm((current) => ({ ...current, rebalance_frequency: event.target.value }))}
            />
          </label>
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Risk constraints
            <textarea
              className="w-full p-3 rounded-xl border border-[#88aab8]/20 bg-[#0c1720]/80 text-[#edf7f5] text-xs outline-none focus:border-[#4fd1b4] transition leading-relaxed resize-none mt-1"
              rows={3}
              value={form.risk_constraints}
              onChange={(event) => setForm((current) => ({ ...current, risk_constraints: event.target.value }))}
            />
          </label>
          <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
            Assumptions
            <textarea
              className="w-full p-3 rounded-xl border border-[#88aab8]/20 bg-[#0c1720]/80 text-[#edf7f5] text-xs outline-none focus:border-[#4fd1b4] transition leading-relaxed resize-none mt-1"
              rows={3}
              value={form.assumptions_note}
              onChange={(event) => setForm((current) => ({ ...current, assumptions_note: event.target.value }))}
            />
          </label>
        </div>
        <div className="flex gap-2 flex-wrap pt-2">
          <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016]" type="button" onClick={onSaveBlueprint}>Lưu mới</button>
          <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#3b82f6] hover:bg-[#60a5fa] text-white disabled:opacity-50 disabled:pointer-events-none" type="button" onClick={() => onUpdateBlueprint(selectedBlueprintId, form)} disabled={!selectedBlueprintId}>Cập nhật</button>
          <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-transparent border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 disabled:opacity-50 disabled:pointer-events-none" type="button" onClick={() => onArchiveBlueprint(selectedBlueprintId)} disabled={!selectedBlueprintId}>Archive</button>
        </div>
      </section>

      <aside className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4">
        <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Saved</p>
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">Blueprints</h3>
        {workspace.blueprints.length ? (
          <div className="flex flex-col gap-3">
            {workspace.blueprints.map((item) => (
              <article
                key={item.blueprint_id}
                className={`p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2 ${item.blueprint_id === selectedBlueprintId ? 'border-[#4fd1b4]/40 bg-[#101d26]/80' : ''}`}
              >
                <button
                  className="text-left text-xs font-bold text-[#4fd1b4] hover:underline cursor-pointer border-none bg-transparent p-0"
                  type="button"
                  onClick={() => {
                    setSelectedBlueprintId(item.blueprint_id)
                    setForm({
                      name: item.name,
                      objective: item.objective,
                      asset_universe: item.asset_universe.join(','),
                      benchmark: item.benchmark,
                      rebalance_frequency: item.rebalance_frequency,
                      risk_constraints: item.risk_constraints,
                      assumptions_note: item.assumptions_note || '',
                    })
                  }}
                >
                  {item.name}
                </button>
                <p className="text-xs text-[#88aab8] leading-relaxed">{item.objective}</p>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">{item.benchmark}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">{item.rebalance_frequency}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0c1720]/80 border border-[#88aab8]/15 text-[#edf7f5]">{item.status}</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-xs text-[#88aab8]">Chưa có blueprint nào. Bắt đầu bằng strategy blueprint trước.</p>
        )}
      </aside>

      <section className="p-5 rounded-2xl bg-[#101d26]/60 border border-[#88aab8]/15 shadow-md flex flex-col gap-4 lg:col-span-2">
        <p className="text-[9px] font-bold text-[#5e7a72] uppercase tracking-wider">Review</p>
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">Blueprint Compare</h3>
        <label className="flex flex-col gap-1 text-[10px] font-bold text-[#5e7a72] uppercase tracking-wider">
          Blueprint bên phải
          <select className="w-full bg-[#0c1720]/80 border border-[#88aab8]/20 text-[#edf7f5] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#4fd1b4] transition mt-1" value={compareRightId} onChange={(event) => setCompareRightId(event.target.value)}>
            <option value="">Chọn blueprint để compare</option>
            {workspace.blueprints
              .filter((item) => item.blueprint_id !== selectedBlueprintId)
              .map((item) => (
                <option key={item.blueprint_id} value={item.blueprint_id}>
                  {item.name}
                </option>
              ))}
          </select>
        </label>
        <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition active:scale-95 bg-[#4fd1b4] hover:bg-[#6ee0c8] text-[#071016] disabled:opacity-50 disabled:pointer-events-none self-start" type="button" onClick={onCompareBlueprints} disabled={!selectedBlueprintId || !compareRightId}>
          Compare blueprints
        </button>
        {compareResult ? (
          <article className="p-4 rounded-xl bg-[#0c1720]/40 border border-[#88aab8]/10 flex flex-col gap-2">
            <p className="text-xs text-[#88aab8] leading-relaxed">{compareResult.summary}</p>
            <div className="grid gap-2 border-t border-[#88aab8]/15 pt-2 mt-1">
              {compareResult.differences.map((item) => (
                <div key={item.field} className="flex justify-between items-center text-xs py-1 border-b border-[#88aab8]/5">
                  <strong className="text-[#edf7f5]">{item.field}</strong>
                  <span className="text-rose-400 font-semibold">{item.left}</span>
                  <span className="text-emerald-400 font-semibold">{item.right}</span>
                </div>
              ))}
            </div>
          </article>
        ) : null}
      </section>
    </div>
  )
}
