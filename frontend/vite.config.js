import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import wasm from 'vite-plugin-wasm'
import topLevelAwait from 'vite-plugin-top-level-await'

export default defineConfig({
  // VITE_APP_BASE is injected by the GitHub Actions workflow as /RepoName/
  base: process.env.VITE_APP_BASE || '/',
  plugins: [
    react(),
    wasm(),
    topLevelAwait(),
  ],
  optimizeDeps: {
    exclude: ['stringverse-wasm'],
  },
})
