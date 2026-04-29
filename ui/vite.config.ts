import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

function resolveManualChunk(id: string): string | undefined {
  const normalizedId = id.replace(/\\/g, "/");

  if (normalizedId.includes("/node_modules/vue/")) {
    return "vue";
  }

  if (normalizedId.includes("/node_modules/tdesign-icons-vue-next/")) {
    return "tdesign-icons";
  }
  return undefined;
}

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
        manualChunks: resolveManualChunk,
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
