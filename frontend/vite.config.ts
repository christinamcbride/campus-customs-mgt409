import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The backend runs on 8787 (8000 is taken by another project on this machine).
// Proxying /api keeps the frontend origin-relative, so image URLs returned by the
// API work unchanged and no CORS preflight is needed in development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
      },
    },
  },
})
