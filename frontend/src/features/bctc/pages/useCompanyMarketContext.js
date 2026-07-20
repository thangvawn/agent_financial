import { useEffect, useState } from 'react'

import { fetchCompanyMarketContext } from '../services/financialsApi'

export function useCompanyMarketContext(ticker) {
  const [state, setState] = useState({ loading: true, data: null })

  useEffect(() => {
    let cancelled = false
    fetchCompanyMarketContext(ticker).then((data) => {
      if (!cancelled) setState({ loading: false, data })
    })
    return () => { cancelled = true }
  }, [ticker])

  return state
}
