// The TypeScript shapes against the JSON Schema pcs14 site --schema exports (site/schema).
import index from "../../schema/index.schema.json";
import { FIELDS, SCHEMA_VERSION } from "./types";

test("Index has the schema's fields", () => {
  expect(Object.keys(index.properties).sort()).toEqual([...FIELDS.Index].sort());
  expect([...index.required].sort()).toEqual(
    ["schema_version", "generated", "commit", "reports", "files"].sort(),
  );
});

test("ReportFound has the schema's fields", () => {
  expect(Object.keys(index.$defs.ReportFound.properties).sort()).toEqual(
    [...FIELDS.ReportFound].sort(),
  );
});

test("the version the site reads is the one pcs14 writes", () => {
  expect(SCHEMA_VERSION).toBe(1);
});
