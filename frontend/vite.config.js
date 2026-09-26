import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = (env.VITE_API_URL || 'http://127.0.0.1:8000').trim();

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: '127.0.0.1',
      proxy: {
        '/chat': {
          target: proxyTarget,
          changeOrigin: true,
          timeout: 180000,
          proxyTimeout: 180000,
        },
        '/health': {
          target: proxyTarget,
          changeOrigin: true,
          timeout: 15000,
          proxyTimeout: 15000,
        },
      },
    },
  };
});

