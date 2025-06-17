import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Rule for standard HTTP API calls
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Dedicated rule for WebSocket connections
      '/ws': {
        target: 'ws://127.0.0.1:5001',
        ws: true,
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('proxyReqWs', (proxyReq, req, socket, options, head) => {
            console.log('Proxying WebSocket request to:', options.target);
            // You can add custom headers here if needed, for example:
            // proxyReq.setHeader('X-Special-Header', 'my-special-value');
          });
          proxy.on('error', (err, req, res) => {
            console.error('WebSocket Proxy Error:', err);
          });
        }
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
}) 