// The math: how the numbers are worked out, in the code's own words, in step order. Each math
// module's explanation, then its functions, the ones that explain themselves first, and each
// firmware file's opening comment, with links to the code pinned to the commit the site was
// built from.
import type { LoadOptions } from "../data/load";
import type { MathData, MathItem } from "../data/types";
import { useData } from "../data/useData";

function stepOf(step?: string): string {
  if (!step) return "";
  return step === "side track" ? "a side track" : `step ${step}`;
}

export function MathPage({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<MathData>("math.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const pinned = data.commit ? `commit ${data.commit}, the one this site was built from` : "the main branch";
  return (
    <main>
      <h1>The math</h1>
      <p className="purpose">
        How the numbers are worked out, in the code's own explanations, in step order: each module's opening note, then
        its functions. Only the code that does the math is here, not the code that writes the reports, the site or the
        command line. Not every function explains itself yet; those are listed by name after the ones that do. The links
        go to the code at {pinned}, so each line stays right as the code moves on.
      </p>
      {data.packages.map((p) => (
        <section key={p.key} aria-label={p.name}>
          <h2>{p.name}</h2>
          {p.step && <p className="muted">{stepOf(p.step)}</p>}
          {p.modules.map((m) => {
            const told = m.items.filter((i) => i.doc);
            const untold = m.items.filter((i) => !i.doc);
            const at = (i: MathItem) => `${m.url}#L${i.line}`;
            return (
              <details key={m.path} className="module">
                <summary>
                  <code>{m.path}</code>
                </summary>
                <p className="links">
                  <a href={m.url} target="_blank" rel="noreferrer">
                    the code
                  </a>
                </p>
                {m.doc ? <pre className="docstring">{m.doc}</pre> : null}
                {told.map((i) => (
                  <div key={`${i.name}-${i.line}`} className="item">
                    <p>
                      <a href={at(i)} target="_blank" rel="noreferrer">
                        <code>{i.signature}</code>
                      </a>{" "}
                      <span className="muted">{i.kind}</span>
                    </p>
                    <pre className="docstring">{i.doc}</pre>
                  </div>
                ))}
                {untold.length > 0 && (
                  <p className="muted untold">
                    Without an explanation yet:{" "}
                    {untold.map((i, k) => (
                      <span key={`${i.name}-${i.line}`}>
                        {k > 0 ? ", " : ""}
                        <a href={at(i)} target="_blank" rel="noreferrer">
                          <code>{i.name}</code>
                        </a>
                      </span>
                    ))}
                  </p>
                )}
              </details>
            );
          })}
        </section>
      ))}
    </main>
  );
}
