// Checks against their limits, as bars: each drawn as a share of its own limit, so minutes,
// ratios and amps sit on one chart with every limit at the same line.
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
  const share = (b: Bar) => (b.limit ? b.value / b.limit : 0);
  const top = Math.max(1, ...bars.map(share)) * 1.1;
  const x = scaleLinear().domain([0, top]).range([left, width - 90]);
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
              width={Math.max(0, x(share(b)) - left)}
              height={rowHeight - 10}
              fill={passes(b) ? "var(--pass)" : "var(--fail)"}
            />
            <line x1={x(1)} x2={x(1)} y1={y} y2={y + rowHeight} stroke="var(--text)" />
            <text x={x(Math.max(share(b), 1)) + 6} y={y + 17} className="bar-value">
              {b.value.toFixed(1)} {b.unit} / {b.limit.toFixed(1)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
