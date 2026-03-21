// Vite 配置
// 功能：
// - React 插件配置
// - 开发服务器代理：/api -> http://localhost:8000（转发到后端FastAPI）
// - 构建输出目录：dist
// - 路径别名：@ -> src
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 120000,        // 2分钟，PDF 生成可能需要一段时间
        proxyTimeout: 120000,
      }
    }
  }
})
