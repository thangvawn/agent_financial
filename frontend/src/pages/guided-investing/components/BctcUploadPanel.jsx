export default function BctcUploadPanel({ uploadTypes, uploadResult, extractionResult, uploading, onUpload, onAnalyze }) {
  const accept = uploadTypes?.accept || '.pdf,.xlsx,.xls,.csv,.docx,.doc,.png,.jpg,.jpeg,.tif,.tiff,.webp,.html,.htm,.xml,.zip'
  const typeSummary = summarizeUploadTypes(uploadTypes)
  const canAnalyze = canAnalyzeUploadedStatement(uploadResult)
  const needsMarkdown = uploadResult && !canAnalyze && uploadResult.status !== 'analyzed'

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 shadow-sm flex flex-col gap-4">
      <div>
        <span className="text-[10px] text-slate-400 dark:text-zinc-550 font-bold uppercase tracking-wider">Upload BCTC</span>
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">{uploading ? 'Đang nhận file...' : 'File BCTC → Markdown → Chart'}</h3>
        <small className="block text-xs text-slate-500 dark:text-zinc-400 mt-1">{typeSummary}</small>
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <label className="px-4 py-2.5 rounded-full text-xs font-semibold bg-teal-500 hover:bg-teal-600 text-white cursor-pointer active:scale-95 transition-all shadow-sm">
          <input type="file" className="hidden" accept={accept} onChange={onUpload} disabled={uploading} />
          {uploading ? 'Đang upload...' : 'Chọn file BCTC'}
        </label>
        {uploadResult && uploadResult.status !== 'analyzed' && (
          <button
            type="button"
            className="px-4 py-2.5 rounded-full text-xs font-semibold bg-white dark:bg-zinc-800 hover:bg-slate-50 dark:hover:bg-zinc-850 border border-slate-200 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 cursor-pointer active:scale-95 transition-all"
            onClick={onAnalyze}
            disabled={uploading}
            title="Tạo Markdown context, map bảng BCTC rồi dựng chart từ các dòng số liệu đã trích xuất."
          >
            Phân tích file
          </button>
        )}
      </div>

      {uploadResult && (
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-zinc-950/20 border border-slate-150 dark:border-zinc-850 text-xs flex flex-col gap-1">
          <strong className="font-semibold text-slate-900 dark:text-white">{uploadResult.file_type?.label || 'File'}</strong>
          <span className="text-slate-550 dark:text-zinc-400">
            {uploadStatusText(uploadResult)} · {formatBytes(uploadResult.size_bytes)} · {uploadResult.file_type?.pipeline}
          </span>
          {needsMarkdown && <i className="text-[10px] text-amber-600 dark:text-amber-400 mt-1 block">Hệ thống sẽ tạo Markdown context và bảng dòng BCTC trước khi vẽ chart.</i>}
        </div>
      )}

      {extractionResult && <BctcExtractionSummary result={extractionResult} />}
    </div>
  )
}

function BctcExtractionSummary({ result }) {
  const pages = result?.pages || []
  const warnings = result?.warnings || []
  const rowCount = result?.markdown_row_count || result?.quality?.ocr_statement_row_count || result?.raw_tables?.[0]?.rows?.length || 0

  return (
    <div className={`p-4 rounded-xl border text-xs flex flex-col gap-3 ${
      result.status === 'markdown_ready'
        ? 'bg-emerald-50/50 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-450'
        : 'bg-slate-50 dark:bg-zinc-950/10 border-slate-200 dark:border-zinc-850'
    }`}>
      <div>
        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-white/60 dark:bg-zinc-800/60 uppercase tracking-wider mb-1">{extractionStatusLabel(result.status)}</span>
        <strong className="block text-slate-900 dark:text-white font-bold">{result.source_kind || 'unknown source'}</strong>
        <p className="text-[10px] text-slate-500 dark:text-zinc-400 mt-1">
          {pages.length ? `${pages.length} trang preview` : 'Chưa có preview'} · {rowCount} dòng Markdown · text layer {result.quality?.text_layer_chars ?? 0} ký tự
        </p>
      </div>

      {(pages.length || result.markdown?.url) && (
        <div className="flex gap-2 flex-wrap border-t border-slate-100 dark:border-zinc-850/60 pt-2">
          {result.markdown?.url && (
            <a href={result.markdown.url} target="_blank" rel="noreferrer" className="px-2 py-1 rounded bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 text-teal-600 dark:text-teal-400 font-bold hover:underline">
              Markdown
            </a>
          )}
          {pages.slice(0, 4).map((page) => (
            <a key={page.page} href={page.preview_url} target="_blank" rel="noreferrer" className="px-2 py-1 rounded bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 text-slate-655 dark:text-zinc-350 hover:underline">
              Trang {page.page}
            </a>
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <ul className="list-disc pl-4 flex flex-col gap-1 text-[10px] text-amber-700 dark:text-amber-450 border-t border-slate-105 dark:border-zinc-850/50 pt-2">
          {warnings.slice(0, 3).map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      )}
    </div>
  )
}

function summarizeUploadTypes(uploadTypes) {
  const types = uploadTypes?.types || {}
  const count = Object.values(types).reduce((total, items) => total + (items?.length || 0), 0)
  const maxSize = uploadTypes?.max_file_size_mb
  if (!count) return 'Hỗ trợ PDF, XLSX, CSV, DOCX, ảnh scan và XML/XBRL.'
  return `${count} định dạng · tối đa ${maxSize || 25}MB/file · ưu tiên PDF gốc hoặc Excel.`
}

function uploadStatusText(uploadResult) {
  if (uploadResult?.status === 'analyzed') return `đã phân tích ${uploadResult.period_count || 0} kỳ`
  if (uploadResult?.extraction_status === 'markdown_ready') return 'đã có Markdown bảng BCTC, sẵn sàng dựng chart'
  if (uploadResult?.extraction_status === 'needs_ocr') return 'đã có Markdown thô nhưng chưa đủ bảng số liệu'
  if (uploadResult?.extraction_status) return `đã trích xuất: ${uploadResult.extraction_status}`
  if (uploadResult?.status === 'uploaded') return 'đã upload, bấm Phân tích file upload'
  return uploadResult?.status || 'ready'
}

function canAnalyzeUploadedStatement(uploadResult) {
  return uploadResult?.file_type?.pipeline === 'structured_table' || uploadResult?.extraction_status === 'markdown_ready'
}

function extractionStatusLabel(status) {
  if (status === 'markdown_ready') return 'Markdown ready'
  if (status === 'needs_ocr') return 'Markdown thô'
  if (status === 'text_detected') return 'Có text layer'
  if (status === 'extracted') return 'Đã trích xuất'
  if (status === 'unsupported') return 'Chưa hỗ trợ'
  return 'Extraction'
}

function formatBytes(bytes) {
  const value = Number(bytes)
  if (!Number.isFinite(value) || value <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1)
  const amount = value / (1024 ** index)
  return `${amount.toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}
