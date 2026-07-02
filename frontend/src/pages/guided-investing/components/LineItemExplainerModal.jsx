import { useEffect, useState } from 'react'
import { fetchLineItemExplanation } from '../../../modules/financials'

export default function LineItemExplainerModal({ itemKey, ticker, period, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchLineItemExplanation(ticker, period, itemKey)
        setData(result)
      } catch (err) {
        console.error('Failed to fetch explanation:', err)
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [ticker, period, itemKey])

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4" onClick={onClose}>
      <div className="relative w-full max-w-lg bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-4 max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-start gap-4">
          <div>
            <span className="text-[10px] text-teal-605 dark:text-teal-400 font-bold uppercase tracking-wider">Tra cứu thuật ngữ</span>
            <h2 className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">{itemKey}</h2>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:bg-slate-105 hover:text-slate-655 dark:hover:bg-zinc-800 cursor-pointer text-lg font-bold">&times;</button>
        </div>
        
        {loading ? (
          <p className="text-xs text-slate-500 py-4 text-center">Đang tải giải thích...</p>
        ) : data ? (
          <div className="flex flex-col gap-4 text-xs md:text-sm text-slate-650 dark:text-zinc-355 leading-relaxed">
            <p className="font-semibold text-slate-805 dark:text-zinc-200">{data.definition}</p>
            {data.formula && (
              <div className="bg-slate-50 dark:bg-zinc-950/60 p-3.5 rounded-xl border border-slate-150 dark:border-zinc-800 font-mono text-xs text-teal-600 dark:text-teal-450">
                <strong className="block text-[10px] font-bold uppercase tracking-wider mb-1 text-slate-450 dark:text-zinc-500">Công thức:</strong> {data.formula}
              </div>
            )}
            <div>
              <strong className="block text-[11px] font-bold uppercase tracking-wider text-slate-450 dark:text-zinc-500 mb-1">Ý nghĩa:</strong>
              <p>{data.significance}</p>
            </div>
            {data.red_flags && data.red_flags.length > 0 && (
              <div className="p-4 rounded-2xl bg-red-50/50 dark:bg-red-950/10 border border-red-100 dark:border-red-900/30">
                <strong className="block text-[11px] font-bold uppercase tracking-wider text-red-600 dark:text-red-405 mb-2">Dấu hiệu cần lưu ý:</strong>
                <ul className="list-disc pl-4 flex flex-col gap-1 text-red-700 dark:text-red-300">
                  {data.red_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.examples && data.examples.length > 0 && (
              <div className="p-4 rounded-2xl bg-teal-50/30 dark:bg-teal-950/10 border border-teal-100 dark:border-teal-900/20">
                <strong className="block text-[11px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400 mb-2">Ví dụ phân tích:</strong>
                <ul className="list-disc pl-4 flex flex-col gap-1 text-slate-600 dark:text-zinc-400">
                  {data.examples.map((ex, idx) => (
                    <li key={idx}>{ex}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-slate-500 py-4 text-center">Không tìm thấy dữ liệu giải thích cho chỉ tiêu này.</p>
        )}
      </div>
    </div>
  )
}
