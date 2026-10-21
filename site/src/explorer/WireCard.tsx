// The card for a picked wire: its two ends, its gauge and type, the length to cut it to, and
// where each end's pins came from, the maker's drawing or my estimate.
import type { PinSource, Wire3d } from "../data/types";

const CARRIES: Record<string, string> = { power: "power", ground: "ground", signal: "a signal", bus: "the CAN bus" };

function Where({ pin, sources }: { pin: string; sources: PinSource[] }) {
  const connector = pin.split(".").slice(0, 2).join(".");
  const s = sources.find((c) => c.connector === connector);
  if (!s) return <li>{connector}: plugged into its mate, so it sits where that one does</li>;
  if (s.estimate) return <li>{connector}: my estimate: {s.note}</li>;
  return (
    <li>
      {connector}: from{" "}
      {s.url ? (
        <a href={s.url} target="_blank" rel="noreferrer">
          the maker's drawing
        </a>
      ) : (
        "the maker"
      )}
      {s.note ? `. ${s.note}` : ""}
    </li>
  );
}

export function WireCard({ wire, sources, onClose }: { wire: Wire3d; sources: PinSource[]; onClose: () => void }) {
  const [a, b] = wire.ends;
  return (
    <section className="card" aria-label="picked wire">
      <h3>
        {a.pin} to {b.pin}
      </h3>
      <dl>
        <dt>Harness</dt>
        <dd>{wire.harness}</dd>
        <dt>Wire</dt>
        <dd>
          {wire.awg} AWG {wire.wire}
        </dd>
        <dt>Cut to</dt>
        <dd>{Math.round(wire.length_mm)} mm</dd>
        <dt>Carries</dt>
        <dd>{CARRIES[wire.role] ?? wire.role}</dd>
      </dl>
      <p>Where its pins are:</p>
      <ul className="sources">
        <Where pin={a.pin} sources={sources} />
        <Where pin={b.pin} sources={sources} />
      </ul>
      <button type="button" onClick={onClose}>
        Back to the whole drone
      </button>
    </section>
  );
}
