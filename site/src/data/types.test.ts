// The TypeScript shapes against the JSON Schema pcs14 site --schema exports (site/schema).
import flights from "../../schema/flights.schema.json";
import index from "../../schema/index.schema.json";
import parts from "../../schema/parts.schema.json";
import playback from "../../schema/playback.schema.json";
import spec from "../../schema/spec.schema.json";
import wires from "../../schema/wires.schema.json";
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

test("the spec sheet's shapes have the schema's fields", () => {
  expect(Object.keys(spec.properties).sort()).toEqual([...FIELDS.SpecSheet].sort());
  for (const name of ["Check", "Combination", "Part"] as const) {
    expect(Object.keys(spec.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
});

test("the parts' and wires' shapes have the schema's fields", () => {
  expect(Object.keys(parts.properties).sort()).toEqual([...FIELDS.Parts].sort());
  expect(Object.keys(parts.$defs.Piece.properties).sort()).toEqual([...FIELDS.Piece].sort());
  expect(Object.keys(wires.properties).sort()).toEqual([...FIELDS.Wires].sort());
  expect(Object.keys(wires.$defs.Route.properties).sort()).toEqual([...FIELDS.Route].sort());
  expect(Object.keys(wires.$defs.Wire.properties).sort()).toEqual([...FIELDS.Wire].sort());
});

test("the flights' shapes have the schema's fields", () => {
  expect(Object.keys(playback.properties).sort()).toEqual([...FIELDS.Playback].sort());
  expect(Object.keys(flights.properties).sort()).toEqual([...FIELDS.Flights].sort());
  expect(Object.keys(flights.$defs.Run.properties).sort()).toEqual([...FIELDS.Run].sort());
});

test("the version the site reads is the one pcs14 writes", () => {
  expect(SCHEMA_VERSION).toBe(1);
});
