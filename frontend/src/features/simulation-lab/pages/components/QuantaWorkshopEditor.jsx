import { useState } from 'react'
import { Code2, Check, Copy } from 'lucide-react'
import { QUANTA_STRATEGY_PRESETS } from '../../content/quantaStrategyPresets'

export default function QuantaWorkshopEditor({ code, onChange, onApplyPreset, onRunBacktest }) {
  const [copied, setCopied] = useState(false)
  const lineCount = (code || '').split('\n').length

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }).catch(() => {})
  }

  const isSyntaxValid = Boolean(
    code.includes('params:') &&
    code.includes('detect:') &&
    (code.includes('act:') || code.includes('score:'))
  )

  return (
    <div className="simlab-editor-box">
      <div className="simlab-editor-toolbar">
        <div className="flex items-center gap-2">
          <Code2 size={15} className="text-cyan-400" />
          <span className="text-xs font-semibold text-slate-200">Quanta Story Script</span>
          <span className={`simlab-status-badge ${isSyntaxValid ? 'is-valid' : 'is-warning'}`}>
            {isSyntaxValid ? 'Đã có các khối chính' : 'Cần khối act/score'}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <select
            className="simlab-preset-select"
            onChange={(e) => {
              const selected = QUANTA_STRATEGY_PRESETS.find((p) => p.id === e.target.value)
              if (selected) onApplyPreset(selected)
            }}
            defaultValue=""
          >
            <option value="" disabled>Mẫu chiến lược...</option>
            {QUANTA_STRATEGY_PRESETS.map((preset) => (
              <option key={preset.id} value={preset.id}>{preset.name}</option>
            ))}
          </select>

          <button
            type="button"
            onClick={handleCopy}
            className="simlab-btn-tool"
            title="Sao chép toàn bộ mã"
          >
            {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
          </button>
        </div>
      </div>

      <div
        className="simlab-editor-workspace"
        style={{ display: 'flex', flexDirection: 'row', minHeight: '340px', background: 'var(--bg)' }}
      >
        <div
          className="simlab-editor-lines"
          style={{
            width: '44px',
            textAlign: 'right',
            padding: '10px 8px',
            userSelect: 'none',
            color: 'var(--ink-muted)',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12px',
            lineHeight: '20px',
            backgroundColor: 'var(--surface-alt)',
            borderRight: '1px solid var(--line)',
            whiteSpace: 'pre',
            boxSizing: 'border-box',
          }}
        >
          {Array.from({ length: lineCount }, (_, i) => i + 1).join('\n')}
        </div>

        <textarea
          value={code}
          onChange={(e) => onChange(e.target.value)}
          className="simlab-editor-textarea"
          spellCheck={false}
          style={{
            flex: 1,
            padding: '10px 12px',
            background: 'transparent',
            border: 'none',
            color: 'var(--ink)',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12.5px',
            lineHeight: '20px',
            outline: 'none',
            resize: 'none',
            whiteSpace: 'pre',
            tabSize: 2,
            height: '340px',
          }}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
              e.preventDefault()
              if (onRunBacktest) onRunBacktest()
            }
          }}
          placeholder="Viết mã Quanta DSL tại đây..."
        />
      </div>

      <div className="simlab-editor-statusbar">
        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span>{lineCount} dòng</span>
          <span>{code.length} ký tự</span>
          <span className="text-cyan-300 font-mono">Quanta v2.5 DSL</span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-500">
          <span><kbd className="simlab-kbd">F5</kbd> Chạy</span>
          <span><kbd className="simlab-kbd">Ctrl+↵</kbd> Compile</span>
        </div>
      </div>
    </div>
  )
}
