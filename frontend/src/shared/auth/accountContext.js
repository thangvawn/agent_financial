import { createContext, useContext } from 'react'
export const AccountContext = createContext('')
export const useAccountId = () => useContext(AccountContext)
export const accountStorageKey = (owner, resource) => owner ? `northstar:account:${encodeURIComponent(owner)}:${resource}` : null
