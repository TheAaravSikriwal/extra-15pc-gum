import type { Flights, Playback } from "../data/types";
import { cellFor, chapters, duration, eventsSoFar, indexAt, series, toThree } from "./playback";

function run(firmware: string): Playback {
  return {
    schema_version: 1,
    scenario: "hover",
    setup: "base",
    firmware,
    passed: true,
    findings: [],
    t: [0, 1, 2, 3],
    position: [
      [0, 0, 0],
      [0, 1, 2],
      [0, 2, 4],
      [0, 3, 6],
    ],
    attitude: [
      [0, 0, 0, 1],
      [0, 0, 0, 1],
      [0, 0, 0, 1],
      [0, 0, 0, 1],
    ],
    motors: [
      [0, 0, 0, 0],
      [500, 500, 500, 500],
      [560, 560, 560, 560],
      [560, 560, 560, 560],
    ],
    events: [
      { at: 0.5, name: "armed" },
      { at: 2.5, name: "hold start" },
    ],
  };
}

test("the sample at a moment is the last one at or before it", () => {
  const p = run("px4");
  expect(indexAt(p, 0)).toBe(0);
  expect(indexAt(p, 1.5)).toBe(1);
  expect(indexAt(p, 99)).toBe(3);
});

test("the events show up as their moment comes", () => {
  expect(eventsSoFar(run("mine"), 1).map((e) => e.name)).toEqual(["armed"]);
  expect(eventsSoFar(run("mine"), 3).map((e) => e.name)).toEqual(["armed", "hold start"]);
});

test("two runs play on one clock as long as the longer, with both firmwares' events", () => {
  const longer = { ...run("mine"), t: [0, 1, 2, 5] };
  expect(duration([run("px4"), longer])).toBe(5);
  const marks = chapters([run("px4"), longer]);
  expect(marks.map((c) => c.name)).toContain("PX4: armed");
  expect(marks.map((c) => c.name)).not.toContain("mine: hold start"); // a grader's window
  expect(marks.map((c) => c.name)).toContain("mine: armed");
  const repeating = { ...run("px4"), events: [1, 2, 3].map((at) => ({ at, name: "critical failure" })) };
  expect(chapters([repeating])).toEqual([{ at: 1, name: "PX4: critical failure" }]);
});

test("east-north-up turns into three.js's y-up: north goes into the screen", () => {
  expect(toThree([1, 2, 3])).toEqual([1, 3, -2]);
});

test("the charts' series: height, sideways speed and the motors' average", () => {
  const s = series(run("px4"));
  expect(s.height).toEqual([0, 2, 4, 6]);
  expect(s.speed[2]).toBeCloseTo(1); // a meter north each second
  expect(s.motors[2]).toBe(560);
});

test("a matrix cell says how a firmware's run went", () => {
  const flights: Flights = {
    schema_version: 1,
    scenarios: ["hover"],
    setups: ["base", "P"],
    runs: [{ scenario: "hover", setup: "base", firmware: "mine", flown: true, passed: false }],
  };
  expect(cellFor(flights, "mine", "hover", "base")).toBe("fail");
  expect(cellFor(flights, "mine", "hover", "P")).toBe("not yet");
  expect(cellFor(flights, "px4", "hover", "base")).toBe("not yet");
});
