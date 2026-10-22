// A page per step: what it's for, where it stands, its report as it stands now (its verdict in
// its own words, its key numbers and its sections), the outcome I wrote in the plan when it
// finished, its parts, pictures, learning topics and log, all from the README's plan, the
// reports and the log. Links to the repo's docs stay in the site's library.
import type { LoadOptions } from "../data/load";
import type { Link, Step, Steps as StepsData } from "../data/types";
import { useData } from "../data/useData";

export function stepLink(id: string): string {
  return `#/steps/${id}`;
}

export function stepTitle(s: Step): string {
  return s.number ? `${s.number}. ${s.name}` : s.name;
}

function LinkTo({ link }: { link: Link }) {
  const away = /^https?:/.test(link.url);
  return (
    <a href={link.url} {...(away ? { target: "_blank", rel: "noreferrer" } : {})}>
      {link.text}
    </a>
  );
}

function reportNow(s: Step): string {
  if (!s.report) return "";
  const { verdict, generated } = s.report;
  // the build package has no verdict, only its date
  return verdict ? [verdict, generated].filter(Boolean).join(", ") : `written ${generated ?? ""}`.trim();
}

// "stills/flight-sim/drop-wide.png" to "drop"
function stillName(src: string): string {
  const name = src.split("/").pop() ?? src;
  return name.replace(/\.png$/, "").replace(/-(wide|portrait|square|vertical)$/, "").replace(/-/g, " ");
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
      <p className="purpose">
        The plan, from the README, step by step. Each step's page has its report as it stands now, with its verdict,
        its key numbers and its sections; the outcome I wrote in the plan when it finished; its parts, pictures and log
        posts; and the topics behind it in the learning file. Side tracks start once their inputs exist and feed their
        numbers back, but never hold up the main line.
      </p>
      {groups.map(([name, list]) => (
        <section key={name} aria-label={name}>
          <h2>{name}</h2>
          <div className="scroll-x">
            <table className="steps-table">
              <thead>
                <tr>
                  <th scope="col">{name === "Side tracks" ? "Side track" : "Step"}</th>
                  <th scope="col">What it's for</th>
                  {name === "Side tracks" && <th scope="col">Starts after</th>}
                  <th scope="col">Status</th>
                  <th scope="col">Its report now</th>
                </tr>
              </thead>
              <tbody>
                {list.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <a href={stepLink(s.id)}>{stepTitle(s)}</a>
                    </td>
                    <td>{s.purpose}</td>
                    {name === "Side tracks" && <td>{s.starts_after}</td>}
                    <td>{s.status}</td>
                    <td className={s.report?.verdict === "fail" ? "fail" : undefined}>{reportNow(s)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
  const r = s.report;
  const done = /done/i.test(s.status);
  return (
    <main>
      <p className="links">
        <a href="#/steps">Every step</a>
      </p>
      <h1>{stepTitle(s)}</h1>
      {s.purpose && <p className="purpose">{s.purpose}</p>}
      <p className="status">
        {s.status}
        {s.starts_after ? ` · starts after ${s.starts_after.toLowerCase()}` : ""}
      </p>
      {r && (
        <section aria-label="the report now">
          <h2>The report now</h2>
          <p className="muted">
            From the report of {r.generated ?? "an unknown date"}
            {r.verdict ? `, which says ${r.verdict}` : ""}, in its own words and numbers.
          </p>
          {(r.says ?? []).map((p) => (
            <p key={p}>{p}</p>
          ))}
          {(r.numbers ?? []).length > 0 && (
            <dl className="numbers" aria-label="its key numbers">
              {(r.numbers ?? []).map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
          )}
          <p className="links">
            <a href={r.url}>the whole report</a>
            {(r.sections ?? []).map((l) => (
              <LinkTo key={l.url} link={l} />
            ))}
          </p>
        </section>
      )}
      {(s.outcome || s.links.length > 0) && (
        <section aria-label="the outcome">
          <h2>{done ? "The outcome, when it was done" : "Where it is"}</h2>
          {r && done && (
            <p className="muted">
              As I wrote it in the plan when the step finished. Where a number here differs from the report's above,
              the report's is current.
            </p>
          )}
          {s.outcome && <p className="outcome">{s.outcome}</p>}
          {s.links.length > 0 && (
            <p className="links">
              {s.links.map((l) => (
                <LinkTo key={l.url} link={l} />
              ))}
            </p>
          )}
        </section>
      )}
      {s.parts.length > 0 && (
        <section aria-label="its parts">
          <h2>Its parts</h2>
          <div className="scroll-x">
            <table className="parts-of-step">
              <thead>
                <tr>
                  <th scope="col">Part</th>
                  <th scope="col">What happens</th>
                  <th scope="col">Status</th>
                  <th scope="col">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {s.parts.map((p) => (
                  <tr key={p.name}>
                    <td>{p.name}</td>
                    <td>{p.what}</td>
                    <td>{p.status}</td>
                    <td>
                      {p.outcome}
                      {(p.links ?? []).length > 0 && (
                        <span className="links">
                          {(p.links ?? []).map((l) => (
                            <LinkTo key={l.url} link={l} />
                          ))}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      {s.stills.length > 0 && (
        <section aria-label="pictures">
          <h2>Pictures</h2>
          <div className="stills">
            {s.stills.map((src) => (
              <img key={src} src={`./data/${src}`} alt={stillName(src)} loading="lazy" />
            ))}
          </div>
        </section>
      )}
      {s.learning.length > 0 && (
        <section aria-label="to learn">
          <h2>The ideas behind it</h2>
          <p className="links learning">
            {s.learning.map((l) => (
              <LinkTo key={l.url} link={l} />
            ))}
          </p>
        </section>
      )}
      {s.logs.length > 0 && (
        <section aria-label="the log">
          <h2>The log</h2>
          <ul className="library">
            {s.logs.map((l) => (
              <li key={l.url}>
                <a href={l.url}>{l.title}</a>
                <span className="muted"> {l.date}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
