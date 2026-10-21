// The home page: the drone and one quiet line per step, each line its step's page. The rest
// is found by going in.
import { useState } from "react";

import type { LoadOptions } from "../data/load";
import type { Index, Steps, Unproven } from "../data/types";
import { useData } from "../data/useData";
import { stepLink, stepTitle } from "./Steps";
import { countUnproven } from "./Unproven";

const REPORT_NAMES: Record<string, string> = {
  sizing: "Sizing and parts",
  cad: "The virtual drone (CAD)",
  electrical: "Electrical design",
  "flight-sim": "Flight sim",
};

function Reports({ index }: { index: Index }) {
  // before steps.json is made: what each report says
  return (
    <ul aria-label="steps" className="quiet-steps">
      {Object.entries(index.reports).map(([name, report]) => (
        <li key={name}>
          {REPORT_NAMES[name] ?? name}: {report.found ? (report.verdict ?? "written") : "not there yet"}
        </li>
      ))}
    </ul>
  );
}

export function Home({ load }: { load?: LoadOptions }) {
  const index = useData<Index>("index.json", load);
  const steps = useData<Steps>("steps.json", load);
  const unproven = useData<Unproven>("unproven.json", load);
  const [picture, setPicture] = useState(true);
  if (index.problem) return <p role="alert">{index.problem}</p>;
  if (!index.data) return <p>Loading</p>;
  const main = steps.data?.steps.filter((s) => !s.side_track) ?? [];
  const side = steps.data?.steps.filter((s) => s.side_track) ?? [];
  return (
    <main className="home">
      <h1>Extra 15pc Gum</h1>
      <p className="lede">
        My long-range quadcopter, with my own flight firmware. Every real part is modeled, wired and flown in
        simulation, in public, before anything gets bought.
      </p>
      {picture && (
        <a href="#/drone" className="hero">
          <img
            src="./data/hero.png"
            alt="The drone in CAD, from three quarters (open it in 3D)"
            width={857}
            height={444}
            onError={() => setPicture(false)}
          />
        </a>
      )}
      {steps.data ? (
        <>
          <ul aria-label="steps" className="quiet-steps">
            {main.map((s) => (
              <li key={s.id}>
                <a href={stepLink(s.id)}>{stepTitle(s)}</a> <span className="status">{s.status}</span>
              </li>
            ))}
          </ul>
          {side.length > 0 && (
            <p className="side-tracks">
              Side tracks:{" "}
              {side.map((s, k) => (
                <span key={s.id}>
                  {k > 0 && ", "}
                  <a href={stepLink(s.id)}>{s.name}</a>
                </span>
              ))}
            </p>
          )}
        </>
      ) : (
        steps.problem && <Reports index={index.data} />
      )}
      {unproven.data && (
        <p className="unproven-line">
          <a href="#/unproven">What the sims can't prove</a>: {countUnproven(unproven.data)}{" "}
          {countUnproven(unproven.data) === 1 ? "thing" : "things"}, and what to measure first.
        </p>
      )}
      <p className="made">
        Made {index.data.generated}
        {index.data.commit ? ` from ${index.data.commit}` : ""}
      </p>
    </main>
  );
}
