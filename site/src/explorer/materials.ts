// What each piece is made of, as three.js materials: the frame's carbon weave, the motors'
// anodized bells, each board's solder mask in its maker's color, the printed parts in their
// filament, the pack in its wrap. Textures are drawn in code (nothing downloaded), and meshes
// the CAD exported without texture coordinates get them from their faces' directions.
import * as THREE from "three";

import type { Piece } from "../data/types";

export interface Look {
  key: string;
  color: string;
  metalness: number;
  roughness: number;
  clearcoat?: number;
  texture?: "carbon" | "board" | null;
}

const BOARD = { metalness: 0.15, roughness: 0.45, clearcoat: 0.4, texture: "board" as const };

// solder masks and housings by part: the makers' own colors
const PARTS: Record<string, Partial<Look>> = {
  "ark-fpv": { ...BOARD, color: "#141414" },
  "ark-gps": { color: "#1b1b1b", metalness: 0.1, roughness: 0.35, clearcoat: 0.6 },
  "ark-cannode": { ...BOARD, color: "#141414" },
  "holybro-tekko32-f4-50a": { ...BOARD, color: "#161616" },
  "pjrc-teensy-41": { ...BOARD, color: "#1f6b3a" },
  "rpi-5-4gb": { ...BOARD, color: "#2c7a3a" },
  "rpi-camera-module-3": { ...BOARD, color: "#2c7a3a" },
  "rpi-active-cooler": { color: "#9a9a96", metalness: 0.85, roughness: 0.3 },
  "heltec-ht-hc01p": { ...BOARD, color: "#151515" },
  "adafruit-lsm6dsox": { ...BOARD, color: "#141414" },
  "adafruit-lm66200": { ...BOARD, color: "#141414" },
  "safety-monitor-buffers": { ...BOARD, color: "#b3262b" },
  "bat54c-on-adapter": { ...BOARD, color: "#b3262b" },
  "p-chute-switch": { ...BOARD, color: "#b3262b" },
  "cjmcu-5018": { ...BOARD, color: "#1d4f91" },
  "pololu-d36v6f3": { ...BOARD, color: "#1d5d3a" },
  "radiomaster-rp2-v2": { color: "#1c1c1c", metalness: 0.05, roughness: 0.6 },
  "matek-bec12s-pro": { color: "#202020", metalness: 0.05, roughness: 0.7 },
  "benewake-tf-luna": { color: "#222222", metalness: 0.05, roughness: 0.4, clearcoat: 0.5 },
  "ruko-r111": { color: "#2a2a2a", metalness: 0.05, roughness: 0.5 },
  "fruity-chutes-harrier-40-42": { color: "#d9531e", metalness: 0.1, roughness: 0.5, clearcoat: 0.3 },
  "halow-antenna-915": { color: "#111111", metalness: 0, roughness: 0.6 },
  "module-socket": { color: "#e6c229", metalness: 0, roughness: 0.55 }, // XT30's yellow
  "module-plug": { color: "#e6c229", metalness: 0, roughness: 0.55 },
  "branch-fuses": { color: "#8a4fbf", metalness: 0, roughness: 0.4 }, // a 3 A MINI's violet
  "claws-placeholder": { color: "#6b6b66", metalness: 0.3, roughness: 0.6 },
  // the printed parts: natural TPU where they flex, carbon-filled PETG for the rest (spearmint
  // is kept for whatever is picked)
  "landing-legs": { color: "#d9d7cf", metalness: 0, roughness: 0.85 },
  "gps-mast": { color: "#d9d7cf", metalness: 0, roughness: 0.85 },
  "remote-id-mount": { color: "#d9d7cf", metalness: 0, roughness: 0.85 },
}

const KINDS: Record<string, Omit<Look, "key">> = {
  frame: { color: "#1d1d1f", metalness: 0.25, roughness: 0.42, clearcoat: 0.7, texture: "carbon" },
  motor: { color: "#3a3d42", metalness: 0.75, roughness: 0.32 },
  prop: { color: "#1a1a1a", metalness: 0, roughness: 0.48, clearcoat: 0.2 },
  pack: { color: "#2b4a6f", metalness: 0, roughness: 0.7 }, // blue PVC wrap
  printed: { color: "#2e2e2e", metalness: 0, roughness: 0.9 }, // PETG-CF's matte charcoal
  bought: { color: "#3c3c3a", metalness: 0.1, roughness: 0.55 },
  wire: { color: "#1a1a1a", metalness: 0, roughness: 0.6 }, // black silicone
};

// a wire's insulation by what it carries: red for power, black silicone for the motor leads,
// white for the camera's ribbon, light gray for signal
const POWER = /battery|feed|power|supply|bec/;

function wireColor(name: string): string {
  if (/motor leads/.test(name)) return "#1a1a1a";
  if (POWER.test(name)) return "#c0302a";
  if (/camera cable/.test(name)) return "#e9e5d8";
  return "#cfccc3";
}

// the named parts of a piece's look (pcs14.cad.looks): the chips, plugs and pins on a board,
// a motor's gap over its windings and its shaft, a lens's glass, the chute's anodized cap, the
// pack's nickel, a shield can, the cooler's fan, heat shrink, the frame's screws and standoffs.
// The board, the bell and anything else (a look's "body") keep the piece's own look
const SUBPARTS: Record<string, Omit<Look, "key">> = {
  chips: { color: "#141414", metalness: 0.1, roughness: 0.55, texture: null }, // black epoxy
  plugs: { color: "#e6dfcc", metalness: 0, roughness: 0.6, texture: null }, // JST's off-white nylon
  pins: { color: "#c9a13b", metalness: 0.9, roughness: 0.3, texture: null }, // gold plating
  antenna: { color: "#d9d2bf", metalness: 0.1, roughness: 0.45, clearcoat: 0.3, texture: null }, // ceramic
  gap: { color: "#a8642a", metalness: 0.6, roughness: 0.4, texture: null }, // copper windings
  shaft: { color: "#b8b8b4", metalness: 0.9, roughness: 0.25, texture: null }, // steel
  base: { color: "#2a2b2e", metalness: 0.7, roughness: 0.4, texture: null },
  lens: { color: "#0b0d10", metalness: 0.3, roughness: 0.06, clearcoat: 1, texture: null }, // glass
  cap: { color: "#1b1b1c", metalness: 0.55, roughness: 0.38, texture: null }, // black anodized
  nickel: { color: "#c9c8c1", metalness: 0.9, roughness: 0.32, texture: null },
  shield: { color: "#b9b9b3", metalness: 0.85, roughness: 0.3, texture: null }, // a tin-plated can
  fan: { color: "#161616", metalness: 0, roughness: 0.55, texture: null },
  sleeve: { color: "#121212", metalness: 0, roughness: 0.75, texture: null }, // heat shrink
  screws: { color: "#2b2b2e", metalness: 0.8, roughness: 0.35, texture: null }, // black oxide
  standoff: { color: "#3a3b3f", metalness: 0.8, roughness: 0.35, texture: null }, // aluminum
};

export const SUBPART_NAMES = new Set([...Object.keys(SUBPARTS), "board", "bell"]);

export function lookFor(piece: Piece, subpart?: string | null): Look {
  const base = piece.kind === "wire" ? { ...KINDS.wire, color: wireColor(piece.name) } : (KINDS[piece.kind] ?? KINDS.bought);
  const part = (piece.part_id && PARTS[piece.part_id]) || {};
  const own = subpart ? SUBPARTS[subpart] : undefined;
  const look = (own ? { ...own } : { texture: null, ...base, ...part }) as Omit<Look, "key">;
  const key = [look.color, look.metalness, look.roughness, look.clearcoat ?? 0, look.texture ?? ""].join("|");
  return { ...look, key };
}

// a 2x2 twill, the weave on most carbon plate, drawn once
function carbonCanvas(): HTMLCanvasElement | null {
  if (typeof document === "undefined") return null;
  const size = 64;
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  if (!g) return null;
  const tow = size / 4;
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      const over = (i + j) % 4 < 2; // the twill's diagonal steps
      const grad = over
        ? g.createLinearGradient(i * tow, 0, (i + 1) * tow, 0)
        : g.createLinearGradient(0, j * tow, 0, (j + 1) * tow);
      grad.addColorStop(0, "#202023");
      grad.addColorStop(0.5, over ? "#3a3a3f" : "#2c2c30");
      grad.addColorStop(1, "#202023");
      g.fillStyle = grad;
      g.fillRect(i * tow, j * tow, tow, tow);
    }
  }
  return c;
}

// a board's surface: its mask with traces, pads and a few chips, light enough to tint
function boardCanvas(): HTMLCanvasElement | null {
  if (typeof document === "undefined") return null;
  const size = 128;
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  if (!g) return null;
  g.fillStyle = "#ffffff";
  g.fillRect(0, 0, size, size);
  g.strokeStyle = "rgba(0,0,0,0.12)";
  g.lineWidth = 1;
  for (let k = 0; k < 14; k++) {
    const y = 8 + k * 8.5;
    g.beginPath();
    g.moveTo(6, y);
    g.lineTo(40 + ((k * 37) % 60), y);
    g.lineTo(52 + ((k * 37) % 60), y + 6);
    g.lineTo(122, y + 6);
    g.stroke();
  }
  g.fillStyle = "#c9a13b"; // gold pads
  for (let k = 0; k < 16; k++) g.fillRect(4 + k * 7.6, 2, 3, 4);
  for (let k = 0; k < 16; k++) g.fillRect(4 + k * 7.6, size - 6, 3, 4);
  g.fillStyle = "#101010"; // chips
  g.fillRect(30, 34, 28, 28);
  g.fillRect(74, 70, 20, 14);
  g.fillRect(84, 30, 12, 12);
  return c;
}

const textures = new Map<string, THREE.Texture | null>();

function texture(kind: "carbon" | "board"): THREE.Texture | null {
  if (!textures.has(kind)) {
    const canvas = kind === "carbon" ? carbonCanvas() : boardCanvas();
    const t = canvas ? new THREE.CanvasTexture(canvas) : null;
    if (t) {
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.colorSpace = THREE.SRGBColorSpace;
    }
    textures.set(kind, t);
  }
  return textures.get(kind) ?? null;
}

const materials = new Map<string, THREE.MeshPhysicalMaterial>();

export function materialFor(look: Look): THREE.MeshPhysicalMaterial {
  let m = materials.get(look.key);
  if (!m) {
    const map = look.texture ? texture(look.texture) : null;
    m = new THREE.MeshPhysicalMaterial({
      // a textured look's color tints the texture; the carbon's is already dark
      color: look.texture === "carbon" ? "#ffffff" : look.color,
      metalness: look.metalness,
      roughness: look.roughness,
      clearcoat: look.clearcoat ?? 0,
      clearcoatRoughness: 0.3,
      map,
    });
    materials.set(look.key, m);
  }
  return m;
}

// how far one copy of each texture spans, in meters: the twill's tows about 2 mm wide, a board's
// pattern about 3 cm
export const TILE = { carbon: 0.008, board: 0.03 };

// the selected piece, lit in spearmint whatever it's made of
export const SELECTED = new THREE.MeshPhysicalMaterial({ color: "#3ddc97", emissive: "#123d2a", roughness: 0.4 });

// a lit wire glows a little, so it reads out of its bundle and against the boards
export const LIT_WIRE = new THREE.MeshPhysicalMaterial({
  color: "#3ddc97",
  emissive: "#3ddc97",
  emissiveIntensity: 0.45,
  roughness: 0.4,
});

const insulations = new Map<string, THREE.MeshPhysicalMaterial>();

// a wire's silicone insulation in its color: soft, a little sheen
export function wireMaterial(color: string): THREE.MeshPhysicalMaterial {
  let m = insulations.get(color);
  if (!m) {
    m = new THREE.MeshPhysicalMaterial({ color, roughness: 0.55, clearcoat: 0.15 });
    insulations.set(color, m);
  }
  return m;
}

const faded = new Map<string, THREE.MeshPhysicalMaterial>();

const ghosts = new Map<string, THREE.MeshPhysicalMaterial>();

// a piece faded to a ghost while a wire is picked, so the wire and its pins show through it
export function ghostMaterial(look: Look): THREE.MeshPhysicalMaterial {
  let m = ghosts.get(look.key);
  if (!m) {
    m = new THREE.MeshPhysicalMaterial({
      color: look.color,
      roughness: 0.8,
      transparent: true,
      opacity: 0.12,
      depthWrite: false,
    });
    ghosts.set(look.key, m);
  }
  return m;
}

// a wire faded back while something else is picked
export function dimWireMaterial(color: string): THREE.MeshPhysicalMaterial {
  let m = faded.get(color);
  if (!m) {
    m = new THREE.MeshPhysicalMaterial({ color, roughness: 0.6, transparent: true, opacity: 0.15, depthWrite: false });
    faded.set(color, m);
  }
  return m;
}

const heats = new Map<string, THREE.MeshPhysicalMaterial>();

// a wire colored by its heating, for when that's what's being shown
export function heatMaterial(color: string): THREE.MeshPhysicalMaterial {
  let m = heats.get(color);
  if (!m) {
    m = new THREE.MeshPhysicalMaterial({ color, roughness: 0.5 });
    heats.set(color, m);
  }
  return m;
}

// texture coordinates from each triangle's direction, so a texture tiles at `tile` (in the
// mesh's own units) on every face: the CAD's meshes come without any
export function planarUVs(geometry: THREE.BufferGeometry, tile: number): void {
  const pos = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal") ?? (geometry.computeVertexNormals(), geometry.getAttribute("normal"));
  const uv = new Float32Array(pos.count * 2);
  for (let k = 0; k < pos.count; k++) {
    const nx = Math.abs(normal.getX(k));
    const ny = Math.abs(normal.getY(k));
    const nz = Math.abs(normal.getZ(k));
    const [a, b] =
      nx >= ny && nx >= nz ? [pos.getY(k), pos.getZ(k)] : ny >= nz ? [pos.getX(k), pos.getZ(k)] : [pos.getX(k), pos.getY(k)];
    uv[2 * k] = a / tile;
    uv[2 * k + 1] = b / tile;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}
