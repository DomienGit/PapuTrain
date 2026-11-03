import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // host: true = nasłuchuj na wszystkich interfejsach (0.0.0.0),
    // żeby aplikacja była dostępna z telefonu w tej samej sieci Wi-Fi.
    host: true,
    // W trybie deweloperskim zapytania /api idą przez serwer Vite do backendu
    // (unikamy problemu CORS — przeglądarka myśli, że to ta sama domena).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
