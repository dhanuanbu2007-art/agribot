import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/chat': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        timeout: 180000,
        proxyTimeout: 180000,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        timeout: 15000,
        proxyTimeout: 15000,
      },
    },
  },
});
