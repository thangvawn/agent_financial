import { useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'

import { createQueryClient } from './queryClient'

export default function QueryProvider({ children }) {
  const [client] = useState(() => createQueryClient())
  return (
    <QueryClientProvider client={client}>
      {children}
    </QueryClientProvider>
  )
}
