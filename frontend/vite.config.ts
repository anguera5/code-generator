import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0', 
    allowedHosts: ['genai-code-generator.duckdns.org', 'genai-portfolio.duckdns.org'],
    proxy: {
      '/api': {
  // Allow overriding the backend origin in local dev without changing docker-compose.
  // Usage examples:
  //  - Create frontend/.env.local with VITE_BACKEND_ORIGIN=http://localhost:8000
  //  - Keep default (backend:8000) when running inside Docker Compose
  target: process.env.VITE_BACKEND_ORIGIN || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
