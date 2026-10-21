// The data: each report's own data file, whole, as a tree. #/data is the list; #/data/cad is
// one of them.
import type { LoadOptions } from "../data/load";
import type { RawData, RawIndex } from "../data/types";
import { useData } from "../data/useData";
import { Tree } from "./Tree";

function One({ name, load }: { name: string; load?: LoadOptions }) {
  const { data, problem } = useData<RawData>(`raw/${name}.json`, load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <p className="links">
        <a href="#/data">All the data</a>
      </p>
      <h1>{data.source}</h1>
      <Tree value={data.data} />
    </main>
  );
}

export function Data({ name, load }: { name?: string; load?: LoadOptions }) {
  const { data, problem } = useData<RawIndex>("raw.json", load);
  if (name) return <One name={name} load={load} />;
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <h1>The data</h1>
      <p className="purpose">
        Every report's own data file, whole: every number the pages here are drawn from, and many they don't show.
      </p>
      <ul className="library">
        {data.files.map((f) => (
          <li key={f.name}>
            <a href={`#/data/${f.name}`}>{f.title}</a> <span className="muted">{f.source}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
