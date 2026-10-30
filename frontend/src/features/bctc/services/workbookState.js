export const workbookKey = (owner, ticker) => `northstar:bctc:model:v2:${encodeURIComponent(owner)}:${ticker.toUpperCase()}`
export const emptyWorkbook = () => ({
  revision: 0, active_tab: 'income', formula: '=NET_INCOME / REVENUE', notes: '',
  assumptions: { revenueGrowthPct: '5', grossMarginPct: '45', taxRatePct: '20', operatingExpenseGrowthPct: '3' },
})
export async function loadWorkbookState({ owner, ticker, storage, load }) {
  try {
    const result = await load(ticker, owner)
    return { model: result?.model ? { ...emptyWorkbook(), ...result.model } : emptyWorkbook(), offline: false }
  } catch (error) {
    if (error.status && error.status < 500) throw error
    let saved
    try { saved = JSON.parse(storage.getItem(workbookKey(owner, ticker)) || 'null') } catch { /* no usable cache */ }
    const model = saved?.owner === owner && saved?.ticker === ticker.toUpperCase() ? saved.model : null
    return { model: model ? { ...emptyWorkbook(), ...model } : emptyWorkbook(), offline: true }
  }
}
export async function saveWorkbookState({ owner, ticker, storage, model, save }) {
  const payload = { expected_revision: model.revision, active_tab: model.active_tab,
    formula: model.formula, notes: model.notes,
    assumptions: Object.fromEntries(Object.entries(model.assumptions).map(([k,v]) => [k, Number(v)]).filter(([,v]) => Number.isFinite(v))),
  }
  try {
    const result = await save(ticker, payload, owner)
    try { storage.removeItem(workbookKey(owner, ticker)) } catch { /* server save succeeded */ }
    return { model: result.model, offline: false }
  } catch (error) {
    if (error.status && error.status < 500) throw error
    storage.setItem(workbookKey(owner, ticker), JSON.stringify({ owner, ticker: ticker.toUpperCase(), model }))
    return { model, offline: true }
  }
}
