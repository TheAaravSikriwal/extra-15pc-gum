// The library: every Markdown doc in the repo, rendered. The project's own docs, the reports and
// the build package first; then the work by topic, each step's specs, plans and log posts
// together, the newest topic first; then the repo's folders and the notes behind the scenes.
// #/library is the index; #/library/docs/log/x is a doc, and ~heading after it scrolls to that
// heading.
import { useEffect } from "react";

import type { LoadOptions } from "../data/load";
import type { Library as LibraryData, LibraryDoc, LibraryPage, LibrarySection } from "../data/types";
import { useData } from "../data/useData";

export function splitPath(parts: string[]): { path: string; heading: string | null } {
  const joined = parts.join("/");
  const [path, heading] = joined.split("~");
  return { path, heading: heading ?? null };
}

function Doc({ path, heading, load }: { path: string; heading: string | null; load?: LoadOptions }) {
  const { data, problem } = useData<LibraryPage>(`library/${path}.json`, load);
  useEffect(() => {
    if (!data) return;
    if (heading) document.getElementById(heading)?.scrollIntoView();
    else document.documentElement.scrollTop = 0;
  }, [data, heading]);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <p className="links">
        <a href="#/library">The library</a>
        <a href={data.url} target="_blank" rel="noreferrer">
          on GitHub
        </a>
      </p>
      {/* the repo's own docs, turned to HTML by pcs14 site with everything else escaped */}
      <article className="doc" dangerouslySetInnerHTML={{ __html: data.html }} />
    </main>
  );
}

function DocLine({ d }: { d: LibraryDoc }) {
  const partly = d.superseded?.toLowerCase().startsWith("partly");
  return (
    <li>
      <a href={`#/library/${d.path}`}>{d.title}</a>
      <span className="muted">{[d.kind, d.date].filter(Boolean).join(", ")}</span>
      {d.superseded && (
        <span className="superseded" title={d.superseded}>
          {partly ? "partly superseded" : "superseded"}
        </span>
      )}
    </li>
  );
}

// the sections in order, the ones that share a group under its one heading
export function grouped(sections: LibrarySection[]): { name: string; about: string; sections: LibrarySection[] }[] {
  const out: { name: string; about: string; sections: LibrarySection[] }[] = [];
  for (const s of sections) {
    const last = out[out.length - 1];
    if (s.group && last && last.name === s.group) last.sections.push(s);
    else out.push({ name: s.group || s.name, about: s.about ?? "", sections: [s] });
  }
  return out;
}

export function Library({ path = [], load }: { path?: string[]; load?: LoadOptions }) {
  const { data, problem } = useData<LibraryData>("library.json", load);
  if (path.length) {
    const { path: doc, heading } = splitPath(path);
    return <Doc path={doc} heading={heading} load={load} />;
  }
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <h1>The library</h1>
      <p className="purpose">
        Every document in the project, as it's written in the repo. First the project's own (the plan, the status, the
        decisions, the roadmap), every report in full and the build package. Then the work by topic: each step's specs,
        plans and log posts together, the newest topic first. Last, what each of the repo's folders holds, and the notes
        behind the scenes. A doc that something later replaced, in whole or in part, is marked, and says what replaced
        it at its top.
      </p>
      {grouped(data.sections).map((g) => (
        <section key={g.name} aria-label={g.name}>
          <h2>{g.name}</h2>
          {g.about && <p className="muted">{g.about}</p>}
          {g.sections.map((s) => (
            <div key={s.name} className="library-section">
              {g.sections.length > 1 || s.name !== g.name ? (
                <h3>
                  {s.name}
                  {s.step && (
                    <a className="step-link" href={`#/steps/${s.step}`}>
                      the step
                    </a>
                  )}
                </h3>
              ) : null}
              <ul className="library">
                {s.docs.map((d) => (
                  <DocLine key={d.path} d={d} />
                ))}
              </ul>
            </div>
          ))}
        </section>
      ))}
    </main>
  );
}
