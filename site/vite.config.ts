// The project site's build: a static folder with relative paths, so it opens from disk and
// drops into the portfolio wherever it ends up (docs/plans/2026-10-20-project-site.md).
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { outDir: "dist", assetsInlineLimit: 0 },
  test: { environment: "jsdom", globals: true, setupFiles: ["src/test-setup.ts"] },
});
