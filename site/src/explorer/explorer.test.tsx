import ReactThreeTestRenderer from "@react-three/test-renderer";
import { render, screen } from "@testing-library/react";
import * as THREE from "three";

import type { Piece, Route } from "../data/types";
import { Card } from "./Card";
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

async function scene(modulesOn: string[], explode = 0, selected: string | null = null) {
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

test("the picked piece lights up in spearmint, and a wire takes its heating color", async () => {
  const root = await scene([], 0, "frame");
  const mesh = root.getObjectByName("frame")!.children[0] as THREE.Mesh;
  expect((mesh.material as THREE.MeshStandardMaterial).color.getHexString()).toBe("3ddc97");
  const wire = root.getObjectByName("wire_battery_leads")!.children[0] as THREE.Mesh;
  const color = (wire.material as THREE.MeshStandardMaterial).color.getHexString();
  expect(color).not.toBe("3ddc97"); // 31% of its limit: on the way to magenta
  expect(color).not.toBe("4a4a47");
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

test("nothing picked, the card says what to do", () => {
  render(<Card piece={null} route={null} combination="max" kase="hover" />);
  expect(screen.getByText("Click any part of the drone.")).toBeInTheDocument();
});
