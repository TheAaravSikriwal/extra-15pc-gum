// After the build: the site has to open from a folder on disk, so every link in the built page
// is relative, and the first load (the page, the scripts and styles it names, and the fonts it
// uses, not the data or the pages that load later) stays inside its budget. Fails otherwise.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const FIRST_LOAD_BUDGET_KB = 600; // set 2026-10-20 from the skeleton; revisited as pages land

export function absoluteLinks(html) {
  const found = [];
  for (const match of html.matchAll(/\s(?:src|href)="([^"]*)"/g)) {
    const link = match[1];
    if (link.startsWith("/") || /^[a-z]+:\/\//i.test(link)) found.push(link);
  }
  return found;
}

// the files the page itself names: its scripts and stylesheets
export function namedFiles(html) {
  return [...html.matchAll(/\s(?:src|href)="\.\/([^"]*\.(?:js|css))"/g)].map((m) => m[1]);
}

function main() {
  const dist = fileURLToPath(new URL("../dist/", import.meta.url));
  const html = readFileSync(join(dist, "index.html"), "utf8");
  const problems = absoluteLinks(html).map((link) => `not relative: ${link}`);
  const assets = readdirSync(join(dist, "assets"));
  const size = (name) => statSync(join(dist, name)).size;
  // a browser takes the woff2 of each font it needs; the woff files are for old ones
  const fonts = assets.filter((a) => a.endsWith(".woff2")).map((a) => `assets/${a}`);
  const first = [...namedFiles(html), ...fonts];
  const kb = (first.reduce((total, f) => total + size(f), 0) + Buffer.byteLength(html)) / 1024;
  if (kb > FIRST_LOAD_BUDGET_KB) {
    problems.push(`first load is ${kb.toFixed(0)} kB, over the ${FIRST_LOAD_BUDGET_KB} kB budget`);
  }
  const later = assets
    .filter((a) => a.endsWith(".js") && !first.includes(`assets/${a}`))
    .map((a) => `${a} ${(size(`assets/${a}`) / 1024).toFixed(0)} kB`);
  if (problems.length) {
    console.error(problems.join("\n"));
    process.exit(1);
  }
  console.log(`dist: relative links only, first load ${kb.toFixed(0)} of ${FIRST_LOAD_BUDGET_KB} kB`);
  if (later.length) console.log(`loaded later: ${later.join(", ")}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
