// The math: how each number is worked out, in the code's own words. Each Python module's
// explanation and each function's, and each firmware file's opening comment, with a link to the
// code itself.
import type { LoadOptions } from "../data/load";
import type { MathData } from "../data/types";
import { useData } from "../data/useData";

export function MathPage({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<MathData>("math.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <h1>The math</h1>
      <p className="purpose">
        How every number on this site is worked out, in the code's own explanations: each module, what it models and
        why, and each of its functions. The code is one click from each.
      </p>
      {data.packages.map((p) => (
        <section key={p.key} aria-label={p.name}>
          <h2>{p.name}</h2>
          {p.modules.map((m) => (
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
              {m.items.map((i) => (
                <div key={`${i.name}-${i.line}`} className="item">
                  <p>
                    <a href={`${m.url}#L${i.line}`} target="_blank" rel="noreferrer">
                      <code>{i.signature}</code>
                    </a>{" "}
                    <span className="muted">{i.kind}</span>
                  </p>
                  {i.doc ? <pre className="docstring">{i.doc}</pre> : null}
                </div>
              ))}
            </details>
          ))}
        </section>
      ))}
    </main>
  );
}
