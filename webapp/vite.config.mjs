import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    minify: false,
    rollupOptions: {
      input: './src/index.tsx',
      output: {
        entryFileNames: '_worker.js',
        format: 'es'
      }
    }
  }
})
