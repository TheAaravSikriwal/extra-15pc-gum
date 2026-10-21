// The CAD's GLB thinned for the browser with gltfpack (meshoptimizer's, MIT), into the data
// folder next to pcs14 site's files. The pieces keep their names (-kn), because parts.json
// matches them up by name; the meshes are simplified and quantized.
import { execFileSync } from "node:child_process";
import { mkdirSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const from = fileURLToPath(new URL("../../outputs/cad/drone.glb", import.meta.url));
const to = fileURLToPath(new URL("../public/data/drone.glb", import.meta.url));
mkdirSync(fileURLToPath(new URL("../public/data/", import.meta.url)), { recursive: true });
const simplify = process.env.GLB_SIMPLIFY ?? "0.5";
// gltfpack's own script, run by this node: no shell, so nothing gets re-quoted on Windows
const cli = createRequire(import.meta.url).resolve("gltfpack/cli.js");
execFileSync(process.execPath, [cli, "-i", from, "-o", to, "-kn", "-si", simplify], {
  stdio: "inherit",
});
const kb = (file) => (statSync(file).size / 1024).toFixed(0);
console.log(`drone.glb: ${kb(from)} kB from the CAD, ${kb(to)} kB thinned (simplify ${simplify})`);
