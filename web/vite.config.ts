import { defineConfig } from "vite";

export default defineConfig({
  // Sample plots live above web/ because they are test data for the whole repo,
  // not front-end assets. Serving them as the public dir keeps the fetch simple.
  publicDir: "../samples",
  server: {
    port: 5173,
    // The Python service holds the fixture table and the photometrics.
    proxy: { "/api": { target: "http://localhost:8000", rewrite: p => p.replace(/^\/api/, "") } },
  },
});
