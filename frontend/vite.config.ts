import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

const BACKEND_URL = 'http://127.0.0.1:8000';

export default defineConfig({
  server: {
    // In dev, Vite serves the frontend on its own port; api/client.ts calls
    // relative paths like /auth/login. Without this proxy those requests hit
    // Vite's own dev server, not the backend, and never reach the real API.
    // The production build has no such issue: it's served by the backend
    // itself (see backend/src/local_attendance/main.py), so paths resolve
    // same-origin with no proxy needed.
    proxy: {
      '/auth': BACKEND_URL,
      '/employees': BACKEND_URL,
      '/attendance': BACKEND_URL,
      '/dashboard': BACKEND_URL,
    },
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [],
      },
      manifest: {
        name: 'Pointage Garde',
        short_name: 'Pointage',
        theme_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ]
});
