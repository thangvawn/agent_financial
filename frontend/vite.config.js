import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/dashboard-static/',
  server: {
    // Lắng nghe mọi interface — truy cập từ máy khác qua http://<IP-LAN>:5173
    host: true,
    proxy: {
      '/dashboard/state': 'http://127.0.0.1:8000',
      '/dashboard/history': 'http://127.0.0.1:8000',
      '/dashboard/cross-asset': 'http://127.0.0.1:8000',
      '/dashboard/live': 'http://127.0.0.1:8000',
      '/dashboard/money-flow': 'http://127.0.0.1:8000',
      '/api/v1': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/eod': 'http://127.0.0.1:8000',
      '/scenario': 'http://127.0.0.1:8000',
      '/chat': 'http://127.0.0.1:8000',
      '/research': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/financials': 'http://127.0.0.1:8000',
      '/backtest': 'http://127.0.0.1:8000',
      '/watchlist': 'http://127.0.0.1:8000',
    },
  },
  preview: {
    host: true,
  },
})
