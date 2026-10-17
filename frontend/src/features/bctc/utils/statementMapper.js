/**
 * BCTC Statement Row Key Aliases & Metric Resolvers.
 * Resolves standard financial keys against provider-specific VAS codes
 * (isa/bse/cfa) and derives missing components (COGS, margins).
 */

export const ROW_KEY_ALIASES = {
  // Income Statement
  revenue: ['revenue', 'isa3', 'isa1', 'net_revenue'],
  cost_of_goods_sold: ['cost_of_goods_sold', 'isa4', 'cogs'],
  gross_profit: ['gross_profit', 'isa5'],
  operating_profit: ['operating_profit', 'isa11', 'operating_income'],
  net_income: ['net_income', 'isa20', 'isa22', 'net_profit'],

  // Balance Sheet
  cash: ['cash', 'bse1', 'bse2', 'cash_and_equivalents'],
  receivables: ['receivables', 'bse10', 'bse130', 'accounts_receivable'],
  inventory: ['inventory', 'bse30', 'bse140'],
  current_assets: ['current_assets', 'bse100', 'bsa1'],
  total_assets: ['total_assets', 'bse200', 'bse270'],
  current_liabilities: ['current_liabilities', 'bse310'],
  total_liabilities: ['total_liabilities', 'bse300'],
  equity: ['equity', 'bse400', 'shareholders_equity'],
  debt: ['debt', 'bse320', 'bse338', 'short_term_debt', 'long_term_debt'],

  // Cash Flow
  operating_cash_flow: ['operating_cash_flow', 'cfa20', 'cfo'],
  investing_cash_flow: ['investing_cash_flow', 'cfa30', 'cfi'],
  financing_cash_flow: ['financing_cash_flow', 'cfa40', 'cff'],
  capex: ['capex', 'cfa22'],
  free_cash_flow: ['free_cash_flow', 'fcf'],
}

/**
 * Finds a row in statementRows Map using the canonical key or known aliases.
 */
export function findRowWithAliases(statementRows, key) {
  if (!statementRows) return undefined
  if (statementRows.has(key)) return statementRows.get(key)
  const aliases = ROW_KEY_ALIASES[key] || []
  for (const alias of aliases) {
    if (statementRows.has(alias)) {
      const candidate = statementRows.get(alias)
      if (candidate?.values?.length || candidate?.value !== undefined) {
        return candidate
      }
    }
  }
  return undefined
}
