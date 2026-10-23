import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { exportSite, kept } from "./export-site.mjs";

test("the portfolio gets the site without the data's from-disk script copies", () => {
  expect(kept("assets/index-1.js")).toBe(true); // the site's own scripts
  expect(kept("data/spec.json")).toBe(true);
  expect(kept("data/spec.js")).toBe(false);
  expect(kept("data/tunnel/flow/max-cruise-slice.bin.js")).toBe(false);
  expect(kept("data/drone.glb.js")).toBe(false);
  expect(kept("licenses.txt")).toBe(true);
});

test("it copies into the portfolio's public/drone-app, and refuses any other folder", () => {
  const root = mkdtempSync(join(tmpdir(), "export-"));
  const dist = join(root, "dist");
  mkdirSync(join(dist, "data"), { recursive: true });
  writeFileSync(join(dist, "index.html"), "<html></html>");
  writeFileSync(join(dist, "data", "spec.json"), "{}");
  writeFileSync(join(dist, "data", "spec.js"), "x");
  const elsewhere = join(root, "elsewhere");
  mkdirSync(elsewhere);
  writeFileSync(join(elsewhere, "package.json"), JSON.stringify({ name: "something-else" }));
  expect(() => exportSite(dist, elsewhere)).toThrow(/isn't the portfolio/);
  const portfolio = join(root, "portfolio");
  mkdirSync(join(portfolio, "public", "drone-app"), { recursive: true });
  writeFileSync(join(portfolio, "package.json"), JSON.stringify({ name: "wearechintu" }));
  writeFileSync(join(portfolio, "public", "drone-app", "stale.json"), "{}"); // from an older export
  const done = exportSite(dist, portfolio);
  expect(done.files).toBe(2);
  expect(existsSync(join(portfolio, "public", "drone-app", "data", "spec.json"))).toBe(true);
  expect(existsSync(join(portfolio, "public", "drone-app", "data", "spec.js"))).toBe(false);
  expect(existsSync(join(portfolio, "public", "drone-app", "stale.json"))).toBe(false);
});
