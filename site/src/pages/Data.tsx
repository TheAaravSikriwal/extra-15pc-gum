// The data: each report's own data file, whole, and every file the site itself reads, each
// with what it holds and its size, and each opening as a tree. #/data is the list; #/data/cad
// is a report's file, and #/data/site/steps is one of the site's.
import type { LoadOptions } from "../data/load";
import type { RawData, RawIndex } from "../data/types";
import { useData } from "../data/useData";
import { Tree } from "./Tree";

export function size(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function Back() {
  return (
    <p className="links">
      <a href="#/data">All the data</a>
    </p>
  );
}

function Report({ name, load }: { name: string; load?: LoadOptions }) {
  const { data, problem } = useData<RawData>(`raw/${name}.json`, load);
  const index = useData<RawIndex>("raw.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  const file = index.data?.files.find((f) => f.name === name);
  return (
    <main>
      <Back />
      <h1>{file?.title ?? data.source}</h1>
      <p className="purpose">
        {file?.about ? `${file.about} ` : ""}
        From <code>{data.source}</code>
        {file?.size_bytes ? `, ${size(file.size_bytes)}` : ""}.
      </p>
      <Tree value={data.data} />
    </main>
  );
}

function SiteData({ view, load }: { view: string; load?: LoadOptions }) {
  const { data, problem } = useData<{ schema_version: number }>(`${view}.json`, load);
  const index = useData<RawIndex>("raw.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (data === undefined || data === null) return <p>Loading</p>;
  const file = index.data?.site?.find((f) => f.view === view);
  return (
    <main>
      <Back />
      <h1>{file?.name ?? `${view}.json`}</h1>
      {file && (
        <p className="purpose">
          {file.about} {size(file.size_bytes)}, made by pcs14 site.
        </p>
      )}
      <Tree value={data} />
    </main>
  );
}

// a file's name from the address, only ever a plain one inside the data folder
const PLAIN = /^[a-z0-9-]+$/;

export function Data({ name, view, load }: { name?: string; view?: string; load?: LoadOptions }) {
  const { data, problem } = useData<RawIndex>("raw.json", load);
  if (view !== undefined || name !== undefined) {
    const asked = view ?? name ?? "";
    if (!PLAIN.test(asked)) return <p role="alert">No data file called {asked}.</p>;
    return view !== undefined ? <SiteData view={view} load={load} /> : <Report name={asked} load={load} />;
  }
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main>
      <h1>The data</h1>
      <p className="purpose">
        Every number on this site comes from a data file. First each report's own, whole, as its step wrote it. Then
        the files the site itself reads, which pcs14 site makes from those, the logs and the design. Each opens as a
        tree. Each of the site's files also has a .js twin, the same data as a script, so the site works when it's
        opened straight from disk; the sizes leave those out.
      </p>
      <section aria-label="the reports' data">
        <h2>The reports' own data</h2>
        <div className="scroll-x">
          <table className="data-files">
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">What it holds</th>
                <th scope="col">Size</th>
              </tr>
            </thead>
            <tbody>
              {data.files.map((f) => (
                <tr key={f.name}>
                  <td>
                    <a href={`#/data/${f.name}`}>{f.title}</a>
                    <span className="holds">{f.source}</span>
                  </td>
                  <td>
                    {f.about}
                    {(f.holds ?? []).length > 0 && <span className="holds">{(f.holds ?? []).join(", ")}</span>}
                  </td>
                  <td>{f.size_bytes ? size(f.size_bytes) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {(data.site ?? []).length > 0 && (
        <section aria-label="the site's data">
          <h2>The site's own data</h2>
          <div className="scroll-x">
            <table className="data-files">
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">What it holds</th>
                  <th scope="col">Size</th>
                </tr>
              </thead>
              <tbody>
                {(data.site ?? []).map((f) => (
                  <tr key={f.name}>
                    <td>{f.view ? <a href={`#/data/site/${f.view}`}>{f.name}</a> : <code>{f.name}</code>}</td>
                    <td>{f.about}</td>
                    <td>
                      {size(f.size_bytes)}
                      {(f.files ?? 1) > 1 ? `, ${f.files} files` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}
