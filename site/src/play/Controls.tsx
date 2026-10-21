// The playback controls under every played-back run: play and pause, the speed, the scrubber,
// and the events as chapter buttons.
import { useState } from "react";

import { type Clock, useClockTime } from "./clock";

const SPEEDS = [0.25, 0.5, 1, 2, 4];

export function formatTime(t: number): string {
  const minutes = Math.floor(t / 60);
  const seconds = t - minutes * 60;
  return `${minutes}:${seconds.toFixed(1).padStart(4, "0")}`;
}

export function Controls({ clock }: { clock: Clock }) {
  const time = useClockTime(clock);
  const [, redraw] = useState(0);
  const refresh = () => redraw((n) => n + 1);
  const playing = clock.playing();
  return (
    <div className="controls" role="group" aria-label="playback">
      <button
        type="button"
        onClick={() => {
          if (playing) clock.pause();
          else clock.play();
          refresh();
        }}
      >
        {playing ? "Pause" : "Play"}
      </button>
      <input
        type="range"
        aria-label="scrubber"
        min={0}
        max={clock.duration}
        step={0.05}
        value={time}
        onChange={(e) => {
          clock.seek(Number(e.target.value));
          refresh();
        }}
      />
      <span className="time">
        {formatTime(time)} / {formatTime(clock.duration)}
      </span>
      <label>
        speed{" "}
        <select
          aria-label="speed"
          value={clock.getSpeed()}
          onChange={(e) => {
            clock.setSpeed(Number(e.target.value));
            refresh();
          }}
        >
          {SPEEDS.map((s) => (
            <option key={s} value={s}>
              {s}x
            </option>
          ))}
        </select>
      </label>
      <div className="chapters">
        {clock.chapters.map((c) => (
          <button
            key={`${c.name}-${c.at}`}
            type="button"
            className={clock.chapterAt(time) === c ? "now" : undefined}
            onClick={() => {
              clock.seek(c.at);
              refresh();
            }}
          >
            {c.name} <span className="at">{formatTime(c.at)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
