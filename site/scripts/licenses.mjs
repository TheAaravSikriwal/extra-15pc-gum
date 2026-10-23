// After the build: licenses.txt beside the site, with the license of every package the site's
// code can bundle (its dependencies and theirs, not the tools that build it), each with its own
// license file, and what else the site shows that isn't mine: FluidX3D's results and the turbo
// colormap. MIT, ISC, BSD and the fonts' OFL all ask for their notice to travel with copies.
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const LICENSE_FILE = /^(licen[cs]e|copying|notice)(\.|-|$)/i;

// where a package's folder is from the one that needs it: node's own lookup, upward
export function findPackage(name, from, root) {
  for (let dir = from; ; dir = dirname(dir)) {
    const here = join(dir, "node_modules", name);
    if (existsSync(join(here, "package.json"))) return here;
    if (resolve(dir) === resolve(root) || dirname(dir) === dir) return null;
  }
}

// every package the site's dependencies reach, each once
export function packagesOf(root) {
  const seen = new Map();
  const visit = (name, from) => {
    const dir = findPackage(name, from, root);
    if (!dir || seen.has(dir)) return;
    const pkg = JSON.parse(readFileSync(join(dir, "package.json"), "utf8"));
    seen.set(dir, { name: pkg.name ?? name, version: pkg.version ?? "", license: licenseOf(pkg), dir });
    for (const dep of Object.keys({ ...pkg.dependencies, ...pkg.optionalDependencies })) visit(dep, dir);
  };
  const top = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
  for (const dep of Object.keys(top.dependencies ?? {})) visit(dep, root);
  return [...seen.values()].sort((a, b) => a.name.localeCompare(b.name));
}

function licenseOf(pkg) {
  if (typeof pkg.license === "string") return pkg.license;
  if (pkg.license?.type) return pkg.license.type;
  if (Array.isArray(pkg.licenses)) return pkg.licenses.map((l) => l.type ?? l).join(" OR ");
  return "see its license file";
}

function licenseText(dir) {
  const files = readdirSync(dir).filter((f) => LICENSE_FILE.test(f));
  return files.map((f) => readFileSync(join(dir, f), "utf8").trim()).join("\n\n");
}

export const HEADER = `Third-party notices for the Extra 15pc Gum project site

The site's own code and data are mine, under GPL-3.0, from github.com/TheAaravSikriwal/extra-15pc-gum.
These aren't:

- The wind tunnel's pictures and flow come from my altered version of FluidX3D, published at
  github.com/TheAaravSikriwal/FluidX3D-extra-15pc-gum. FluidX3D is Dr. Moritz Lehmann's
  (github.com/ProjectPhysX/FluidX3D), under its own license: public research, education or
  personal use only, no commercial or military use.
- The turbo colormap the site colors flow and heat with is Google's (Copyright 2019 Google LLC,
  Apache-2.0), sampled from matplotlib's copy of it.
- The packages below are bundled into the site's scripts and fonts, each under its own license,
  given in full.
`;

export function notices(root) {
  const parts = [HEADER];
  for (const p of packagesOf(root)) {
    // a package without a license file is under the license its package names, whose text is SPDX's
    const text = licenseText(p.dir) || `No license file shipped. Its package says ${p.license}, whose text is at https://spdx.org/licenses/${p.license}.html`;
    parts.push(`\n${"-".repeat(76)}\n${p.name} ${p.version} (${p.license})\n\n${text}\n`);
  }
  return parts.join("");
}

function main() {
  const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
  const out = join(root, "dist", "licenses.txt");
  writeFileSync(out, notices(root));
  console.log(`dist: licenses.txt, ${packagesOf(root).length} packages`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
