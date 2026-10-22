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
  // a server that answers a missing file with the site's own page sends HTML, not data
  try {
    return await reply.json();
  } catch {
    throw new DataError(`no ${name}: run pcs14 site`);
  }
}

// a data file's script version: spec.json comes as spec.js, drone.glb as drone.glb.js
export function scriptFor(name: string): string {
  return name.endsWith(".json") ? name.replace(/\.json$/, ".js") : `${name}.js`;
}

async function viaScript(name: string, loader: ScriptLoader): Promise<unknown> {
  const held = window.pcs14Data?.[name];
  if (held !== undefined) return held;
  try {
    await loader(`./data/${scriptFor(name)}`);
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

// base64, as the binary files' script versions carry them, back into bytes
export function fromBase64(text: string): ArrayBuffer {
  const raw = atob(text);
  const bytes = new Uint8Array(raw.length);
  for (let k = 0; k < raw.length; k++) bytes[k] = raw.charCodeAt(k);
  return bytes.buffer;
}

// a binary data file (the 3D model): fetched, or from its script version on disk
export async function loadBinary(name: string, options: LoadOptions = {}): Promise<ArrayBuffer> {
  const fromDisk = options.fromDisk ?? window.location.protocol === "file:";
  if (fromDisk) return fromBase64((await viaScript(name, options.loader ?? addScript)) as string);
  const reply = await (options.fetcher ?? fetch)(`./data/${name}`);
  if (!reply.ok) throw new DataError(`no ${name}: run npm run glb`);
  return reply.arrayBuffer();
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
