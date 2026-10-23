// The site for the portfolio: the built folder copied into wearechintu.com's repo at
// public/drone-app/, where it's framed at /drone. On the web the page fetches its data, so the
// script copies the data carries for a folder opened from disk (spec.js beside spec.json,
// x.bin.js, drone.glb.js) stay behind. Run it after the build, with the portfolio's folder in
// PORTFOLIO_DIR or as the first argument.
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const DEFAULT_PORTFOLIO = "D:/VisualStudioProjects/gitbuddywebsite";
export const APP_FOLDER = "drone-app";

// whether a built file goes to the portfolio: everything but the data's script copies
export function kept(path) {
  const parts = path.split(/[\\/]/);
  return !(parts[0] === "data" && path.endsWith(".js"));
}

function walk(dir, root = dir, out = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, root, out);
    else out.push(relative(root, full).split(sep).join("/"));
  }
  return out;
}

export function exportSite(dist, portfolio) {
  const pkg = join(portfolio, "package.json");
  if (!existsSync(pkg) || JSON.parse(readFileSync(pkg, "utf8")).name !== "wearechintu") {
    throw new Error(`${portfolio} isn't the portfolio's repo (its package.json is wearechintu's)`);
  }
  if (!existsSync(join(dist, "index.html"))) throw new Error("no build: npm run build first");
  const target = join(portfolio, "public", APP_FOLDER);
  rmSync(target, { recursive: true, force: true }); // only ever this one folder
  let bytes = 0;
  const files = walk(dist).filter(kept);
  for (const file of files) {
    const to = join(target, file);
    mkdirSync(dirname(to), { recursive: true });
    copyFileSync(join(dist, file), to);
    bytes += statSync(to).size;
  }
  return { target, files: files.length, bytes };
}

function main() {
  const dist = resolve(fileURLToPath(new URL("../dist", import.meta.url)));
  const portfolio = resolve(process.argv[2] ?? process.env.PORTFOLIO_DIR ?? DEFAULT_PORTFOLIO);
  const { target, files, bytes } = exportSite(dist, portfolio);
  console.log(`exported ${files} files, ${(bytes / 1e6).toFixed(1)} MB, to ${target}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
