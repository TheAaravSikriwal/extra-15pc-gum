import type { Flights, Playback } from "../data/types";
import { clipOf } from "./clip";
import { firmwaresFor, handoff, numbersAt, propSpeeds, resultLine, runFor, speedWords, storyProps } from "./fly";

const FLIGHTS: Flights = {
  schema_version: 1,
  scenarios: ["hover", "parachute drop"],
  about: [],
  setups: ["base", "max"],
  runs: [
    { scenario: "hover", setup: "max", firmware: "mine", flown: true, passed: true, file: "flights/max-hover-mine.json" },
    { scenario: "hover", setup: "max", firmware: "px4", flown: true, passed: true, file: "flights/max-hover-px4.json" },
    { scenario: "parachute drop", setup: "max", firmware: "px4", flown: true, passed: true, file: "flights/max-parachute-drop-px4.json" },
  ],
};

function flight(): Playback {
  const t = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  return {
    schema_version: 1,
    scenario: "parachute drop",
    setup: "max",
    firmware: "px4",
    passed: false,
    findings: [
      { check: "order", passed: true, detail: "motors first" },
      { check: "height lost", passed: false, detail: "lost 12 m against 10" },
    ],
    t,
    position: t.map((s) => [s * 3, 4 * s, s < 9 ? Math.min(10, s * 3) : 0.1]),
    attitude: t.map(() => [0, 0, 0, 1]),
    motors: t.map((s) => (s < 6 ? [500, 510, 520, 530] : [0, 0, 0, 0])),
    events: [{ at: 6, name: "chute fired" }],
  };
}

test("the run for a combination, scenario and firmware, and none where it wasn't flown", () => {
  expect(runFor(FLIGHTS, "max", "hover", "mine")?.file).toBe("flights/max-hover-mine.json");
  expect(runFor(FLIGHTS, "base", "hover", "mine")).toBeNull();
  expect(firmwaresFor(FLIGHTS, "max", "hover")).toEqual(["mine", "px4"]);
  expect(firmwaresFor(FLIGHTS, "max", "parachute drop")).toEqual(["px4"]);
});

test("the numbers beside the drone: height off the ground, speed across it, the run's time", () => {
  const clip = clipOf(flight());
  const n = numbersAt(clip, clip.timeOf(5));
  expect(n.height).toBeCloseTo(10, 0);
  expect(n.speed).toBeCloseTo(5, 0); // 3 east and 4 north each second
  expect(n.time).toBeCloseTo(5, 1);
  expect(n.factor).toBeCloseTo(1); // a short run plays at real time
});

test("how fast it's playing, in words", () => {
  expect(speedWords(1)).toBe("real time");
  expect(speedWords(1.3)).toBe("1.3x");
  expect(speedWords(12.4)).toBe("12x");
});

test("each prop spins with its own motor, in PX4's numbering", () => {
  const spins = propSpeeds([100, 0, 300, 400]);
  expect(spins["prop front right"]).toBeGreaterThan(0); // motor 1
  expect(spins["prop back left"]).toBe(0); // motor 2 stopped, so its prop does
  expect(spins["prop front left"]).toBeGreaterThan(spins["prop front right"]);
});

test("the result in a line: the first check it failed, or that it passed", () => {
  expect(resultLine(flight())).toBe("Failed height lost: lost 12 m against 10");
  expect(resultLine({ ...flight(), passed: true })).toBe("Passed every check");
});

test("only what tells the story: the canopy once the chute fires, and only with P", () => {
  const props = storyProps(flight());
  expect(props.canopyFrom).toBe(6);
  expect(storyProps({ ...flight(), setup: "base" }).canopyFrom).toBeNull();
  expect(storyProps({ ...flight(), scenario: "wind", events: [{ at: 3, name: "wind start" }] }).windFrom).toBe(3);
});

test("changing scenario eases from where the drone is to the next one's calm start", () => {
  const from = { t: 0, position: [0, 0, 5] as [number, number, number], attitude: [0.3, 0, 0, 0.954] as [number, number, number, number], motors: [800, 800, 800, 800], speed: 1, fade: 1 };
  const to = { ...from, attitude: [0, 0, 0, 1] as [number, number, number, number], motors: [560, 560, 560, 560] };
  handoff(from, to, 0).attitude.forEach((v, i) => expect(v).toBeCloseTo(from.attitude[i], 3));
  expect(handoff(from, to, 1).motors).toEqual(to.motors);
  const half = handoff(from, to, 0.5);
  expect(half.motors[0]).toBeCloseTo(680);
  expect(half.attitude[0]).toBeGreaterThan(0);
  expect(half.attitude[0]).toBeLessThan(0.3);
});
