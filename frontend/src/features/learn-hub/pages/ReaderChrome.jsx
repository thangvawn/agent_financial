const MODES = [
  ['type', 'Gõ'],
  ['draw', 'Vẽ'],
  ['erase', 'Tẩy'],
]

export function ReaderTopBar({ title, savedAt, onBack, onSave, openUrl }) {
  return (
    <header className="br-top">
      <button type="button" className="br-top__back" onClick={onBack} aria-label="Quay lại thư viện">
        ← Thư viện
      </button>
      <div className="br-top__center">
        <p className="br-top__kicker">Đang đọc</p>
        <h1 className="br-top__title">{title}</h1>
      </div>
      <div className="br-top__actions">
        <span className="br-top__saved" aria-live="polite">
          {savedAt ? `Đã lưu · ${new Date(savedAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}` : 'Chưa lưu'}
        </span>
        {openUrl ? (
          <a className="br-btn br-btn--ghost" href={openUrl} target="_blank" rel="noreferrer">Nguồn</a>
        ) : null}
        <button type="button" className="br-btn br-btn--ghost" onClick={onSave}>Lưu</button>
        <button type="button" className="br-btn br-btn--solid" onClick={onBack}>Xong</button>
      </div>
    </header>
  )
}

export function ReaderPanelSwitch({ panel, onChange }) {
  return (
    <div className="br-switch" role="tablist" aria-label="Chế độ xem">
      <button type="button" role="tab" aria-selected={panel === 'book'} className={panel === 'book' ? 'is-on' : undefined} onClick={() => onChange('book')}>
        Sách
      </button>
      <button type="button" role="tab" aria-selected={panel === 'notes'} className={panel === 'notes' ? 'is-on' : undefined} onClick={() => onChange('notes')}>
        Ghi chú
      </button>
    </div>
  )
}

export function NoteToolbar({
  editorMode,
  drawColor,
  drawSize,
  eraserSize,
  onMode,
  onColor,
  onDrawSize,
  onEraserSize,
  onAddPage,
  onUpload,
  onClearDrawing,
}) {
  return (
    <div className="br-tools">
      <div className="br-tools__modes" role="group" aria-label="Công cụ ghi chú">
        {MODES.map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={editorMode === id ? 'is-on' : undefined}
            onClick={() => onMode(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {editorMode === 'draw' ? (
        <div className="br-tools__ink">
          <label className="br-tools__color">
            <span className="sr-only">Màu bút</span>
            <input type="color" value={drawColor} onChange={(e) => onColor(e.target.value)} />
          </label>
          <label className="br-tools__range">
            <span>Nét</span>
            <input type="range" min={1} max={12} step={0.5} value={drawSize} onChange={(e) => onDrawSize(Number(e.target.value))} />
          </label>
          <button type="button" className="br-btn br-btn--ghost" onClick={onClearDrawing}>Xóa nét</button>
        </div>
      ) : null}

      {editorMode === 'erase' ? (
        <label className="br-tools__range">
          <span>Tẩy</span>
          <input type="range" min={8} max={96} step={2} value={eraserSize} onChange={(e) => onEraserSize(Number(e.target.value))} />
        </label>
      ) : null}

      <div className="br-tools__actions">
        <button type="button" className="br-btn br-btn--ghost" onClick={onUpload}>Chèn ảnh</button>
        <button type="button" className="br-btn br-btn--ghost" onClick={onAddPage}>+ Trang</button>
      </div>
    </div>
  )
}

export function NotePageStrip({
  pages,
  activePageId,
  activeTitle,
  onSelect,
  onTitleChange,
}) {
  return (
    <div className="br-pages">
      <div className="br-pages__strip" role="tablist" aria-label="Trang ghi chú">
        {pages.map((page, index) => (
          <button
            key={page.id}
            type="button"
            role="tab"
            aria-selected={page.id === activePageId}
            className={page.id === activePageId ? 'is-on' : undefined}
            onClick={() => onSelect(page.id)}
          >
            {index + 1}
          </button>
        ))}
      </div>
      <input
        className="br-pages__title"
        value={activeTitle || ''}
        onChange={(e) => onTitleChange(e.target.value)}
        placeholder="Đặt tên trang ghi chú…"
        aria-label="Tên trang ghi chú"
      />
    </div>
  )
}
