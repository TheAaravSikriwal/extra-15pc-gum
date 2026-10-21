// Lines over time with the clock's moment marked: a flight's height, speed or motors scrolling
// along as it plays. Plain SVG; d3 only does the arithmetic.
import { scaleLinear } from "d3-scale";
import { line } from "d3-shape";

export interface Series {
  name: string;
  t: number[]; // s
  v: number[];
  color?: string; // a CSS color; the style's accent unless set
}

export interface TimeChartProps {
  title: string;
  unit: string;
  series: Series[];
  time: number; // the clock's moment, s
  duration: number; // s
  window?: number; // s shown, scrolling with the clock; the whole flight when unset
  width?: number;
  height?: number;
}

const MARGIN = { top: 24, right: 12, bottom: 24, left: 44 };

// the time span shown: the whole flight, or `window` s ending at the clock (clamped to the run)
export function visibleSpan(time: number, duration: number, window?: number): [number, number] {
  if (!window || window >= duration) return [0, duration];
  const end = Math.min(Math.max(time, window), duration);
  return [end - window, end];
}

export function TimeChart(p: TimeChartProps) {
  const width = p.width ?? 640;
  const height = p.height ?? 180;
  const [from, to] = visibleSpan(p.time, p.duration, p.window);
  const x = scaleLinear().domain([from, to]).range([MARGIN.left, width - MARGIN.right]);
  const all = p.series.flatMap((s) => s.v);
  const lo = Math.min(0, ...all);
  const hi = Math.max(lo + 1e-6, ...all);
  const y = scaleLinear().domain([lo, hi]).nice().range([height - MARGIN.bottom, MARGIN.top]);
  const toPath = line<[number, number]>()
    .x((d) => x(d[0]))
    .y((d) => y(d[1]));
  const draw = (s: Series) =>
    toPath(
      s.t.map((t, k) => [t, s.v[k]] as [number, number]).filter(([t]) => t >= from && t <= to),
    ) ?? "";
  const cursor = x(Math.min(Math.max(p.time, from), to));
  return (
    <svg
      className="time-chart"
      role="img"
      aria-label={p.title}
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
    >
      <text x={MARGIN.left} y={14} className="chart-title">
        {p.title} ({p.unit})
      </text>
      {y.ticks(4).map((v) => (
        <g key={v}>
          <line
            x1={MARGIN.left}
            x2={width - MARGIN.right}
            y1={y(v)}
            y2={y(v)}
            stroke="var(--lines)"
          />
          <text x={MARGIN.left - 6} y={y(v) + 4} textAnchor="end" className="tick">
            {v}
          </text>
        </g>
      ))}
      {p.series.map((s) => (
        <path
          key={s.name}
          data-series={s.name}
          d={draw(s)}
          fill="none"
          stroke={s.color ?? "var(--accent)"}
          strokeWidth={1.5}
        />
      ))}
      <line
        data-cursor=""
        x1={cursor}
        x2={cursor}
        y1={MARGIN.top}
        y2={height - MARGIN.bottom}
        stroke="var(--text)"
        strokeDasharray="3 3"
      />
    </svg>
  );
}
