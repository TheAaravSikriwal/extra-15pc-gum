// After the build: the site has to open from a folder on disk, so every link in the built page
// is relative, and the first load (the page, its scripts, styles and fonts, not the data) stays
// inside its budget. Fails the build otherwise.
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

function sizeOf(folder, skip) {
  let total = 0;
  for (const name of readdirSync(folder)) {
    const path = join(folder, name);
    if (skip(name)) continue;
    const info = statSync(path);
    total += info.isDirectory() ? sizeOf(path, () => false) : info.size;
  }
  return total;
}

function main() {
  const dist = fileURLToPath(new URL("../dist/", import.meta.url));
  const html = readFileSync(join(dist, "index.html"), "utf8");
  const problems = absoluteLinks(html).map((link) => `not relative: ${link}`);
  const kb = sizeOf(dist, (name) => name === "data") / 1024;
  if (kb > FIRST_LOAD_BUDGET_KB) {
    problems.push(`first load is ${kb.toFixed(0)} kB, over the ${FIRST_LOAD_BUDGET_KB} kB budget`);
  }
  if (problems.length) {
    console.error(problems.join("\n"));
    process.exit(1);
  }
  console.log(`dist: relative links only, first load ${kb.toFixed(0)} of ${FIRST_LOAD_BUDGET_KB} kB`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
