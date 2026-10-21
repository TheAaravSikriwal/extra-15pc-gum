// The playback clock: one per page, driving the 3D drone, the charts and the events together,
// so a flight "plays live" from its log. Real speed by default, with a speed control, a
// scrubber and the events as chapter marks.
import { useEffect, useState } from "react";

export interface Chapter {
  at: number; // s into the flight
  name: string;
}

export interface ClockOptions {
  duration: number; // s
  chapters?: Chapter[];
  now?: () => number; // ms; the page's clock unless a test passes its own
}

export class Clock {
  readonly duration: number;
  readonly chapters: Chapter[];
  private now: () => number;
  private startedAt = 0; // ms on the page's clock when it last started playing
  private from = 0; // s into the flight at that moment
  private speed = 1;
  private running = false;

  constructor(options: ClockOptions) {
    this.duration = options.duration;
    this.chapters = [...(options.chapters ?? [])].sort((a, b) => a.at - b.at);
    this.now = options.now ?? (() => performance.now());
  }

  time(): number {
    if (!this.running) return this.from;
    const t = this.from + ((this.now() - this.startedAt) / 1000) * this.speed;
    if (t >= this.duration) {
      this.running = false;
      this.from = this.duration;
      return this.duration;
    }
    return t;
  }

  playing(): boolean {
    this.time(); // stops it if it has run off the end
    return this.running;
  }

  play(): void {
    if (this.running) return;
    if (this.from >= this.duration) this.from = 0; // from the start again
    this.startedAt = this.now();
    this.running = true;
  }

  pause(): void {
    this.from = this.time();
    this.running = false;
  }

  seek(t: number): void {
    this.from = Math.min(Math.max(t, 0), this.duration);
    this.startedAt = this.now();
  }

  setSpeed(speed: number): void {
    this.from = this.time();
    this.startedAt = this.now();
    this.speed = speed;
  }

  getSpeed(): number {
    return this.speed;
  }

  jumpTo(name: string): void {
    const chapter = this.chapters.find((c) => c.name === name);
    if (chapter) this.seek(chapter.at);
  }

  // the last chapter at or before `t`
  chapterAt(t: number): Chapter | undefined {
    let found: Chapter | undefined;
    for (const c of this.chapters) if (c.at <= t) found = c;
    return found;
  }
}

// the clock's time as React state, refreshed every animation frame while it plays
export function useClockTime(clock: Clock): number {
  const [time, setTime] = useState(clock.time());
  useEffect(() => {
    let frame = 0;
    const tick = () => {
      setTime(clock.time());
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [clock]);
  return time;
}
