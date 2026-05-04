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
    return <p className="pro-lab-state">Mở workspace Pro để chỉnh blueprint.</p>
  }

  return (
    <section className="pro-lab-section pro-lab-blueprint-layout">
      <section className="pro-lab-card pro-lab-card--span">
        <div className="pro-lab-section-heading">
          <div>
            <p className="pro-lab-eyebrow">Blueprint Checklist</p>
            <h2>Trước khi chạy Lab, cần rõ 4 thứ</h2>
          </div>
          <span className="pro-lab-badge">{selectedBlueprintId ? 'Editing saved blueprint' : 'New blueprint'}</span>
        </div>
        <div className="pro-lab-checklist-grid">
          <article><strong>Thesis</strong><span>Chiến lược đang kiểm tra điều gì?</span></article>
          <article><strong>Universe</strong><span>Những mã/tài sản nào được phép vào sandbox?</span></article>
          <article><strong>Benchmark</strong><span>So với chuẩn nào để không tự đánh giá cảm tính?</span></article>
          <article><strong>Risk constraint</strong><span>Điều kiện nào khiến strategy bị loại?</span></article>
        </div>
      </section>

      <section className="pro-lab-card pro-lab-blueprint-editor">
        <p className="pro-lab-eyebrow">Strategy Blueprint</p>
        <h2>Blueprint editor</h2>
        <p>Định nghĩa thesis, universe, benchmark và constraint trước khi chạy bất kỳ experiment nào.</p>
        <label>
          Name
          <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
        </label>
        <label>
          Objective
          <textarea value={form.objective} onChange={(event) => setForm((current) => ({ ...current, objective: event.target.value }))} />
        </label>
        <label>
          Universe
          <input value={form.asset_universe} onChange={(event) => setForm((current) => ({ ...current, asset_universe: event.target.value }))} />
        </label>
        <label>
          Benchmark
          <input value={form.benchmark} onChange={(event) => setForm((current) => ({ ...current, benchmark: event.target.value }))} />
        </label>
        <label>
          Rebalance
          <input
            value={form.rebalance_frequency}
            onChange={(event) => setForm((current) => ({ ...current, rebalance_frequency: event.target.value }))}
          />
        </label>
        <label>
          Risk constraints
          <textarea
            value={form.risk_constraints}
            onChange={(event) => setForm((current) => ({ ...current, risk_constraints: event.target.value }))}
          />
        </label>
        <label>
          Assumptions
          <textarea
            value={form.assumptions_note}
            onChange={(event) => setForm((current) => ({ ...current, assumptions_note: event.target.value }))}
          />
        </label>
        <div className="pro-lab-actions-row">
          <button type="button" onClick={onSaveBlueprint}>Lưu mới</button>
          <button type="button" onClick={onUpdateBlueprint} disabled={!selectedBlueprintId}>Cập nhật</button>
          <button type="button" onClick={onArchiveBlueprint} disabled={!selectedBlueprintId}>Archive</button>
        </div>
      </section>

      <aside className="pro-lab-card">
        <p className="pro-lab-eyebrow">Saved</p>
        <h3>Blueprints</h3>
        {workspace.blueprints.length ? (
          <div className="pro-lab-stack">
            {workspace.blueprints.map((item) => (
              <article
                key={item.blueprint_id}
                className={item.blueprint_id === selectedBlueprintId ? 'pro-lab-mini-card pro-lab-mini-card--active' : 'pro-lab-mini-card'}
              >
                <button
                  className="pro-lab-link-button"
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
                <p>{item.objective}</p>
                <div className="pro-lab-badges">
                  <span className="pro-lab-badge">{item.benchmark}</span>
                  <span className="pro-lab-badge">{item.rebalance_frequency}</span>
                  <span className="pro-lab-badge">{item.status}</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p>Chưa có blueprint nào. Bắt đầu bằng strategy blueprint trước.</p>
        )}
      </aside>

      <section className="pro-lab-card pro-lab-card--span">
        <p className="pro-lab-eyebrow">Review</p>
        <h3>Blueprint Compare</h3>
        <label>
          Blueprint bên phải
          <select value={compareRightId} onChange={(event) => setCompareRightId(event.target.value)}>
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
        <button type="button" onClick={onCompareBlueprints} disabled={!selectedBlueprintId || !compareRightId}>
          Compare blueprints
        </button>
        {compareResult ? (
          <article className="pro-lab-mini-card">
            <p>{compareResult.summary}</p>
            <div className="pro-lab-compare-grid">
              {compareResult.differences.map((item) => (
                <div key={item.field}>
                  <strong>{item.field}</strong>
                  <span>{item.left}</span>
                  <span>{item.right}</span>
                </div>
              ))}
            </div>
          </article>
        ) : null}
      </section>
    </section>
  )
}
