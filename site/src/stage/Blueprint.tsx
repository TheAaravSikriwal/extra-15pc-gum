// The blueprint behind the drone when you're inside it: a drawing sheet of a generic X quad (not
// this drone), its top and side views, a prop and a motor in detail, dimension lines and a
// title block, on a fine grid in blueprint blue. The grid and the sheet's border fill the screen
// whatever its shape; each drawing is its own small figure pinned to a corner of the space the
// panel leaves, so none gets cropped or hidden, and the middle stays clear for the real drone.

import type { ReactNode } from "react";

const LINE = "rgba(255, 255, 255, 0.55)";
const FAINT = "rgba(255, 255, 255, 0.28)";

// the dimension lines' arrowheads, one set per figure (each figure is its own SVG)
function Arrowheads({ id }: { id: string }) {
  return (
    <defs>
      <marker id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0 L10 5 L0 10 z" fill={LINE} />
      </marker>
    </defs>
  );
}

function Figure({ name, viewBox, children }: { name: string; viewBox: string; children: ReactNode }) {
  return (
    <svg className={`bp-figure bp-${name}`} viewBox={viewBox} preserveAspectRatio="xMidYMid meet">
      <Arrowheads id={`bp-arrow-${name}`} />
      {children}
    </svg>
  );
}

// a quad from above: a body, four arms at 45 degrees, motors and dashed prop discs
function TopView({ x, y, s, arrow }: { x: number; y: number; s: number; arrow: string }) {
  const arm = 110 * s;
  const ends = [45, 135, 225, 315].map((d) => {
    const a = (d * Math.PI) / 180;
    return [x + arm * Math.cos(a), y - arm * Math.sin(a)];
  });
  return (
    <g stroke={LINE} fill="none" strokeWidth="1.3">
      <rect x={x - 22 * s} y={y - 40 * s} width={44 * s} height={80 * s} rx={4 * s} />
      <rect x={x - 14 * s} y={y - 14 * s} width={28 * s} height={28 * s} stroke={FAINT} />
      {ends.map(([ex, ey], k) => (
        <g key={k}>
          <line x1={x} y1={y} x2={ex} y2={ey} strokeWidth={9 * s} stroke={FAINT} strokeLinecap="round" />
          <line x1={x} y1={y} x2={ex} y2={ey} />
          <circle cx={ex} cy={ey} r={13 * s} />
          <circle cx={ex} cy={ey} r={4 * s} />
          <circle cx={ex} cy={ey} r={62 * s} strokeDasharray="6 5" stroke={FAINT} />
        </g>
      ))}
      <path d={`M${x} ${y - 52 * s} l${-6 * s} ${10 * s} h${12 * s} z`} fill={LINE} stroke="none" />
      {/* the motor-to-motor diagonal */}
      <line x1={ends[2][0]} y1={ends[2][1] + 26 * s} x2={ends[0][0]} y2={ends[0][1] + 26 * s} stroke={FAINT} />
      <line
        x1={ends[1][0] - 70 * s}
        y1={y + arm * 0.71 + 40 * s}
        x2={ends[0][0] + 70 * s}
        y2={y + arm * 0.71 + 40 * s}
        markerStart={`url(#${arrow})`}
        markerEnd={`url(#${arrow})`}
      />
      <text x={x} y={y + arm * 0.71 + 32 * s} fill={LINE} stroke="none" fontSize={11} textAnchor="middle">
        MOTOR TO MOTOR 420
      </text>
      <text x={x} y={y - arm - 30 * s} fill={LINE} stroke="none" fontSize={12} textAnchor="middle" letterSpacing="2">
        TOP VIEW
      </text>
    </g>
  );
}

// from the side: three plates, standoffs, the stack, two motors and their props edge-on, legs
function SideView({ x, y, s, arrow }: { x: number; y: number; s: number; arrow: string }) {
  const half = 150 * s;
  return (
    <g stroke={LINE} fill="none" strokeWidth="1.3">
      <rect x={x - 60 * s} y={y - 4 * s} width={120 * s} height={4 * s} />
      <rect x={x - 60 * s} y={y - 26 * s} width={120 * s} height={4 * s} />
      <rect x={x - 45 * s} y={y - 48 * s} width={90 * s} height={4 * s} />
      {[-50, 50].map((dx) => (
        <line key={dx} x1={x + dx * s} y1={y - 22 * s} x2={x + dx * s} y2={y - 44 * s} stroke={FAINT} />
      ))}
      <rect x={x - 16 * s} y={y - 21 * s} width={32 * s} height={15 * s} stroke={FAINT} />
      <line x1={x - half} y1={y - 12 * s} x2={x + half} y2={y - 12 * s} />
      {[-1, 1].map((side) => (
        <g key={side}>
          <rect x={x + side * half - 14 * s} y={y - 40 * s} width={28 * s} height={26 * s} rx={3 * s} />
          <line x1={x + side * half} y1={y - 40 * s} x2={x + side * half} y2={y - 48 * s} />
          <ellipse cx={x + side * half} cy={y - 50 * s} rx={62 * s} ry={3 * s} stroke={FAINT} />
          <line x1={x + side * 40 * s} y1={y} x2={x + side * 56 * s} y2={y + 46 * s} />
        </g>
      ))}
      <line x1={x - half - 80 * s} y1={y + 46 * s} x2={x + half + 80 * s} y2={y + 46 * s} stroke={FAINT} strokeDasharray="14 6" />
      <line x1={x + half + 56 * s} y1={y - 50 * s} x2={x + half + 56 * s} y2={y + 46 * s} markerStart={`url(#${arrow})`} markerEnd={`url(#${arrow})`} />
      <text x={x + half + 64 * s} y={y} fill={LINE} stroke="none" fontSize={11}>
        HEIGHT
      </text>
      <text x={x} y={y + 76 * s} fill={LINE} stroke="none" fontSize={12} textAnchor="middle" letterSpacing="2">
        SIDE VIEW
      </text>
    </g>
  );
}

// a three-blade prop and its disc, and a motor's bell from above, with their sizes
function Details({ x, y, arrow }: { x: number; y: number; arrow: string }) {
  const blades = [90, 210, 330].map((d) => (d * Math.PI) / 180);
  return (
    <g stroke={LINE} fill="none" strokeWidth="1.2">
      <circle cx={x} cy={y} r={70} stroke={FAINT} strokeDasharray="6 5" />
      {blades.map((a, k) => (
        <path
          key={k}
          d={`M${x} ${y} Q ${x + 30 * Math.cos(a - 0.35)} ${y - 30 * Math.sin(a - 0.35)} ${x + 68 * Math.cos(a)} ${y - 68 * Math.sin(a)} Q ${x + 30 * Math.cos(a + 0.25)} ${y - 30 * Math.sin(a + 0.25)} ${x} ${y}`}
        />
      ))}
      <circle cx={x} cy={y} r={7} />
      <line x1={x - 70} y1={y + 92} x2={x + 70} y2={y + 92} markerStart={`url(#${arrow})`} markerEnd={`url(#${arrow})`} />
      <text x={x} y={y + 86} fill={LINE} stroke="none" fontSize={11} textAnchor="middle">
        10 IN, 3 BLADES
      </text>
      <circle cx={x + 190} cy={y} r={34} />
      <circle cx={x + 190} cy={y} r={26} stroke={FAINT} />
      {[0, 90, 180, 270].map((d) => {
        const a = ((d + 45) * Math.PI) / 180;
        return <circle key={d} cx={x + 190 + 13 * Math.cos(a)} cy={y - 13 * Math.sin(a)} r={2.2} />;
      })}
      <circle cx={x + 190} cy={y} r={4} />
      <text x={x + 190} y={y + 58} fill={LINE} stroke="none" fontSize={11} textAnchor="middle">
        MOTOR, 19 X 19 MOUNT
      </text>
      <text x={x + 95} y={y - 104} fill={LINE} stroke="none" fontSize={12} textAnchor="middle" letterSpacing="2">
        DETAILS
      </text>
    </g>
  );
}

function TitleBlock({ x, y }: { x: number; y: number }) {
  const rows: [string, string][] = [
    ["DRAWING", "GENERIC QUADROTOR, X LAYOUT"],
    ["SHEET", "A STUDY, NOT THIS DRONE"],
    ["SCALE", "NOT TO SCALE"],
    ["PROJECT", "EXTRA 15PC GUM"],
  ];
  return (
    <g stroke={LINE} fill="none" strokeWidth="1.2" fontSize={11}>
      <rect x={x} y={y} width={330} height={rows.length * 26} />
      {rows.map(([k, v], i) => (
        <g key={k}>
          {i > 0 && <line x1={x} y1={y + i * 26} x2={x + 330} y2={y + i * 26} />}
          <line x1={x + 86} y1={y + i * 26} x2={x + 86} y2={y + (i + 1) * 26} />
          <text x={x + 8} y={y + i * 26 + 17} fill={FAINT} stroke="none" letterSpacing="1.5">
            {k}
          </text>
          <text x={x + 96} y={y + i * 26 + 17} fill={LINE} stroke="none" letterSpacing="1">
            {v}
          </text>
        </g>
      ))}
    </g>
  );
}

export function Blueprint() {
  return (
    <div className="blueprint" aria-hidden="true">
      <div className="bp-sheet" />
      <div className="bp-area">
        <Figure name="side" viewBox="-240 -72 530 160">
          <SideView x={0} y={0} s={1} arrow="bp-arrow-side" />
        </Figure>
        <Figure name="top" viewBox="-162 -162 324 314">
          <TopView x={0} y={0} s={1} arrow="bp-arrow-top" />
        </Figure>
        <Figure name="details" viewBox="-80 -122 352 226">
          <Details x={0} y={0} arrow="bp-arrow-details" />
        </Figure>
        <Figure name="title" viewBox="-2 -2 334 108">
          <TitleBlock x={0} y={0} />
        </Figure>
      </div>
    </div>
  );
}
