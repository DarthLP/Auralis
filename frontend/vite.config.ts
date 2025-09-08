import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
// eslint-disable-next-line no-redeclare
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(fileURLToPath(new URL('.', import.meta.url)), 'src'),
      '@schema': path.resolve(fileURLToPath(new URL('.', import.meta.url)), '../schema'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
