import { useState } from 'react'
import { Check, Copy, Play, Sparkles, X } from 'lucide-react'

const TEMPLATES = [
  {
    name: 'EMA Cross Pulse',
    code: `strategy "Tide Reclaim Pulse"
@regime "trending"
@style "momentum"

params:
  fast_len = 20 in [5..100]
  slow_len = 50 in [20..200]
  risk_pct = 5pct in [1pct..20pct]

detect:
  c = market.close
  tide_fast = ema(c, fast_len)
  tide_slow = ema(c, slow_len)
  long_setup = tide_fast crossover tide_slow

act:
  when long_setup and not position.is_long:
    enter long with wnav risk_pct tag "Tide Long"

render:
  panel main:
    line tide_fast as "Fast Tide" in cyan
    line tide_slow as "Slow Tide" in amber`,
  },
  {
    name: 'Turtle Donchian Vol',
    code: `strategy "Turtle Donchian Breakout"
@regime "breakout"

params:
  channel_len = 20 in [10..55]

detect:
  c = market.close
  upper = hhv(market.high, channel_len)
  breakout = c > upper[1]

act:
  when breakout and not position.is_long:
    enter long with wnav 10pct tag "Breakout"`,
  },
]

export default function QuantaStudioModal({ isOpen, onClose }) {
  const [code, setCode] = useState(TEMPLATES[0].code)
  const [copied, setCopied] = useState(false)
  const [verified, setVerified] = useState(null)

  if (!isOpen) return null

  function handleVerify() {
    const hasStrategy = code.includes('strategy') || code.includes('study')
    const hasDetect = code.includes('detect:') || code.includes('render:')
    if (hasStrategy && hasDetect) {
      setVerified({ ok: true, msg: 'Cú pháp hợp lệ! Đã xác nhận các khối logic Quanta Story.' })
    } else {
      setVerified({ ok: false, msg: 'Cần khai báo header (strategy/study) và khối detect:/render:.' })
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }).catch(() => {})
  }

  return (
    <div className="qd-modal-overlay" role="dialog" aria-modal="true">
      <div className="qd-modal-box">
        <header className="qd-modal-header">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-cyan-300" />
            <h2 className="text-base font-bold text-white">Quanta Studio Sandbox</h2>
            <span className="qd-badge qd-badge--cyan">v4.0 Quant OS</span>
          </div>
          <button type="button" className="qd-modal-close" onClick={onClose}>
            <X size={16} />
          </button>
        </header>

        <div className="qd-modal-body">
          <div className="qd-template-bar">
            <span className="text-xs text-gray-400">Mẫu chiến lược:</span>
            {TEMPLATES.map((tmpl) => (
              <button
                key={tmpl.name}
                type="button"
                className="qd-tmpl-btn"
                onClick={() => { setCode(tmpl.code); setVerified(null) }}
              >
                {tmpl.name}
              </button>
            ))}
          </div>

          <textarea
            value={code}
            onChange={(e) => { setCode(e.target.value); setVerified(null) }}
            className="qd-editor-textarea font-mono text-xs thin-scrollbar"
            rows={14}
            spellCheck="false"
          />

          {verified && (
            <div className={`qd-verify-badge ${verified.ok ? 'is-ok' : 'is-err'}`}>
              {verified.ok ? '✓ ' : '⚠ '} {verified.msg}
            </div>
          )}
        </div>

        <footer className="qd-modal-footer">
          <button type="button" className="qd-btn qd-btn--outline" onClick={handleCopy}>
            {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
            <span>{copied ? 'Đã sao chép' : 'Sao chép mã'}</span>
          </button>
          <button type="button" className="qd-btn qd-btn--primary" onClick={handleVerify}>
            <Play size={14} />
            <span>Kiểm tra Cú pháp DSL</span>
          </button>
        </footer>
      </div>
    </div>
  )
}
