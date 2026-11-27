import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      frappeTypes: false,
      buildConfig: {
        indexHtmlPath: '../project_board/www/project-board.html',
        outDir: '../project_board/public/frontend',
        baseUrl: '/assets/project_board/frontend/',
        emptyOutDir: true,
        sourcemap: true,
      },
    }),
    vue(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    include: ['tailwind.config.js', 'lowlight'],
  },
  server: {
    port: 8081,
    allowedHosts: true,
  },
})
