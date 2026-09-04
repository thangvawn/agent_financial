import { NotePaper } from './NotePaper'
import { BookDocumentPane } from './BookDocumentPane'
import { NotePageStrip, NoteToolbar, ReaderPanelSwitch, ReaderTopBar } from './ReaderChrome'
import { ReaderSplitPane } from './ReaderSplitPane'
import { resolveBookSource } from './bookSource'
import { normalizeNoteImages } from './bookReaderModel'
import { useBookReaderState } from './useBookReaderState'
import './book-reader.css'

export function BookReaderWorkspace({ book, sessionId, onClose }) {
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
    <div className="br-shell">
      <ReaderTopBar
        title={book.title}
        savedAt={savedAt}
        onBack={closeAndPersist}
        onSave={saveReaderState}
        openUrl={source.openUrl}
      />
      <ReaderPanelSwitch panel={panel} onChange={setPanel} />

      <ReaderSplitPane
        panel={panel}
        book={<BookDocumentPane book={book} />}
        notes={(
          <>
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
    </div>
  )
}
