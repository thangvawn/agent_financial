import { NotePaper } from './NotePaper'
import { BookDocumentPane } from './BookDocumentPane'
import { NotePageStrip, NoteToolbar, ReaderPanelSwitch, ReaderTopBar } from './ReaderChrome'
import { ReaderSplitPane } from './ReaderSplitPane'
import { resolveBookSource } from './bookSource'
import { normalizeNoteImages } from './bookReaderModel'
import { useBookReaderState } from './useBookReaderState'
import './book-reader.css'

export function BookReaderWorkspace({ book, sessionId, onClose }) {
  const reader = useBookReaderState({ book, sessionId })
  const source = resolveBookSource(book)

  function closeAndPersist() {
    reader.saveReaderState()
    onClose()
  }

  return (
    <div className="br-shell">
      <ReaderTopBar
        title={book.title}
        savedAt={reader.savedAt}
        onBack={closeAndPersist}
        onSave={reader.saveReaderState}
        openUrl={source.openUrl}
      />
      <ReaderPanelSwitch panel={reader.panel} onChange={reader.setPanel} />

      <ReaderSplitPane
        panel={reader.panel}
        book={<BookDocumentPane book={book} />}
        notes={(
          <>
          <NoteToolbar
            editorMode={reader.editorMode}
            drawColor={reader.drawColor}
            drawSize={reader.drawSize}
            eraserSize={reader.eraserSize}
            onMode={reader.setEditorMode}
            onColor={reader.setDrawColor}
            onDrawSize={reader.setDrawSize}
            onEraserSize={reader.setEraserSize}
            onAddPage={reader.handleAddPage}
            onUpload={() => reader.uploadInputRef.current?.click()}
            onClearDrawing={() => reader.updatePageById(reader.resolvedActivePageId, { drawingDataUrl: '' })}
          />
          <NotePageStrip
            pages={reader.pages}
            activePageId={reader.resolvedActivePageId}
            activeTitle={reader.activePage?.title || ''}
            onSelect={reader.handleSelectPage}
            onTitleChange={(title) => reader.updatePageById(reader.resolvedActivePageId, { title })}
          />
          <input
            ref={reader.uploadInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={reader.handleImageUpload}
            className="br-hidden"
          />

          <div className="br-notes__scroll">
            {reader.pages.map((page, index) => (
              <NotePaper
                key={page.id}
                page={page}
                pageIndex={index}
                isActive={page.id === reader.resolvedActivePageId}
                showPageLabel={page.id === reader.visiblePageBadgeId}
                editorMode={reader.editorMode}
                drawColor={reader.drawColor}
                drawSize={reader.drawSize}
                eraserSize={reader.eraserSize}
                setPageRef={(node) => {
                  if (node) reader.pageElementRefs.current.set(page.id, node)
                  else reader.pageElementRefs.current.delete(page.id)
                }}
                onActivate={() => reader.setActivePageId(page.id)}
                onTextChange={(noteText) => reader.updatePageById(page.id, { noteText })}
                onDrawingChange={(drawingDataUrl) => reader.updatePageById(page.id, { drawingDataUrl })}
                onImageChange={(imageIndex, patch) => reader.updatePageById(page.id, (pageItem) => ({
                  images: normalizeNoteImages(pageItem.images).map((image, idx) => (
                    idx === imageIndex ? { ...image, ...patch } : image
                  )),
                }))}
                onImageRemove={(imageIndex) => reader.updatePageById(page.id, (pageItem) => ({
                  images: normalizeNoteImages(pageItem.images).filter((_, idx) => idx !== imageIndex),
                }))}
                onPaste={(event) => reader.pasteImagesFromClipboard(event, page.id)}
                onTypeMode={() => reader.setEditorMode('type')}
              />
            ))}
            <button type="button" className="br-notes__add" onClick={reader.handleAddPage}>
              + Thêm trang ghi chú
            </button>
          </div>
          </>
        )}
      />
    </div>
  )
}
