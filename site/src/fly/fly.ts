// Fly it: which run plays, the numbers beside the floating drone, its props spinning with their
// own motors, the result in a line, the story's props, and the ease from one scenario into the
// next.
import type { Flights, Playback, Run } from "../data/types";
import { modulesOf } from "../explorer/logic";
import type { Clip, Frame, Quat } from "./clip";

export function runFor(flights: Flights | null, combination: string, scenario: string, firmware: string): Run | null {
  return (
    flights?.runs.find(
      (r) => r.setup === combination && r.scenario === scenario && r.firmware === firmware && r.flown && r.file,
    ) ?? null
  );
}

// the firmwares that flew a scenario in a combination, mine first
export function firmwaresFor(flights: Flights | null, combination: string, scenario: string): string[] {
  return ["mine", "px4"].filter((f) => runFor(flights, combination, scenario, f));
}

export interface Numbers {
  height: number; // m above where it took off
  speed: number; // m/s across the ground
  time: number; // s into the run
  factor: number; // how many times real time it's playing
}

export function numbersAt(clip: Clip, s: number): Numbers {
  const now = clip.at(s);
  const before = clip.at(Math.max(0, s - 0.1));
  const after = clip.at(Math.min(clip.duration, s + 0.1));
  const dt = after.t - before.t || 1;
  const speed = Math.hypot(after.position[0] - before.position[0], after.position[1] - before.position[1]) / dt;
  return { height: now.position[2] - clip.ground, speed, time: now.t, factor: now.speed };
}

// PX4's quad X numbering: motor 1 front right, 2 back left, 3 front left, 4 back right
const PROPS = ["prop front right", "prop back left", "prop front left", "prop back right"];
const SHOWN = 0.05; // a real prop's 500 rad/s would only flicker, so they turn at a twentieth

export function propSpeeds(motors: number[]): Record<string, number> {
  return Object.fromEntries(PROPS.map((name, k) => [name, (motors[k] ?? 0) * SHOWN]));
}

// how fast it's playing, in words
export function speedWords(factor: number): string {
  if (factor < 1.05) return "real time";
  return factor < 3 ? `${factor.toFixed(1)}x` : `${factor.toFixed(0)}x`;
}

// the result in a line: the first check it failed, or that it passed
export function resultLine(p: Playback): string {
  if (p.passed) return "Passed every check";
  const failed = p.findings.find((f) => !f.passed);
  return failed ? `Failed ${failed.check}: ${failed.detail}` : "Failed";
}

export interface StoryProps {
  canopyFrom: number | null; // the run's time the chute fires, where there's one
  windFrom: number | null; // the run's time the wind starts blowing
  columnFrom: number | null; // the run's time it flies into the rising air
}

export function storyProps(p: Playback): StoryProps {
  const first = (...names: string[]) => p.events.find((e) => names.includes(e.name))?.at ?? null;
  const chute = modulesOf(p.setup).includes("P");
  return {
    canopyFrom: chute ? first("chute fired", "termination", "terminate") : null,
    windFrom: p.scenario === "turn back" ? 0 : first("wind start"),
    columnFrom: first("lifted start"),
  };
}

function nlerp(a: Quat, b: Quat, f: number): Quat {
  const dot = a.reduce((s, v, i) => s + v * b[i], 0);
  const sign = dot < 0 ? -1 : 1;
  const q = a.map((v, i) => v * (1 - f) + sign * b[i] * f);
  const n = Math.hypot(...q) || 1;
  return q.map((v) => v / n) as Quat;
}

// partway (f, 0 to 1) from one frame to another: the drone's tilt and its motors
export function handoff(from: Frame, to: Frame, f: number): Frame {
  const x = Math.min(Math.max(f, 0), 1);
  const e = x * x * (3 - 2 * x);
  return {
    ...to,
    attitude: nlerp(from.attitude, to.attitude, e),
    motors: to.motors.map((m, i) => (from.motors[i] ?? m) + (m - (from.motors[i] ?? m)) * e),
    fade: from.fade + (to.fade - from.fade) * e,
  };
}
