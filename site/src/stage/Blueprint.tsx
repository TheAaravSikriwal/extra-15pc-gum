// The blueprint behind the drone when you're inside it: a drawing sheet of a generic X quad (not
// this drone), its top and side views, a prop and a motor in detail, dimension lines and a
// title block, on a fine grid in blueprint blue. The drawings keep to the edges and the middle
// stays clear, since the real drone sits there.

const LINE = "rgba(255, 255, 255, 0.55)";
const FAINT = "rgba(255, 255, 255, 0.28)";

function Arrowheads() {
  return (
    <defs>
      <marker id="bp-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0 L10 5 L0 10 z" fill={LINE} />
      </marker>
      <pattern id="bp-minor" width="20" height="20" patternUnits="userSpaceOnUse">
        <path d="M20 0 L0 0 0 20" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="1" />
      </pattern>
      <pattern id="bp-major" width="100" height="100" patternUnits="userSpaceOnUse">
        <rect width="100" height="100" fill="url(#bp-minor)" />
        <path d="M100 0 L0 0 0 100" fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth="1" />
      </pattern>
      <radialGradient id="bp-clear" cx="50%" cy="52%" r="42%">
        <stop offset="0%" stopColor="#163f73" stopOpacity="0.85" />
        <stop offset="100%" stopColor="#163f73" stopOpacity="0" />
      </radialGradient>
    </defs>
  );
}

// a quad from above: a body, four arms at 45 degrees, motors and dashed prop discs
function TopView({ x, y, s }: { x: number; y: number; s: number }) {
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
        markerStart="url(#bp-arrow)"
        markerEnd="url(#bp-arrow)"
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
function SideView({ x, y, s }: { x: number; y: number; s: number }) {
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
      <line x1={x + half + 56 * s} y1={y - 50 * s} x2={x + half + 56 * s} y2={y + 46 * s} markerStart="url(#bp-arrow)" markerEnd="url(#bp-arrow)" />
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
function Details({ x, y }: { x: number; y: number }) {
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
      <line x1={x - 70} y1={y + 92} x2={x + 70} y2={y + 92} markerStart="url(#bp-arrow)" markerEnd="url(#bp-arrow)" />
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
    <svg
      className="blueprint"
      viewBox="0 0 1600 1000"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      fontFamily="JetBrains Mono, ui-monospace, monospace"
    >
      <Arrowheads />
      <rect width="1600" height="1000" fill="#163f73" />
      <rect width="1600" height="1000" fill="url(#bp-major)" />
      <rect x="20" y="20" width="1560" height="960" fill="none" stroke={FAINT} strokeWidth="1.5" />
      <TopView x={250} y={300} s={1} />
      <SideView x={1290} y={260} s={0.95} />
      <Details x={170} y={790} />
      <TitleBlock x={1230} y={870} />
      {/* the middle kept clear for the drone */}
      <rect width="1600" height="1000" fill="url(#bp-clear)" />
    </svg>
  );
}
