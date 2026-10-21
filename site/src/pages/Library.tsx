// The library: every Markdown doc in the repo, rendered: the README, the status, the decisions,
// every report, the build package, every log post, spec and plan. #/library is the index;
// #/library/docs/log/x is a doc, and ~heading after it scrolls to that heading.
import { useEffect } from "react";

import type { LoadOptions } from "../data/load";
import type { Library as LibraryData, LibraryPage } from "../data/types";
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
        Every document in the project, as it's written in the repo: the plan and the status, every decision, every
        report in full, the build package, and every log post, spec and plan, in the order they happened.
      </p>
      {data.sections.map((s) => (
        <section key={s.name} aria-label={s.name}>
          <h2>{s.name}</h2>
          <ul className="library">
            {s.docs.map((d) => (
              <li key={d.path}>
                <a href={`#/library/${d.path}`}>{d.title}</a>
                {d.date ? <span className="muted"> {d.date}</span> : null}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
