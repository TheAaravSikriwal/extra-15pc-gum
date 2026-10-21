// The home page, for now: what the data says is there. It grows into the drone and one quiet
// line per step (task 13).
import { useEffect, useState } from "react";

import { loadData, type LoadOptions } from "../data/load";
import type { Index } from "../data/types";

const STEPS: Record<string, string> = {
  sizing: "Sizing and parts",
  cad: "The virtual drone (CAD)",
  electrical: "Electrical design",
  "flight-sim": "Flight sim",
};

export function Home({ load }: { load?: LoadOptions }) {
  const [index, setIndex] = useState<Index | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => {
    loadData<Index>("index.json", load)
      .then(setIndex)
      .catch((error: Error) => setProblem(error.message));
  }, [load]);
  if (problem) return <p role="alert">{problem}</p>;
  if (!index) return <p>Loading</p>;
  return (
    <main>
      <h1>Extra 15pc Gum</h1>
      <ul aria-label="steps">
        {Object.entries(index.reports).map(([name, report]) => (
          <li key={name}>
            {STEPS[name] ?? name}:{" "}
            {report.found ? (report.verdict ?? "written") : "not there yet"}
          </li>
        ))}
      </ul>
      <p className="made">
        Made {index.generated}
        {index.commit ? ` from ${index.commit}` : ""}
      </p>
    </main>
  );
}
