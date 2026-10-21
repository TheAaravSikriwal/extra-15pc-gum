import * as THREE from "three";

import type { Piece } from "../data/types";
import { lookFor, materialFor, planarUVs } from "./materials";

function piece(kind: string, part_id: string | null, name = "x"): Piece {
  return { name, kind, module: "base", mass_g: 1, part_id, moving: false, catalog: null } as unknown as Piece;
}

test("each kind of piece looks like what it's made of", () => {
  expect(lookFor(piece("frame", "iflight-nazgul-xl10-v6")).texture).toBe("carbon");
  const motor = lookFor(piece("motor", "emax-e3-2814-850kv"));
  expect(motor.metalness).toBeGreaterThan(0.6); // an anodized bell
  expect(lookFor(piece("prop", "gemfan-1050x3")).metalness).toBe(0);
  expect(lookFor(piece("pack", "molicel-p45b")).roughness).toBeGreaterThan(0.6); // its wrap
});

test("boards take their maker's solder mask, and printed parts their filament", () => {
  expect(lookFor(piece("bought", "pjrc-teensy-41")).color).toBe("#1f6b3a"); // Teensy green
  expect(lookFor(piece("bought", "rpi-5-4gb")).color).toBe("#2c7a3a");
  expect(lookFor(piece("bought", "safety-monitor-buffers")).color).toBe("#b3262b"); // SparkFun red
  expect(lookFor(piece("printed", "landing-legs")).color).toBe(lookFor(piece("printed", "gps-mast")).color); // TPU
  expect(lookFor(piece("printed", "battery-tray")).color).not.toBe(lookFor(piece("printed", "landing-legs")).color);
  expect(lookFor(piece("bought", "something-new")).color).toBeTruthy(); // anything else still gets a look
});

test("wires wear their insulation: red for power, black motor leads, light signal", () => {
  const power = lookFor(piece("wire", null, "wire battery leads")).color;
  expect(lookFor(piece("wire", null, "wire module power to V")).color).toBe(power);
  expect(power).toBe("#c0302a");
  expect(lookFor(piece("wire", null, "wire motor leads front left")).color).toBe("#1a1a1a");
  expect(lookFor(piece("wire", null, "wire gps")).color).not.toBe(power);
});

test("one material per look, made once", () => {
  const a = materialFor(lookFor(piece("motor", "emax-e3-2814-850kv")));
  const b = materialFor(lookFor(piece("motor", "emax-e3-2814-850kv")));
  expect(a).toBe(b);
  expect(a).toBeInstanceOf(THREE.MeshPhysicalMaterial);
});

test("a mesh without texture coordinates gets them from its faces' directions", () => {
  const g = new THREE.BoxGeometry(0.1, 0.02, 0.05);
  g.deleteAttribute("uv");
  planarUVs(g, 0.01);
  const uv = g.getAttribute("uv");
  expect(uv.count).toBe(g.getAttribute("position").count);
  // a face 0.1 m across spans 10 tiles at 1 cm a tile
  let lo = Infinity;
  let hi = -Infinity;
  for (let k = 0; k < uv.count; k++) {
    lo = Math.min(lo, uv.getX(k));
    hi = Math.max(hi, uv.getX(k));
  }
  expect(hi - lo).toBeCloseTo(10, 5);
});
