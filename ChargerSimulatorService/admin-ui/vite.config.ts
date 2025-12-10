import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  root: '.',
  server: {
    port: 5173
  },
  build: {
    outDir: resolve(__dirname, '../src/api/../admin_build'),
    emptyOutDir: true
  }
})
