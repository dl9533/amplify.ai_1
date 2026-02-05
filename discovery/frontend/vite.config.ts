import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      // Only proxy specific API paths, not SPA routes
      // SPA routes like /discovery/{uuid}/upload should be handled by React Router
      '/discovery/sessions': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/uploads': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/role-mappings': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/lob': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/activities': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/analysis': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/roadmap': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/handoff': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/exports': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/admin': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/onet': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/discovery/chat': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
