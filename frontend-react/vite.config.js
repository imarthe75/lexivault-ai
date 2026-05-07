import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/lexivault/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    hmr: {
      host: 'arquitectura.casmart.internal',
      protocol: 'wss'
    },
    proxy: {
      '/lexivault/api': {
        target: 'http://flask_backend:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/lexivault\/api/, '')
      }
    }
  }
})
