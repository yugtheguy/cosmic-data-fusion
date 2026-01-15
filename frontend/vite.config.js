import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ingest': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/search': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/visualize': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/datasets': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/harmonize': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ai': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/query/search': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/query/export': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/query/sources': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/errors': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
