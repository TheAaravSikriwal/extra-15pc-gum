// A page per step: what it was for, where it stands, what it decided, its pictures and the
// log entries that tell the story, all from the README's plan, the reports and the log.
import type { LoadOptions } from "../data/load";
import type { Step, Steps as StepsData } from "../data/types";
import { useData } from "../data/useData";

export function stepLink(id: string): string {
  return `#/steps/${id}`;
}

function title(s: Step): string {
  return s.number ? `${s.number}. ${s.name}` : s.name;
}

export function Steps({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<StepsData>("steps.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const groups: [string, Step[]][] = [
    ["The steps", data.steps.filter((s) => !s.side_track)],
    ["Side tracks", data.steps.filter((s) => s.side_track)],
  ];
  return (
    <main>
      <h1>Every step</h1>
      {groups.map(([name, list]) => (
        <section key={name} aria-label={name}>
          <h2>{name}</h2>
          <ul className="steps">
            {list.map((s) => (
              <li key={s.id}>
                <a href={stepLink(s.id)}>{title(s)}</a> <span className="status">{s.status}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}

export function StepPage({ id, load }: { id: string; load?: LoadOptions }) {
  const { data, problem } = useData<StepsData>("steps.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const s = data.steps.find((x) => x.id === id);
  if (!s) return <p role="alert">No step called {id}.</p>;
  return (
    <main>
      <p>
        <a href="#/steps">Every step</a>
      </p>
      <h1>{title(s)}</h1>
      <p className="purpose">{s.purpose}</p>
      <p>
        <span className="status">{s.status}</span>
        {s.report?.verdict ? ` · the report says ${s.report.verdict}` : ""}
      </p>
      {s.outcome && <p className="outcome">{s.outcome}</p>}
      {s.links.length > 0 && (
        <p className="links">
          {s.links.map((l) => (
            <a key={l.url} href={l.url} target="_blank" rel="noreferrer">
              {l.text}
            </a>
          ))}
        </p>
      )}
      {s.parts.length > 0 && (
        <table className="parts-of-step">
          <thead>
            <tr>
              <th scope="col">Part</th>
              <th scope="col">Status</th>
              <th scope="col">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {s.parts.map((p) => (
              <tr key={p.name}>
                <td>{p.name}</td>
                <td>{p.status}</td>
                <td>{p.outcome}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {s.stills.length > 0 && (
        <section aria-label="pictures" className="stills">
          {s.stills.map((src) => (
            <img key={src} src={`./data/${src}`} alt={src.split("/").pop()?.replace(".png", "")} loading="lazy" />
          ))}
        </section>
      )}
      {s.logs.length > 0 && (
        <section aria-label="the log">
          <h2>The log</h2>
          <ul>
            {s.logs.map((l) => (
              <li key={l.url}>
                <a href={l.url} target="_blank" rel="noreferrer">
                  {l.title}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
