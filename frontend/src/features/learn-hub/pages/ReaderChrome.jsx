import ThemeToggle from '../../../shared/theme/ThemeToggle'
import {ArrowLeft,BookOpen,Box,Check,Columns2,Eraser,ExternalLink,ImagePlus,NotebookPen,PenLine,Plus,Save,Type} from 'lucide-react'
import ReaderDeskScene from './ReaderDeskScene'
import {useEffect,useRef} from 'react'

const MODES = [['type','Gõ',Type],['draw','Vẽ',PenLine],['erase','Tẩy',Eraser]]

export function ReaderTopBar({ title, author, savedAt, onBack, onSave, openUrl, depthEnabled=true, onToggleDepth }) {
  return (
    <header className="br-top">
      <button type="button" className="br-top__back" onClick={onBack} aria-label="Quay lại thư viện">
        <ArrowLeft size={16}/><span>Thư viện</span>
      </button>
      <div className="br-top__center">
        <ReaderDeskScene enabled={depthEnabled}/>
        <div className="br-top__book-info">
        <h1 className="br-top__title" title={[title,author].filter(Boolean).join(' — ')}>{title}</h1>
        {author && <p className="br-top__author">{author}</p>}</div>
      </div>
      <div className="br-top__actions">
        <ThemeToggle />
        <span className="br-top__saved" aria-live="polite">
          {savedAt && <Check size={13}/>} {savedAt ? `Đã lưu · ${new Date(savedAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}` : 'Ghi chú chưa lưu'}
        </span>
        {openUrl ? (
          <a className="br-btn br-btn--ghost br-top__source" href={openUrl} target="_blank" rel="noreferrer"><ExternalLink size={14}/>Nguồn</a>
        ) : null}
        <button type="button" className="br-btn br-depth-toggle" aria-label="Hiệu ứng 3D" aria-pressed={depthEnabled} title="Bật hoặc tắt chiều sâu 3D" onClick={onToggleDepth}><Box size={16}/><span>3D</span></button>
        <button type="button" className="br-btn br-btn--solid" onClick={onSave} title="Lưu ghi chú"><Save size={14}/>Lưu</button>
        <button type="button" className="br-btn br-btn--ghost" onClick={onBack}>Xong</button>
      </div>
    </header>
  )
}

export function ReaderPanelSwitch({ panel, onChange }) {
  return (
    <div className="br-switch" role="tablist" aria-label="Chế độ xem">
      <button type="button" role="tab" aria-selected={panel === 'book'} className={panel === 'book' ? 'is-on' : undefined} onClick={() => onChange('book')}>
        <BookOpen size={14}/>Sách
      </button>
      <button type="button" role="tab" aria-selected={panel === 'split'} className={`br-switch__split ${panel === 'split' ? 'is-on' : ''}`} onClick={() => onChange('split')}><Columns2 size={14}/>Song song</button>
      <button type="button" role="tab" aria-selected={panel === 'notes'} className={panel === 'notes' ? 'is-on' : undefined} onClick={() => onChange('notes')}>
        <NotebookPen size={14}/>Ghi chú
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
        {MODES.map((mode) => {
          const [id,label,Icon]=mode
          return (
          <button
            key={id}
            type="button"
            aria-pressed={editorMode === id}
            className={editorMode === id ? 'is-on' : undefined}
            onClick={() => onMode(id)}
          >
            <Icon size={14}/>{label}
          </button>
          )
        })}
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
        <button type="button" className="br-btn br-btn--ghost" onClick={onUpload} aria-label="Chèn ảnh" title="Chèn ảnh vào ghi chú"><ImagePlus size={16}/></button>
        <button type="button" className="br-btn br-btn--ghost" onClick={onAddPage} aria-label="Trang" title="Thêm trang ghi chú"><Plus size={18}/></button>
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
  meta,
}) {
  const stripRef = useRef(null)
  useEffect(() => {
    const strip = stripRef.current
    const active = strip?.querySelector('[aria-selected="true"]')
    if (!active) return
    const bounds = strip.getBoundingClientRect()
    const tab = active.getBoundingClientRect()
    if (tab.left < bounds.left) strip.scrollLeft += tab.left - bounds.left
    else if (tab.right > bounds.right) strip.scrollLeft += tab.right - bounds.right
  }, [activePageId, pages.length])
  return (
    <div className="br-pages">
      <div ref={stripRef} className="br-pages__strip" role="tablist" aria-label="Trang ghi chú">
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
      {meta}
    </div>
  )
}
