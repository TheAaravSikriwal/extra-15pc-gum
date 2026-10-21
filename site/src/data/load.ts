// Reading the data files pcs14 site writes into public/data, next to the page. Served over
// http, the page fetches the JSON. Opened from a folder on disk (file://), browsers won't let
// it fetch, so it adds the same data's script version (name.js) as a script tag, which hands
// the data over on window.pcs14Data.
import { SCHEMA_VERSION } from "./types";

export class DataError extends Error {}

declare global {
  interface Window {
    pcs14Data?: Record<string, unknown>;
  }
}

export type ScriptLoader = (src: string) => Promise<void>;

function addScript(src: string): Promise<void> {
  return new Promise((done, failed) => {
    const tag = document.createElement("script");
    tag.src = src;
    tag.onload = () => done();
    tag.onerror = () => failed(new Error(src));
    document.head.appendChild(tag);
  });
}

async function viaFetch(name: string, fetcher: typeof fetch): Promise<unknown> {
  const reply = await fetcher(`./data/${name}`);
  if (!reply.ok) throw new DataError(`no ${name}: run pcs14 site`);
  return reply.json();
}

async function viaScript(name: string, loader: ScriptLoader): Promise<unknown> {
  const held = window.pcs14Data?.[name];
  if (held !== undefined) return held;
  try {
    await loader(`./data/${name.replace(/\.json$/, ".js")}`);
  } catch {
    throw new DataError(`no ${name}: run pcs14 site`);
  }
  const loaded = window.pcs14Data?.[name];
  if (loaded === undefined) throw new DataError(`${name} didn't load: rerun pcs14 site`);
  return loaded;
}

export interface LoadOptions {
  fetcher?: typeof fetch;
  fromDisk?: boolean; // the page was opened as file://
  loader?: ScriptLoader;
}

// a data file, refused if it was written with another schema version
export async function loadData<T extends { schema_version: number }>(
  name: string,
  options: LoadOptions = {},
): Promise<T> {
  const fromDisk = options.fromDisk ?? window.location.protocol === "file:";
  const data = (
    fromDisk
      ? await viaScript(name, options.loader ?? addScript)
      : await viaFetch(name, options.fetcher ?? fetch)
  ) as T;
  if (data.schema_version !== SCHEMA_VERSION) {
    throw new DataError(
      `${name} is schema version ${data.schema_version}, not ${SCHEMA_VERSION}: rerun pcs14 site`,
    );
  }
  return data;
}
