// What's happening in a run, in plain words: each kind of event the sims mark, said the way
// I'd say it, for the caption under the flying drone.
import type { FlightEvent } from "../data/types";
import { isMoment } from "./clip";

const WORDS: Record<string, string> = {
  arm: "Arming",
  armed: "Armed",
  takeoff: "Taking off",
  "took off": "Taking off",
  hold: "Holding its height",
  altitude: "Holding its height",
  offboard: "Following the test's script",
  "hover start": "Hovering",
  "dash start": "Flat out to the north",
  "wind start": "The wind picks up",
  "link cut": "The link to the ground is cut",
  "link lost": "It hears nothing from the ground",
  return: "Flying home",
  "low battery": "The battery says come home",
  "motor failed": "Motor 1 stops",
  "motor failure": "Motor 1 stops",
  "critical failure": "It knows it can't fly",
  termination: "Flight termination",
  terminate: "Flight termination",
  "chute fired": "The chute fires",
  "motors stopped": "The motors are off",
  "position lost": "It loses its position",
  "gps failed": "The GPS is gone",
  "pack sagged": "The pack sags",
  grab: "It grabs the box",
  "carry start": "Carrying the box",
  release: "It lets go of the box",
  land: "Coming down",
  "land sent": "Coming down",
  descend: "Coming down",
  landed: "Down",
  disarmed: "Disarmed",
  look: "Looking around",
  out: "Heading out",
  back: "Heading back",
  home: "Home",
  turn: "Turning back",
  "sense start": "Sensing the wind",
  "grid start": "Flying the mapping grid",
  "back to start": "Flying back to the start",
  "land here": "Flying to the spot it's given",
  "land now": "Landing where it is",
  "still start": "Hovering in still air",
  "lifted start": "In the rising air",
  spiral: "Spiraling down",
  straight: "Straight down the last 4 m",
  "flow start": "Flying on the camera alone",
  "to the spot": "Flying to the safe spot",
};

const NUMBERED: [RegExp, (n: number) => string][] = [
  [/^step (\d+) start$/, (n) => `Stick step ${n + 1}`],
  [/^doublet (\d+) start$/, (n) => `Roll doublet ${n + 1}`],
  [/^cruise (\d+) start$/, (n) => `Cruising, leg ${n + 1}`],
  [/^waypoint (\d+)$/, (n) => `Waypoint ${n}`],
];

export function eventWords(name: string): string {
  if (WORDS[name]) return WORDS[name];
  for (const [pattern, words] of NUMBERED) {
    const m = pattern.exec(name);
    if (m) return words(Number(m[1]));
  }
  return name.charAt(0).toUpperCase() + name.slice(1);
}

// a scenario's description down to its first sentence, for the line under its name
export function firstSentence(text: string): string {
  const m = /^(.+?[.!?])(\s|$)/.exec(text.trim());
  return m ? m[1] : text.trim();
}

export interface Caption {
  at: number; // the run's time it happened
  text: string;
}

// what happened last by the run's time t: each kind once, at its first, and only what happened
// rather than a grader's measuring window
export function captionAt(events: FlightEvent[], t: number): Caption | null {
  const seen = new Set<string>();
  let last: Caption | null = null;
  for (const e of [...events].sort((a, b) => a.at - b.at)) {
    if (e.at > t) break;
    if (!isMoment(e.name) || seen.has(e.name)) continue;
    seen.add(e.name);
    last = { at: e.at, text: eventWords(e.name) };
  }
  return last;
}
