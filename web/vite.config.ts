import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '../', '')
  const vitePort    = parseInt(env.SERVER_VITE_PORT    || '13406')
  const previewPort = parseInt(env.SERVER_PREVIEW_PORT || String(vitePort + 1))
  const serverPort  = parseInt(env.SERVER_PORT         || '13405')

  const apiProxy = {
    '/internal': `http://localhost:${serverPort}`,
    '/api': `http://localhost:${serverPort}`,
  }

  return {
  plugins: [
    vue(),
    vuetify({ autoImport: true, styles: { configFile: 'src/styles/settings.scss' } }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: vitePort,
    proxy: apiProxy,
  },
  optimizeDeps: {
    include: [
      'vuetify/components/VRangeSlider',
    ],
  },
  publicDir: 'static',
  preview: {
    port: previewPort,
    proxy: apiProxy,
  },
  build: {
    outDir: 'dist',
  },
  }
})
