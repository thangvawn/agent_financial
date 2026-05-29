import { useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { createQueryClient } from './queryClient'

export default function QueryProvider({ children }) {
  const [client] = useState(() => createQueryClient())
  return (
    <QueryClientProvider client={client}>
      {children}
      {import.meta.env.DEV ? <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" /> : null}
    </QueryClientProvider>
  )
}
