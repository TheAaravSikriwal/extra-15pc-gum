import type { Wire3d } from "../data/types";
import { easeInOut, focusOf, harnessesOf, wireStates } from "./explore";

function wire(label: string, harness: string, a: string, b: string): Wire3d {
  return {
    label,
    harness,
    ends: [
      { pin: `${a}.J1.1`, at_mm: [10, 0, 0], piece: a },
      { pin: `${b}.J1.1`, at_mm: [90, 0, 0], piece: b },
    ],
    route: null,
    route_piece: null,
    path_mm: [],
    awg: 26,
    diameter_mm: 1.1,
    wire: "silicone",
    role: "signal",
    length_mm: 80,
    gaps_mm: [],
  };
}

const WIRES = [wire("rx", "receiver", "fc", "rx"), wire("lidar", "lidar", "fc", "lidar"), wire("esc", "esc cable", "esc", "cut")];

test("nothing picked: every wire as it is", () => {
  const states = wireStates(WIRES, {});
  expect([...states.values()]).toEqual(["normal", "normal", "normal"]);
});

test("a board picked lights its own wires and fades the rest", () => {
  const states = wireStates(WIRES, { piece: "fc" });
  expect(states.get("rx")).toBe("lit");
  expect(states.get("lidar")).toBe("lit");
  expect(states.get("esc")).toBe("dim");
});

test("a wire picked is the only one lit, and a harness isolates its own", () => {
  expect(wireStates(WIRES, { wire: "lidar", piece: "fc" }).get("rx")).toBe("dim");
  expect(wireStates(WIRES, { wire: "lidar" }).get("lidar")).toBe("lit");
  const harness = wireStates(WIRES, { harness: "esc cable" });
  expect(harness.get("esc")).toBe("normal");
  expect(harness.get("rx")).toBe("hidden");
});

test("the harnesses, each once, in the connection list's order", () => {
  expect(harnessesOf(WIRES)).toEqual(["receiver", "lidar", "esc cable"]);
});

test("the glide starts and stops gently, and gets there", () => {
  expect(easeInOut(0)).toBe(0);
  expect(easeInOut(1)).toBe(1);
  expect(easeInOut(0.5)).toBeCloseTo(0.5);
  expect(easeInOut(0.1)).toBeLessThan(0.1); // slow off the mark
  expect(easeInOut(2)).toBe(1);
});

test("the camera flies to a picked wire's first pin, where its piece has moved it", () => {
  const moved = (piece: string): [number, number, number] => (piece === "fc" ? [0, 0, 0.05] : [0, 0, 0]);
  expect(focusOf(WIRES[0], moved)).toEqual([0.01, 0, 0.05]);
});
