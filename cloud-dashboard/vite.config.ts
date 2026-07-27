import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Only used in dev: cloud-backend/'s local dev server port. The dashboard
// and cloud-backend are two separately deployed services (unlike the local
// guard PWA, which is served by its own backend as static assets) — in
// production the dashboard calls VITE_API_BASE_URL directly (see
// src/api/client.ts) and this proxy is not involved at all.
const CLOUD_BACKEND_URL = 'http://127.0.0.1:8001';

export default defineConfig({
  server: {
    proxy: {
      '/auth': CLOUD_BACKEND_URL,
      '/employees': CLOUD_BACKEND_URL,
      '/attendance': CLOUD_BACKEND_URL,
      '/reports': CLOUD_BACKEND_URL,
      '/users': CLOUD_BACKEND_URL,
    },
  },
  plugins: [react()],
});
