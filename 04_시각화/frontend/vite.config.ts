import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const port = Number(process.env.PORT) || 5173;

export default defineConfig({
  plugins: [vue()],
  server: {
    port,
    host: true,
    strictPort: false,
  },
  base: "./",
});
