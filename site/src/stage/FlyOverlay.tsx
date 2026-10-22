// Under the flying drone, the run at a glance: what just happened, in a line; its path seen from
// above, with a dot where the drone is; and its height along the loop from liftoff to touchdown,
// filling in as it plays, a tick at each moment, and a playhead to click or drag along. The dot
// and the playhead follow the drone every frame rather than every re-render, so they glide.
import { type KeyboardEvent, type PointerEvent, useEffect, useMemo, useRef } from "react";

import { captionAt, eventWords } from "../fly/captions";
import { SLOW_MOTION } from "../fly/particles";
import { TURBO_GRADIENT } from "../fly/turbo";
import { planOf, profileOf, roundMeters } from "../fly/maps";
import type { FlyData } from "./Stage";

const KEY_STEP = 0.05; // how far an arrow key moves along the loop

// in the wind tunnel: which way the air comes, and what its colors mean
function TunnelStrip({ fly }: { fly: FlyData }) {
  const entry = fly.flowEntry;
  if (!entry) return null;
  const top = fly.flow?.color_max ?? 17;
  return (
    <section className="fly-overlay tunnel" aria-label="the air">
      <div className="fly-story">
        <p className="fly-caption">
          <span className="at">{fly.flow ? `${fly.flow.speed} m/s` : "..."}</span>
          <span className="what" key={entry.direction}>
            {entry.label}
          </span>
        </p>
        <div className="turbo-scale wide" aria-hidden="true">
          <i style={{ background: TURBO_GRADIENT }} />
          <span>0</span>
          <span>{Math.round(top / 2)}</span>
          <span>{top} m/s</span>
        </div>
        <div className="fly-ends">
          <span>Blue is slow, red is fast</span>
          <span>Slowed down {SLOW_MOTION} times</span>
        </div>
      </div>
    </section>
  );
}

export function FlyOverlay({ fly }: { fly: FlyData }) {
  if (fly.flowEntry) return <TunnelStrip fly={fly} />;
  return <RunStrip fly={fly} />;
}

function RunStrip({ fly }: { fly: FlyData }) {
  const { playback, clip, playing, live, seek } = fly;
  const plan = useMemo(() => (playback && clip ? planOf(playback, clip) : null), [playback, clip]);
  const profile = useMemo(() => (playback && clip ? profileOf(playback, clip) : null), [playback, clip]);
  const dot = useRef<SVGCircleElement>(null);
  const cut = useRef<SVGRectElement>(null);
  const head = useRef<HTMLSpanElement>(null);
  const mark = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!plan || !profile || typeof requestAnimationFrame === "undefined") return;
    let id = 0;
    const follow = () => {
      const now = live.current;
      if (now) {
        const [x, y] = plan.place(now.position);
        dot.current?.setAttribute("cx", x.toFixed(2));
        dot.current?.setAttribute("cy", y.toFixed(2));
        const across = profile.x(now.t);
        const up = profile.y(now.position[2] - (clip?.ground ?? 0));
        cut.current?.setAttribute("width", across.toFixed(2));
        if (head.current) head.current.style.left = `${across}%`;
        if (mark.current) {
          mark.current.style.left = `${across}%`;
          mark.current.style.top = `${up}%`;
        }
      }
      id = requestAnimationFrame(follow);
    };
    id = requestAnimationFrame(follow);
    return () => cancelAnimationFrame(id);
  }, [plan, profile, live, clip]);

  if (!playback || !clip || !plan || !profile) return null;
  const caption = playing ? captionAt(playback.events, playing.time) : null;
  const [padX, padY] = plan.place(playback.position[playback.t.findIndex((t) => t >= clip.start)] ?? [0, 0, 0]);
  const span = clip.end - clip.start;
  // a jump to a share of the way along the loop
  const jump = (f: number) => {
    seek.current = Math.min(Math.max(f, 0), 0.999) * clip.duration;
  };
  const along = (e: PointerEvent<HTMLDivElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    jump((e.clientX - box.left) / (box.width || 1));
  };
  const keys = (e: KeyboardEvent<HTMLDivElement>) => {
    const now = clip.timeOf(live.current?.t ?? clip.start) / clip.duration;
    if (e.key === "ArrowRight") jump(now + KEY_STEP);
    else if (e.key === "ArrowLeft") jump(now - KEY_STEP);
    else if (e.key === "Home") jump(0);
    else return;
    e.preventDefault();
  };

  return (
    <section className="fly-overlay" aria-label="the run">
      <figure className="fly-plan">
        <svg viewBox="0 0 100 100" role="img" aria-label="its path from above, north up">
          <polyline points={plan.points} />
          <rect className="pad" x={padX - 4} y={padY - 4} width="8" height="8" />
          <circle ref={dot} className="now" r="4" cx={padX} cy={padY} />
        </svg>
        <figcaption>Above · {roundMeters(plan.across)} m</figcaption>
      </figure>
      <div className="fly-story">
        <p className="fly-caption" aria-live="polite">
          <span className="at">{(caption?.at ?? clip.start).toFixed(0)} s</span>
          <span className="what" key={caption?.text ?? ""}>
            {caption?.text ?? "Taking off"}
          </span>
        </p>
        <div
          className="fly-strip"
          role="slider"
          tabIndex={0}
          aria-label="the run's time"
          aria-valuemin={Math.round(clip.start)}
          aria-valuemax={Math.round(clip.end)}
          aria-valuenow={Math.round(playing?.time ?? clip.start)}
          aria-valuetext={`${(playing?.time ?? clip.start).toFixed(0)} s${caption ? `, ${caption.text}` : ""}`}
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture?.(e.pointerId);
            along(e);
          }}
          onPointerMove={(e) => {
            if (e.buttons & 1) along(e);
          }}
          onKeyDown={keys}
        >
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <clipPath id="fly-flown">
                <rect ref={cut} x="0" y="0" width="0" height="100" />
              </clipPath>
            </defs>
            <polyline points={profile.points} />
            <polyline className="flown" points={profile.points} clipPath="url(#fly-flown)" />
            {clip.moments.map((m) => {
              const x = profile.x(m.at);
              return (
                <g key={m.name} className={m.at === caption?.at ? "tick on" : "tick"}>
                  <title>{`${m.at.toFixed(0)} s: ${eventWords(m.name)}`}</title>
                  <line x1={x} x2={x} y1="84" y2="100" />
                  <rect x={x - 1.5} y="0" width="3" height="100" />
                </g>
              );
            })}
          </svg>
          <span ref={head} className="playhead" />
          <i ref={mark} className="now" />
        </div>
        <div className="fly-ends">
          <span>Height · top {roundMeters(profile.top)} m</span>
          <span>{span.toFixed(0)} s flown</span>
        </div>
      </div>
    </section>
  );
}
