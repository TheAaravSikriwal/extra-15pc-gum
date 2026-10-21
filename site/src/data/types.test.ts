// The TypeScript shapes against the JSON Schema pcs14 site --schema exports (site/schema).
import build from "../../schema/build.schema.json";
import catalog from "../../schema/catalog.schema.json";
import libraryPage from "../../schema/library-page.schema.json";
import library from "../../schema/library.schema.json";
import math from "../../schema/math.schema.json";
import rawData from "../../schema/raw-data.schema.json";
import raw from "../../schema/raw.schema.json";
import flights from "../../schema/flights.schema.json";
import index from "../../schema/index.schema.json";
import parts from "../../schema/parts.schema.json";
import playback from "../../schema/playback.schema.json";
import spec from "../../schema/spec.schema.json";
import steps from "../../schema/steps.schema.json";
import tunnel from "../../schema/tunnel.schema.json";
import unproven from "../../schema/unproven.schema.json";
import wiring from "../../schema/wiring.schema.json";
import wires from "../../schema/wires.schema.json";
import wires3d from "../../schema/wires3d.schema.json";
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

test("every wire in 3D has the schema's fields", () => {
  expect(Object.keys(wires3d.properties).sort()).toEqual([...FIELDS.Wires3d].sort());
  for (const name of ["Wire3d", "WireEnd3d", "PinSource"] as const) {
    expect(Object.keys(wires3d.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
});

test("the flights' shapes have the schema's fields", () => {
  expect(Object.keys(playback.properties).sort()).toEqual([...FIELDS.Playback].sort());
  expect(Object.keys(flights.properties).sort()).toEqual([...FIELDS.Flights].sort());
  expect(Object.keys(flights.$defs.Run.properties).sort()).toEqual([...FIELDS.Run].sort());
});

test("the steps' shapes have the schema's fields", () => {
  expect(Object.keys(steps.properties).sort()).toEqual([...FIELDS.Steps].sort());
  expect(Object.keys(steps.$defs.Step.properties).sort()).toEqual([...FIELDS.Step].sort());
});

test("the wind tunnel's shapes have the schema's fields", () => {
  expect(Object.keys(tunnel.properties).sort()).toEqual([...FIELDS.Tunnel].sort());
  for (const name of ["TunnelStill", "TunnelFrame", "TunnelCase"] as const) {
    expect(Object.keys(tunnel.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
});

test("the unproven list's shapes have the schema's fields", () => {
  expect(Object.keys(unproven.properties).sort()).toEqual([...FIELDS.Unproven].sort());
  expect(Object.keys(unproven.$defs.UnprovenGroup.properties).sort()).toEqual([...FIELDS.UnprovenGroup].sort());
  expect(Object.keys(unproven.$defs.UnprovenItem.properties).sort()).toEqual([...FIELDS.UnprovenItem].sort());
});

test("the wiring's shapes have the schema's fields", () => {
  expect(Object.keys(wiring.properties).sort()).toEqual([...FIELDS.Wiring].sort());
  for (const name of ["PinRow", "BoardPins", "Harness"] as const) {
    expect(Object.keys(wiring.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
});

test("the version the site reads is the one pcs14 writes", () => {
  expect(SCHEMA_VERSION).toBe(1);
});

test("the build package's shapes have the schema's fields", () => {
  expect(Object.keys(build.properties).sort()).toEqual([...FIELDS.Build].sort());
  for (const name of ["BuildLine", "BuildTotal", "BuildGuide"] as const) {
    expect(Object.keys(build.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
});

test("the library's, the catalog's, the raw data's and the math's shapes have the schema's fields", () => {
  expect(Object.keys(library.properties).sort()).toEqual([...FIELDS.Library].sort());
  for (const name of ["LibraryDoc", "LibrarySection"] as const) {
    expect(Object.keys(library.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
  expect(Object.keys(libraryPage.properties).sort()).toEqual([...FIELDS.LibraryPage].sort());
  expect(Object.keys(catalog.properties).sort()).toEqual([...FIELDS.Catalog].sort());
  expect(Object.keys(catalog.$defs.CatalogPart.properties).sort()).toEqual([...FIELDS.CatalogPart].sort());
  expect(Object.keys(raw.properties).sort()).toEqual([...FIELDS.RawIndex].sort());
  expect(Object.keys(raw.$defs.RawFile.properties).sort()).toEqual([...FIELDS.RawFile].sort());
  expect(Object.keys(rawData.properties).sort()).toEqual([...FIELDS.RawData].sort());
  expect(Object.keys(math.properties).sort()).toEqual([...FIELDS.Math].sort());
  for (const name of ["MathItem", "MathModule", "MathPackage"] as const) {
    expect(Object.keys(math.$defs[name].properties).sort()).toEqual([...FIELDS[name]].sort());
  }
});
