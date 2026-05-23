import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const envDir = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, '')
  const backendPort = Number(env.ANI_COL_PORT || '8001')
  const devServerPort = Number(env.VITE_DEV_SERVER_PORT || '5173')
  const apiTarget = env.VITE_API_BASE_URL || `http://localhost:${backendPort}`

  return {
    envDir,
    plugins: [vue()],
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) {
              return
            }

            if (id.includes('@element-plus/icons-vue')) {
              return 'element-plus-icons'
            }

            if (id.includes('node_modules/element-plus/')) {
              const componentPath = 'node_modules/element-plus/es/components/'
              const componentIndex = id.indexOf(componentPath)

              if (componentIndex >= 0) {
                const componentName = id.slice(componentIndex + componentPath.length).split('/')[0]
                return `element-plus-${componentName}`
              }

              return 'element-plus-core'
            }

            if (id.includes('vue-router')) {
              return 'vue-router'
            }

            return 'vendor'
          }
        }
      }
    },
    server: {
      port: devServerPort,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true
        },
        '/health': {
          target: apiTarget,
          changeOrigin: true
        }
      }
    }
  }
})
