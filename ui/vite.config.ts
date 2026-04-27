import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ["vue", "vue-router"],
          tdesign: ["tdesign-vue-next"],
        },
      },
    },
  },
  server: {
    host: "127.0.0.1",
    port: 43187,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:43188",
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "127.0.0.1",
    port: 43187,
    strictPort: true,
  },
});
