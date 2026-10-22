// How to look around the drone in Fly it, said quietly under the intro: a little mouse for each
// of the orbit controls, the part that does it filled in, and on a touch screen the fingers
// instead.

type Part = "left" | "wheel" | "right";

function Mouse({ part }: { part: Part }) {
  return (
    <svg className="hint-mouse" viewBox="0 0 12 18" aria-hidden="true">
      {part === "left" && <path className="on" d="M6 1.5H5.5A4.5 4.5 0 0 0 1 6V7.5H6Z" />}
      {part === "right" && <path className="on" d="M6 1.5H6.5A4.5 4.5 0 0 1 11 6V7.5H6Z" />}
      <rect x="1" y="1.5" width="10" height="15" rx="5" />
      <path d="M1 7.5H11 M6 1.5V7.5" />
      <rect className={part === "wheel" ? "on" : undefined} x="5" y="3.2" width="2" height="3" rx="1" />
    </svg>
  );
}

function Fingers({ count, apart }: { count: 1 | 2; apart?: boolean }) {
  const xs = count === 1 ? [6] : apart ? [2.5, 9.5] : [4, 8];
  return (
    <svg className="hint-mouse" viewBox="0 0 12 18" aria-hidden="true">
      {xs.map((x) => (
        <circle key={x} className="on" cx={x} cy="9" r="1.8" />
      ))}
      {apart && <path d="M4.5 9H7.5 M0.5 9H1 M11 9H11.5" />}
    </svg>
  );
}

export function ControlsHint() {
  return (
    <ul className="controls-hint" aria-label="looking around">
      <li className="by-mouse">
        <Mouse part="left" />
        <span>Drag</span> to turn around it
      </li>
      <li className="by-mouse">
        <Mouse part="wheel" />
        <span>Scroll</span> to zoom
      </li>
      <li className="by-mouse">
        <Mouse part="right" />
        <span>Right-drag</span> to slide
      </li>
      <li className="by-touch">
        <Fingers count={1} />
        <span>Drag</span> to turn around it
      </li>
      <li className="by-touch">
        <Fingers count={2} apart />
        <span>Pinch</span> to zoom
      </li>
      <li className="by-touch">
        <Fingers count={2} />
        <span>Two fingers</span> to slide
      </li>
    </ul>
  );
}
