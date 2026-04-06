import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/dashboard-static/',
  server: {
    proxy: {
      '/dashboard/state': 'http://127.0.0.1:8000',
      '/dashboard/history': 'http://127.0.0.1:8000',
      '/dashboard/live': 'http://127.0.0.1:8000',
      '/dashboard/money-flow': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/eod': 'http://127.0.0.1:8000',
      '/scenario': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/research': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/financials': 'http://127.0.0.1:8000',
    },
  },
})
