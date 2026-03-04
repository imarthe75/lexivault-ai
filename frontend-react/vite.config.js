import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 8000,
    proxy: {
      '/login': 'http://flask_backend:5000',
      '/register': 'http://flask_backend:5000',
      '/documents': 'http://flask_backend:5000',
      '/ask': 'http://flask_backend:5000',
    }
  }
})
