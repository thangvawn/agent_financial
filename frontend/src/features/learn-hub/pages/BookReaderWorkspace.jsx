import { NotePaper } from './NotePaper'
import { BookDocumentPane } from './BookDocumentPane'
import { NotePageStrip, NoteToolbar, ReaderPanelSwitch, ReaderTopBar } from './ReaderChrome'
import { ReaderSplitPane } from './ReaderSplitPane'
import { resolveBookSource } from './bookSource'
import { normalizeNoteImages } from './bookReaderModel'
import { useBookReaderState } from './useBookReaderState'
import './book-reader.css'
import {useCallback,useRef,useState} from 'react'
import ReaderLibraryTools from './ReaderLibraryTools'
import {NotebookPen} from 'lucide-react'
import './reader-studio.css'

export function BookReaderWorkspace({ book, sessionId, onClose, library }) {
  const [depthEnabled,setDepthEnabled]=useState(()=>{try{return localStorage.getItem('learn-reader:depth')!=='off'}catch{return true}})
  function toggleDepth(){setDepthEnabled(current=>{const next=!current;try{localStorage.setItem('learn-reader:depth',next?'on':'off')}catch{ /* Rendering remains usable without storage. */ }return next})}
  const [readingBook]=useState(book)
  const [initialPage]=useState(book.libraryItem?.current_page || 1)
  const [eventId]=useState(()=>crypto.randomUUID())
  const [libraryItem,setLibraryItem]=useState(book.libraryItem || null)
  const [historyBusy,setHistoryBusy]=useState(false)
  const [historyError,setHistoryError]=useState('')
  const recorded=useRef(false)
  const recordOpen=library?.recordOpen
  const onDocumentReady=useCallback(()=>{
    if(!recordOpen || recorded.current)return
    recorded.current=true;setHistoryBusy(true);setHistoryError('')
    recordOpen(readingBook,eventId).then(setLibraryItem).catch(error=>setHistoryError(error.message)).finally(()=>setHistoryBusy(false))
  },[recordOpen,readingBook,eventId])
  const {
    pages,
    resolvedActivePageId,
    activePage,
    visiblePageBadgeId,
    savedAt,
    editorMode,
    setEditorMode,
    drawColor,
    setDrawColor,
    drawSize,
    setDrawSize,
    eraserSize,
    setEraserSize,
    panel,
    setPanel,
    updatePageById,
    pasteImagesFromClipboard,
    handleImageUpload,
    handleSelectPage,
    handleAddPage,
    saveReaderState,
    setActivePageId,
    setPageElementRef,
    triggerUpload,
    uploadInputRef,
  } = useBookReaderState({ book, sessionId })

  const source = resolveBookSource(book)

  function closeAndPersist() {
    saveReaderState()
    onClose()
  }

  return (
    <div className="br-shell br-studio" data-depth={depthEnabled?'on':'off'}>
      <ReaderTopBar
        title={book.title}
        author={book.author}
        depthEnabled={depthEnabled}
        onToggleDepth={toggleDepth}
        savedAt={savedAt}
        onBack={closeAndPersist}
        onSave={saveReaderState}
        openUrl={source.openUrl}
      />
      <div className="br-workspace-bar">
        {library && <ReaderLibraryTools item={libraryItem} book={book} busy={historyBusy} error={historyError} onRetry={()=>{recorded.current=false;onDocumentReady()}} onUpdate={async(id,patch)=>setLibraryItem(await library.update(id,patch))}/>}
        <ReaderPanelSwitch panel={panel} onChange={setPanel} />
      </div>

      <ReaderSplitPane
        panel={panel}
        book={<BookDocumentPane book={book} onReady={onDocumentReady} initialPage={initialPage} />}
        notes={(
          <>
          <div className="br-notebook-heading"><div><NotebookPen size={17}/><h2>Sổ ghi chú</h2></div><span>{pages.length} trang</span></div>
          <NoteToolbar
            editorMode={editorMode}
            drawColor={drawColor}
            drawSize={drawSize}
            eraserSize={eraserSize}
            onMode={setEditorMode}
            onColor={setDrawColor}
            onDrawSize={setDrawSize}
            onEraserSize={setEraserSize}
            onAddPage={handleAddPage}
            onUpload={triggerUpload}
            onClearDrawing={() => updatePageById(resolvedActivePageId, { drawingDataUrl: '' })}
          />
          <NotePageStrip
            pages={pages}
            activePageId={resolvedActivePageId}
            activeTitle={activePage?.title || ''}
            onSelect={handleSelectPage}
            onTitleChange={(title) => updatePageById(resolvedActivePageId, { title })}
          />
          <input
            ref={uploadInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleImageUpload}
            className="br-hidden"
          />

          <div className="br-notes__scroll">
            {pages.map((page, index) => (
              <NotePaper
                key={page.id}
                page={page}
                pageIndex={index}
                isActive={page.id === resolvedActivePageId}
                showPageLabel={page.id === visiblePageBadgeId}
                editorMode={editorMode}
                drawColor={drawColor}
                drawSize={drawSize}
                eraserSize={eraserSize}
                setPageRef={(node) => setPageElementRef(page.id, node)}
                onActivate={() => setActivePageId(page.id)}
                onTextChange={(noteText) => updatePageById(page.id, { noteText })}
                onDrawingChange={(drawingDataUrl) => updatePageById(page.id, { drawingDataUrl })}
                onImageChange={(imageIndex, patch) => updatePageById(page.id, (pageItem) => ({
                  images: normalizeNoteImages(pageItem.images).map((image, idx) => (
                    idx === imageIndex ? { ...image, ...patch } : image
                  )),
                }))}
                onImageRemove={(imageIndex) => updatePageById(page.id, (pageItem) => ({
                  images: normalizeNoteImages(pageItem.images).filter((_, idx) => idx !== imageIndex),
                }))}
                onPaste={(event) => pasteImagesFromClipboard(event, page.id)}
                onTypeMode={() => setEditorMode('type')}
              />
            ))}
            <button type="button" className="br-notes__add" onClick={handleAddPage}>
              + Thêm trang ghi chú
            </button>
          </div>
          </>
        )}
      />
      <footer className="br-workspace-footer"><span>Tài liệu & ghi chú cá nhân</span><span className="br-split-hint">Kéo thanh giữa để điều chỉnh · Nhấp đúp để cân lại</span></footer>
    </div>
  )
}
