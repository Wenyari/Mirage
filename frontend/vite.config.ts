import react from '@vitejs/plugin-react'
import path from "path"
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
headers: {
      // 在原有的基础上，显式加上 script-src-elem 和 script-src-attr
      // 这里的规则必须和 script-src 完全一致
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com blob:; script-src-elem 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com blob:; script-src-attr 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com blob:; child-src 'self' https://challenges.cloudflare.com blob:; worker-src 'self' blob:; frame-src 'self' https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://challenges.cloudflare.com;"
    }
  },
})
