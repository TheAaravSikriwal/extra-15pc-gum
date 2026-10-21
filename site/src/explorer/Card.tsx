// The card for whatever's picked in 3D: a part, with its catalog entry, or a wire route with
// every wire in it, end to end, and how hard it works.
import type { Piece, Route } from "../data/types";
import { wireRows } from "./logic";

export function Card({
  piece,
  route,
  combination,
  kase,
}: {
  piece: Piece | null;
  route: Route | null;
  combination: string;
  kase: string;
}) {
  if (!piece) return <p className="card hint">Click any part of the drone.</p>;
  const c = piece.catalog;
  return (
    <section className="card" aria-label="picked">
      <h3>{c ? `${c.maker} ${c.model}` : piece.name}</h3>
      <dl>
        <dt>Module</dt>
        <dd>{piece.module}</dd>
        <dt>Kind</dt>
        <dd>{piece.kind}</dd>
        <dt>Weight</dt>
        <dd>{piece.mass_g.toFixed(1)} g</dd>
        {c?.price_usd != null && (
          <>
            <dt>Price</dt>
            <dd>${c.price_usd.toFixed(2)}</dd>
          </>
        )}
      </dl>
      {c?.link && (
        <a href={c.link} target="_blank" rel="noreferrer">
          Where it comes from
        </a>
      )}
      {route && <RouteRows route={route} combination={combination} kase={kase} />}
    </section>
  );
}

function RouteRows({ route, combination, kase }: { route: Route; combination: string; kase: string }) {
  const { share, wires } = wireRows(route, combination, kase);
  return (
    <>
      <p>
        {share === null
          ? `Not worked out for ${combination} in ${kase}.`
          : `Its hardest wire is at ${(share * 100).toFixed(0)}% of its heating limit in ${combination}, ${kase}.`}
      </p>
      <ul className="wires">
        {wires.map((w) => (
          <li key={`${w.from}-${w.to}`}>
            {w.from} to {w.to}
          </li>
        ))}
      </ul>
    </>
  );
}
