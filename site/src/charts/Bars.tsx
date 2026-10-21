// A check against its limit, as a bar: how far past (or short of) the line each value is.
import { scaleLinear } from "d3-scale";

export interface Bar {
  name: string;
  value: number;
  limit: number;
  unit: string;
  higherIsBetter: boolean;
}

export function passes(b: Bar): boolean {
  return b.higherIsBetter ? b.value >= b.limit : b.value <= b.limit;
}

export function Bars({ title, bars, width = 640 }: { title: string; bars: Bar[]; width?: number }) {
  const rowHeight = 28;
  const left = 220;
  const height = bars.length * rowHeight + 8;
  const top = Math.max(...bars.map((b) => Math.max(b.value, b.limit)), 1e-6) * 1.1;
  const x = scaleLinear().domain([0, top]).range([left, width - 60]);
  return (
    <svg className="bars" role="img" aria-label={title} viewBox={`0 0 ${width} ${height}`} width="100%">
      {bars.map((b, k) => {
        const y = 4 + k * rowHeight;
        return (
          <g key={b.name} data-bar={b.name} data-passes={passes(b) ? "yes" : "no"}>
            <text x={0} y={y + 17} className="bar-name">
              {b.name}
            </text>
            <rect
              x={left}
              y={y + 4}
              width={Math.max(0, x(b.value) - left)}
              height={rowHeight - 10}
              fill={passes(b) ? "var(--pass)" : "var(--fail)"}
            />
            <line x1={x(b.limit)} x2={x(b.limit)} y1={y} y2={y + rowHeight} stroke="var(--text)" />
            <text x={x(Math.max(b.value, b.limit)) + 6} y={y + 17} className="bar-value">
              {b.value.toFixed(1)} {b.unit}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
