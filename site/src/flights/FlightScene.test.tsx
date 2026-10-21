import ReactThreeTestRenderer from "@react-three/test-renderer";
import * as THREE from "three";

import type { Piece, Playback } from "../data/types";
import { modulesOf } from "../explorer/logic";
import { nodeName } from "../explorer/Scene";
import { attitudeIn3, FlightScene } from "./FlightScene";

function run(firmware: string, north: number): Playback {
  return {
    schema_version: 1,
    scenario: "hover",
    setup: "base",
    firmware,
    passed: true,
    findings: [],
    t: [0, 10],
    position: [
      [0, 0, 0],
      [0, north, 10],
    ],
    attitude: [
      [0, 0, 0, 1],
      [0, 0, 0, 1],
    ],
    motors: [
      [0, 0, 0, 0],
      [560, 560, 560, 560],
    ],
    events: [],
  };
}

test("each drone sits where its log says at the clock's moment", async () => {
  const r = await ReactThreeTestRenderer.create(
    <FlightScene runs={[run("px4", 4), run("mine", 2)]} time={10} />,
  );
  const mine = r.scene.findByProps({ name: "drone mine" }).instance as THREE.Group;
  expect(mine.position.toArray()).toEqual([0, 10, -2]); // 10 m up, 2 m north (into the screen)
  const px4 = r.scene.findByProps({ name: "drone px4" }).instance as THREE.Group;
  expect(px4.position.z).toBe(-4);
});

test("once the CAD's model is in, each drone is the model, with only its setup's modules", async () => {
  expect(modulesOf("mission")).toEqual(["V", "P"]);
  const root = new THREE.Group();
  const pieces = new Map<string, Piece>();
  for (const [name, module] of [["frame", "base"], ["ark-gps", "V"]]) {
    const node = new THREE.Group();
    node.name = nodeName(name);
    node.add(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.02, 0.02)));
    root.add(node);
    pieces.set(name, { name, kind: "bought", module, mass_g: 10, part_id: null, moving: false, catalog: null });
  }
  const r = await ReactThreeTestRenderer.create(
    <FlightScene runs={[run("mine", 2)]} time={10} model={{ root, pieces }} />,
  );
  // through three.js's own scene graph: the test renderer's tree doesn't walk into a primitive
  const drone = (r.scene.instance as THREE.Object3D).getObjectByName("drone mine") as THREE.Group;
  expect(drone.getObjectByName("stand-in")).toBeUndefined();
  expect(drone.getObjectByName("frame")?.visible).toBe(true);
  expect(drone.getObjectByName("ark-gps")?.visible).toBe(false); // base has no V
  const mesh = drone.getObjectByName("frame")!.children[0] as THREE.Mesh;
  expect((mesh.material as THREE.MeshStandardMaterial).color.getHexString()).toBe("3ddc97");
  expect(root.getObjectByName("ark-gps")?.visible).toBe(true); // the explorer's copy untouched
});

test("a level drone facing east stays level in three.js, and a turn about up stays about up", () => {
  const level = attitudeIn3([0, 0, 0, 1]);
  expect(level.angleTo(new THREE.Quaternion())).toBeCloseTo(0);
  // a quarter turn to the left (about east-north-up's z) is a quarter turn about three.js's y
  const s = Math.SQRT1_2;
  const turned = attitudeIn3([0, 0, s, s]);
  const forward = new THREE.Vector3(1, 0, 0).applyQuaternion(turned);
  expect(forward.x).toBeCloseTo(0);
  expect(forward.z).toBeCloseTo(-1); // now facing north
});
