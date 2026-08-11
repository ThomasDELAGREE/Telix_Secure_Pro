import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Le portail est servi derriere Nginx Proxy Manager (voir npm-provisioning/).
// Les appels API passent par /api/auth/* (proxifie vers auth-service par NPM
// ou, en developpement local, directement via le proxy Vite ci-dessous).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/auth/, '/auth'),
      },
    },
  },
});
