import ReactThreeTestRenderer from "@react-three/test-renderer";
import { render, screen } from "@testing-library/react";
import * as THREE from "three";

import type { Piece, Route } from "../data/types";
import { Card } from "./Card";
import { propSpin } from "./logic";
import { DroneScene, nodeName, pieceOf } from "./Scene";

function piece(name: string, module: string, kind = "bought"): Piece {
  return { name, kind, module, mass_g: 12.5, part_id: null, moving: false, catalog: null };
}

function model() {
  const root = new THREE.Group();
  for (const [name, x] of [["frame", 0], ["fruity-chutes-harrier", 0.1], ["wire battery leads", -0.1]] as const) {
    const node = new THREE.Group();
    node.name = nodeName(name); // as three.js's GLTFLoader names it
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.02, 0.02));
    node.add(mesh);
    node.position.set(x, 0, 0);
    root.add(node);
  }
  return root;
}

const PIECES = new Map([
  ["frame", piece("frame", "base", "frame")],
  ["fruity-chutes-harrier", piece("fruity-chutes-harrier", "P")],
  ["wire battery leads", piece("wire battery leads", "base", "wire")],
]);
const ROUTE: Route = {
  name: "battery leads",
  node: "wire battery leads",
  wires: [{ label: "a to b", ends: ["lead.XT60.+", "esc.BAT.VBAT"] }],
  heating_share: { max: { burst: 0.31 } },
};

async function scene(modulesOn: string[], explode = 0, selected: string | null = null, heat = true) {
  const root = model();
  await ReactThreeTestRenderer.create(
    <DroneScene
      root={root}
      pieces={PIECES}
      routes={new Map([["wire battery leads", ROUTE]])}
      modulesOn={new Set(modulesOn)}
      explode={explode}
      selected={selected}
      combination="max"
      kase="burst"
      heat={heat}
      onSelect={() => {}}
    />,
  );
  return root;
}

test("a module switched off hides its pieces, and Base always shows", async () => {
  const off = await scene([]);
  expect(off.getObjectByName("frame")?.visible).toBe(true);
  expect(off.getObjectByName("fruity-chutes-harrier")?.visible).toBe(false);
  const on = await scene(["P"]);
  expect(on.getObjectByName("fruity-chutes-harrier")?.visible).toBe(true);
  expect(nodeName("wire battery leads")).toBe("wire_battery_leads");
});

test("the exploded view moves pieces out from the middle", async () => {
  const root = await scene(["P"], 1);
  expect(root.getObjectByName("fruity-chutes-harrier")!.position.x).toBeGreaterThan(0.1);
  expect(root.getObjectByName("wire_battery_leads")!.position.x).toBeLessThan(-0.1);
});

test("the exploded view moves pieces out in the world, under a parent that turns z-up into y-up", async () => {
  // the CAD's GLB: its pieces sit under one node that turns the CAD's z-up into glTF's y-up
  const root = new THREE.Group();
  const turn = new THREE.Group();
  turn.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2);
  root.add(turn);
  for (const [name, z] of [["frame", 0], ["fruity-chutes-harrier", 0.1]] as const) {
    const node = new THREE.Group();
    node.name = nodeName(name);
    node.add(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.02, 0.02)));
    node.position.set(0, 0, z); // the chute above the frame, in the CAD's frame
    turn.add(node);
  }
  await ReactThreeTestRenderer.create(
    <DroneScene root={root} pieces={PIECES} routes={new Map()} modulesOn={new Set(["P"])} explode={1}
      selected={null} combination="max" kase="hover" onSelect={() => {}} />,
  );
  const chute = root.getObjectByName("fruity-chutes-harrier")!.getWorldPosition(new THREE.Vector3());
  expect(chute.y).toBeGreaterThan(0.1); // further up, not off to the side
  expect(Math.abs(chute.z)).toBeLessThan(1e-6);
});

test("the props spin the way PX4's quad X turns them, each about its own hub", async () => {
  expect([propSpin("prop front right"), propSpin("prop back left")]).toEqual([1, 1]);
  expect([propSpin("prop front left"), propSpin("prop back right")]).toEqual([-1, -1]);
  expect(propSpin("frame")).toBe(0);
  const root = new THREE.Group();
  const pieces = new Map<string, Piece>();
  for (const name of ["prop front left", "prop front right", "frame"]) {
    const node = new THREE.Group();
    node.name = nodeName(name);
    node.add(new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.01, 0.02)));
    node.position.set(name === "frame" ? 0 : 0.15, 0, 0.04);
    root.add(node);
    pieces.set(name, piece(name, "base", name === "frame" ? "frame" : "prop"));
  }
  const renderer = await ReactThreeTestRenderer.create(
    <DroneScene root={root} pieces={pieces} routes={new Map()} modulesOn={new Set()} explode={0}
      selected={null} combination="max" kase="hover" onSelect={() => {}} spin={2} />,
  );
  await ReactThreeTestRenderer.act(async () => renderer.advanceFrames(10, 0.1));
  const left = root.getObjectByName(nodeName("prop front left"))!;
  const right = root.getObjectByName(nodeName("prop front right"))!;
  expect(left.rotation.z).toBeLessThan(-0.5); // clockwise seen from above
  expect(right.rotation.z).toBeGreaterThan(0.5);
  expect(right.position.x).toBeCloseTo(0.15); // turning in place, on its hub
  expect(root.getObjectByName("frame")!.rotation.z).toBe(0);
});

test("in flight each prop turns at its own motor's speed, and a stopped one stays still", async () => {
  const root = new THREE.Group();
  const pieces = new Map<string, Piece>();
  for (const name of ["prop front left", "prop front right"]) {
    const node = new THREE.Group();
    node.name = nodeName(name);
    node.add(new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.01, 0.02)));
    root.add(node);
    pieces.set(name, piece(name, "base", "prop"));
  }
  const spins = { current: { "prop front left": 10, "prop front right": 0 } };
  const renderer = await ReactThreeTestRenderer.create(
    <DroneScene root={root} pieces={pieces} routes={new Map()} modulesOn={new Set()} explode={0}
      selected={null} combination="max" kase="hover" onSelect={() => {}} spin={2} spins={spins} />,
  );
  await ReactThreeTestRenderer.act(async () => renderer.advanceFrames(10, 0.1));
  expect(Math.abs(root.getObjectByName(nodeName("prop front left"))!.rotation.z)).toBeGreaterThan(5);
  expect(root.getObjectByName(nodeName("prop front right"))!.rotation.z).toBe(0);
});

test("the picked piece lights up in spearmint, and a wire takes its heating color", async () => {
  const root = await scene([], 0, "frame");
  const mesh = root.getObjectByName("frame")!.children[0] as THREE.Mesh;
  expect((mesh.material as THREE.MeshStandardMaterial).color.getHexString()).toBe("3ddc97");
  const wire = root.getObjectByName("wire_battery_leads")!.children[0] as THREE.Mesh;
  const color = (wire.material as THREE.MeshStandardMaterial).color.getHexString();
  expect(color).not.toBe("3ddc97"); // 31% of its limit: on the way to magenta
  expect(color).not.toBe("4a4a47");
});

test("without the heating, each piece wears what it's made of", async () => {
  const root = await scene([], 0, null, false);
  const wire = root.getObjectByName("wire_battery_leads")!.children[0] as THREE.Mesh;
  expect((wire.material as THREE.MeshStandardMaterial).color.getHexString()).toBe("c0302a"); // power red
});

test("a click on a mesh picks the piece it belongs to, by the piece's own name", () => {
  const root = model();
  const byNode = new Map([...PIECES.keys()].map((n) => [nodeName(n), n]));
  const mesh = root.getObjectByName("wire_battery_leads")!.children[0];
  expect(pieceOf(mesh, byNode)).toBe("wire battery leads");
  expect(pieceOf(root, byNode)).toBeNull();
});

test("a wire's card names both ends of every wire in it", () => {
  render(<Card piece={PIECES.get("wire battery leads")!} route={ROUTE} combination="max" kase="burst" />);
  expect(screen.getByText("lead.XT60.+ to esc.BAT.VBAT")).toBeInTheDocument();
  expect(screen.getByText(/31% of its heating limit in max, burst/)).toBeInTheDocument();
});

test("a board's card links to its pins", () => {
  render(<Card piece={PIECES.get("frame")!} route={null} combination="max" kase="hover" boards={["fc"]} />);
  expect(screen.getByRole("link", { name: "Its pins" })).toHaveAttribute("href", "#/wiring/fc");
});

test("nothing picked, the card says what to do", () => {
  render(<Card piece={null} route={null} combination="max" kase="hover" />);
  expect(screen.getByText("Click any part of the drone.")).toBeInTheDocument();
});

test("given every wire, it draws each one in place of the bundled route", async () => {
  const root = model();
  const wire = {
    label: "lead.XT60.+ to esc.BAT.VBAT",
    harness: "main power",
    ends: [
      { pin: "lead.XT60.+", at_mm: [0, 0, 0], piece: "frame" },
      { pin: "esc.BAT.VBAT", at_mm: [100, 0, 0], piece: "fruity-chutes-harrier" },
    ],
    route: "battery leads",
    route_piece: "wire battery leads",
    path_mm: [[50, 0, 10]],
    awg: 12,
    diameter_mm: 3.4,
    wire: "silicone",
    role: "power",
    length_mm: 110,
    gaps_mm: [],
  };
  await ReactThreeTestRenderer.create(
    <DroneScene root={root} pieces={PIECES} routes={new Map()} modulesOn={new Set(["P"])} explode={0}
      selected={null} combination="max" kase="hover" onSelect={() => {}} wires={[wire]} />,
  );
  const drawn = root.getObjectByName("wires3d")!;
  expect(drawn.children).toHaveLength(1);
  expect(drawn.children[0].userData.wire).toBe("lead.XT60.+ to esc.BAT.VBAT");
  expect(root.getObjectByName("wire_battery_leads")!.visible).toBe(false);
});
