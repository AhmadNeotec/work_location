import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname)
    }
  },
  build: {
    outDir: '../../public/pwa',
    emptyOutDir: true,
  },
  publicDir: false,
})
