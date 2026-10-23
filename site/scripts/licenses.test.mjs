import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { HEADER, notices, packagesOf } from "./licenses.mjs";

function made(root, dir, pkg, license) {
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "package.json"), JSON.stringify(pkg));
  if (license) writeFileSync(join(dir, "LICENSE"), license);
}

test("every package the site's dependencies reach, each once, with its license in full", () => {
  const root = mkdtempSync(join(tmpdir(), "licenses-"));
  made(root, root, { name: "site", dependencies: { a: "1", b: "1" }, devDependencies: { vitest: "1" } });
  made(root, join(root, "node_modules", "a"), { name: "a", version: "1.0.0", license: "MIT", dependencies: { c: "1" } }, "MIT text of a");
  made(root, join(root, "node_modules", "b"), { name: "b", version: "2.0.0", license: "ISC", dependencies: { c: "1" } }, "ISC text of b");
  // b needs its own c, nested under it
  made(root, join(root, "node_modules", "b", "node_modules", "c"), { name: "c", version: "3.0.0", license: "Apache-2.0" });
  made(root, join(root, "node_modules", "c"), { name: "c", version: "4.0.0", license: "MIT" }, "MIT text of c");
  made(root, join(root, "node_modules", "vitest"), { name: "vitest", license: "MIT" }, "not bundled");
  const found = packagesOf(root).map((p) => `${p.name} ${p.version}`);
  expect(found.sort()).toEqual(["a 1.0.0", "b 2.0.0", "c 3.0.0", "c 4.0.0"]); // the build's tools aren't in it
  const text = notices(root);
  expect(text.startsWith(HEADER)).toBe(true);
  expect(text).toContain("MIT text of a");
  expect(text).toContain("https://spdx.org/licenses/Apache-2.0.html"); // a package with no license file
  expect(text).not.toContain("not bundled");
  expect(HEADER).toContain("FluidX3D-extra-15pc-gum"); // the altered source, and FluidX3D's origin
  expect(HEADER).toContain("github.com/ProjectPhysX/FluidX3D");
});
