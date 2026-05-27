import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/demo/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/cases": "http://localhost:8000",
      "/scenarios": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
