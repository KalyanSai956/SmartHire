import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import seo from "./vite-plugin-seo.js";

export default defineConfig({
  plugins: [react(), seo()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
});
