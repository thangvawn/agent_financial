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
      '/dashboard/state': 'http://127.0.0.1:8001',
      '/dashboard/history': 'http://127.0.0.1:8001',
      '/dashboard/cross-asset': 'http://127.0.0.1:8001',
      '/dashboard/live': 'http://127.0.0.1:8001',
      '/dashboard/money-flow': 'http://127.0.0.1:8001',
      '/api': 'http://127.0.0.1:8001',
      '/health': 'http://127.0.0.1:8001',
      '/eod': 'http://127.0.0.1:8001',
      '/scenario': 'http://127.0.0.1:8001',
      '/research': 'http://127.0.0.1:8001',
      '/admin': 'http://127.0.0.1:8001',
      '/financials': 'http://127.0.0.1:8001',
      '/backtest': 'http://127.0.0.1:8001',
      '/learning-assets': 'http://127.0.0.1:8001',
      '/watchlist': 'http://127.0.0.1:8001',
    },
  },
  preview: {
    host: true,
  },
})
