const { defineConfig } = require('vite')
const vue = require('@vitejs/plugin-vue')
const path = require('path')

module.exports = defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      // Proxy /alert_images to the backend server for alert images
      '/alert_images': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Proxy all API calls starting with /api to the backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // Add this new rule for WebSocket
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
})