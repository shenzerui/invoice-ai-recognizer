import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import legacy from '@vitejs/plugin-legacy'
import path from 'path'

// Vite 配置
export default defineConfig({
  plugins: [
    vue(),
    // ★ 关键：legacy 插件，让打包产物兼容 IE11 / 旧浏览器
    //    自动做三件事：
    //      1. 把现代 <script type="module"> 编译成 IE 能识别的 legacy 脚本
    //      2. 注入 core-js polyfill（Promise / Proxy / Map / Set / async-await ...）
    //      3. 给旧版浏览器加 <script nomodule> 回退入口
    //    这样 PyWebView 的 mshtml（IE 内核）就能跑 Vue3 了
    legacy({
      targets: ['defaults', 'IE 11'],   // 最低兼容 IE 11（mshtml 相当于 IE 11）
      additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/uploads': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  // 注意：不要自己设 build.target，legacy 插件会 override
})
