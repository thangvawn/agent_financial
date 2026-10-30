import { useEffect, useRef, useState } from 'react'
import { fetchFinancialWorkbookModel, saveFinancialWorkbookModel } from '../services/financialsApi'
import { emptyWorkbook, loadWorkbookState, saveWorkbookState, workbookKey } from '../services/workbookState'

export function useWorkbookModel(ticker, owner) {
  const scope = workbookKey(owner, ticker)
  const [state, setState] = useState({ scope, model: emptyWorkbook(), loading: true })
  const currentScope = useRef(scope)
  useEffect(() => { currentScope.current = scope }, [scope])
  const current = state.scope === scope ? state : { scope, model: emptyWorkbook(), loading: true }
  useEffect(() => {
    let cancelled = false
    setState({ scope, model: emptyWorkbook(), loading: true })
    loadWorkbookState({ owner, ticker, storage: window.localStorage, load: fetchFinancialWorkbookModel })
      .then(result => { if (!cancelled) setState({ scope, ...result, loading: false }) })
      .catch(error => { if (!cancelled) setState({ scope, model: emptyWorkbook(), loading: false, error: error.message }) })
    return () => { cancelled = true }
  }, [scope, ticker, owner])
  const field = name => value => setState(previous => {
    const base = previous.scope === scope ? previous : { scope, model: emptyWorkbook(), loading: true }
    return { ...base, model: { ...base.model, [name]: typeof value === 'function' ? value(base.model[name]) : value } }
  })
  async function save() {
    if (current.loading || current.saving || current.error) throw new Error(current.error || 'Workbook đang được tải hoặc lưu. Vui lòng đợi.')
    setState(previous => ({ ...previous, saving: true }))
    try {
      const result = await saveWorkbookState({ owner, ticker, storage: window.localStorage, model: current.model, save: saveFinancialWorkbookModel })
      if (currentScope.current !== scope) return null
      setState(previous => ({ ...previous, model: { ...previous.model, revision: result.model.revision }, saving: false }))
      return result.offline ? 'Đã lưu bản nháp trên thiết bị; chưa đồng bộ với máy chủ.' : 'Mô hình đã lưu vào phiên học.'
    } finally {
      if (currentScope.current === scope) setState(previous => ({ ...previous, saving: false }))
    }
  }
  return { ...current.model, loading: current.loading, saving: current.saving, error: current.error, save,
    setFormula: field('formula'), setNotes: field('notes'), setScenario: field('assumptions'), setActiveTab: field('active_tab') }
}
