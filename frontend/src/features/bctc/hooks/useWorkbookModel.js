import { useEffect, useRef, useState } from 'react'
import { fetchFinancialWorkbookModel, saveFinancialWorkbookModel } from '../services/financialsApi'
import { emptyWorkbook, loadWorkbookState, saveWorkbookState, workbookKey } from '../services/workbookState'

export function useWorkbookModel(ticker, sessionId, accountId) {
  const owner = accountId || sessionId
  const scope = workbookKey(owner, ticker)
  const [state, setState] = useState({ scope, model: emptyWorkbook(), loading: true })
  const currentScope = useRef(scope)
  useEffect(() => { currentScope.current = scope }, [scope])
  const current = state.scope === scope ? state : { scope, model: emptyWorkbook(), loading: true }
  useEffect(() => {
    let cancelled = false
    setState({ scope, model: emptyWorkbook(), loading: true })
    // Only migrate a draft tagged with this server-verified current session.
    if (accountId && sessionId && accountId !== sessionId) {
      try {
        const oldKey = workbookKey(sessionId,ticker), newKey = workbookKey(accountId,ticker)
        const draft = JSON.parse(window.localStorage.getItem(oldKey) || 'null')
        if (draft?.owner === sessionId && draft.ticker === ticker.toUpperCase() && !window.localStorage.getItem(newKey)) {
          window.localStorage.setItem(newKey,JSON.stringify({...draft,owner:accountId}))
          window.localStorage.removeItem(oldKey)
        }
      } catch { /* keep the original draft when storage is unavailable */ }
    }
    loadWorkbookState({ owner, ticker, storage: window.localStorage, load: symbol => fetchFinancialWorkbookModel(symbol,sessionId) })
      .then(result => { if (!cancelled) setState({ scope, ...result, loading: false }) })
      .catch(error => { if (!cancelled) setState({ scope, model: emptyWorkbook(), loading: false, error: error.message }) })
    return () => { cancelled = true }
  }, [scope, ticker, owner, sessionId, accountId])
  const field = name => value => setState(previous => {
    const base = previous.scope === scope ? previous : { scope, model: emptyWorkbook(), loading: true }
    return { ...base, model: { ...base.model, [name]: typeof value === 'function' ? value(base.model[name]) : value } }
  })
  async function save() {
    if (current.loading || current.saving || current.error || current.conflict) throw new Error(current.error || (current.conflict ? 'Chọn cách xử lý xung đột trước khi lưu.' : '') || 'Workbook đang được tải hoặc lưu. Vui lòng đợi.')
    setState(previous => ({ ...previous, saving: true }))
    try {
      const result = await saveWorkbookState({ owner, ticker, storage: window.localStorage, model: current.model, save: (symbol,payload) => saveFinancialWorkbookModel(symbol,payload,sessionId) })
      if (currentScope.current !== scope) return null
      setState(previous => ({ ...previous, model: { ...previous.model, revision: result.model.revision }, saving: false, restoredDraft:result.offline, offline:result.offline }))
      return result.offline ? 'Đã lưu bản nháp trên thiết bị; chưa đồng bộ với máy chủ.' : 'Mô hình đã lưu vào phiên học.'
    } catch (error) {
      if (error.status === 409 && currentScope.current === scope) {
        const server = await fetchFinancialWorkbookModel(ticker,sessionId)
        if (currentScope.current === scope) setState(previous => ({...previous,conflict:true,serverModel:server?.model,restoredDraft:true}))
      }
      throw error
    } finally {
      if (currentScope.current === scope) setState(previous => ({ ...previous, saving: false }))
    }
  }
  function resolveConflict(keepDraft) {
    if (!current.serverModel) return
    setState(previous => ({...previous,conflict:false,model:keepDraft ? {...previous.model,revision:current.serverModel.revision} : current.serverModel,restoredDraft:keepDraft}))
    if (!keepDraft) window.localStorage.removeItem(scope)
  }
  return { ...current.model, restoredDraft:current.restoredDraft, conflict:current.conflict, resolveConflict, loading: current.loading, saving: current.saving, error: current.error, save,
    setFormula: field('formula'), setNotes: field('notes'), setScenario: field('assumptions'), setActiveTab: field('active_tab') }
}
