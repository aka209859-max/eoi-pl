import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    target: 'esnext',
    minify: true,
    rollupOptions: {
      input: 'src/index.tsx',
      output: {
        entryFileNames: '_worker.js',
        format: 'es'
      }
    }
  }
})
