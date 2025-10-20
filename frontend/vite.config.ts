import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react({
    // 使用 SWC 进行更快的刷新
    fastRefresh: true,
  })],
  server: {
    host: '0.0.0.0',
    port: 3004,
    hmr: {
      overlay: true, // 错误覆盖层
    },
    proxy: {
      '/api': 'http://localhost:8020',
      '/ws': {
        target: 'http://localhost:8020',
        ws: true
      }
    }
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'antd',
      '@ant-design/icons',
      'zustand',
      'axios',
      'nanoid'
    ],
  },
  // 构建优化
  build: {
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
        }
      }
    }
  }
});
