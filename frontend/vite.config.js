import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/dashboard-static/',
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('three')) return 'vendor-three'
            if (id.includes('lightweight-charts')) return 'vendor-charts'
            if (id.includes('lucide-react')) return 'vendor-icons'
            if (id.includes('framer-motion') || id.includes('animejs')) return 'vendor-motion'
            if (id.includes('@tanstack/react-query')) return 'vendor-query'
            if (id.includes('react') || id.includes('react-dom')) return 'vendor-react'
          }
        },
      },
    },
    chunkSizeWarningLimit: 650,
  },
  server: {
    // Lắng nghe mọi interface — truy cập từ máy khác qua http://<IP-LAN>:5173
    host: true,
    proxy: {
      '/dashboard/state': 'http://127.0.0.1:8000',
      '/dashboard/history': 'http://127.0.0.1:8000',
      '/dashboard/cross-asset': 'http://127.0.0.1:8000',
      '/dashboard/live': 'http://127.0.0.1:8000',
      '/dashboard/money-flow': 'http://127.0.0.1:8000',
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/eod': 'http://127.0.0.1:8000',
      '/scenario': 'http://127.0.0.1:8000',
      '/research': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/financials': 'http://127.0.0.1:8000',
      '/backtest': 'http://127.0.0.1:8000',
      '/learning-assets': 'http://127.0.0.1:8000',
      '/watchlist': 'http://127.0.0.1:8000',
    },
  },
  preview: {
    host: true,
  },
})
