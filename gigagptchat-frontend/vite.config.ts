import { defineConfig } from 'vite'

import react from '@vitejs/plugin-react'

import path from 'path'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    proxy: {
      '/api/v1': {
        target: 'https://gigachat.devices.sberbank.ru',
        
        changeOrigin: true,
        
        secure: false,
      },

      '/oauth': {
        target: 'https://ngw.devices.sberbank.ru:9443',
        
        changeOrigin: true,
        
        secure: false,
        
        rewrite: (path) => path.replace(/^\/oauth/, ''),
      },
    },
  },
})