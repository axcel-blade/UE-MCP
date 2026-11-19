import { defineConfig } from "astro/config";

// GitHub Pages defaults; override with ASTRO_SITE / ASTRO_BASE (e.g. Docker).
const site = process.env.ASTRO_SITE || "https://axcel-blade.github.io";
const base = process.env.ASTRO_BASE || "/UE-MCP";

export default defineConfig({
  site,
  base,
  trailingSlash: "ignore",
  build: {
    format: "directory",
  },
});
