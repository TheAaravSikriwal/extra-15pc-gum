import { DataError, loadData } from "./load";

function answering(body: unknown, ok = true): typeof fetch {
  return (async () => ({ ok, json: async () => body })) as unknown as typeof fetch;
}

afterEach(() => {
  delete window.pcs14Data;
});

test("a data file from this schema version loads", async () => {
  const data = await loadData<{ schema_version: number; files: string[] }>("index.json", {
    fromDisk: false,
    fetcher: answering({ schema_version: 1, files: ["spec.json"] }),
  });
  expect(data.files).toEqual(["spec.json"]);
});

test("a file from another schema version is refused, saying what makes the right one", async () => {
  await expect(
    loadData("index.json", { fromDisk: false, fetcher: answering({ schema_version: 2 }) }),
  ).rejects.toThrow(/schema version 2, not 1: rerun pcs14 site/);
});

test("a missing file says how to make it", async () => {
  await expect(
    loadData("index.json", { fromDisk: false, fetcher: answering({}, false) }),
  ).rejects.toBeInstanceOf(DataError);
});

test("opened from disk, it loads the file's script version instead of fetching", async () => {
  const asked: string[] = [];
  const loader = async (src: string) => {
    asked.push(src);
    window.pcs14Data = { "spec.json": { schema_version: 1, verdict: "pass" } };
  };
  const data = await loadData<{ schema_version: number; verdict: string }>("spec.json", {
    fromDisk: true,
    loader,
  });
  expect(asked).toEqual(["./data/spec.js"]);
  expect(data.verdict).toBe("pass");
});

test("from disk, a script that isn't there says how to make it", async () => {
  const loader = async () => {
    throw new Error("404");
  };
  await expect(loadData("spec.json", { fromDisk: true, loader })).rejects.toThrow(/pcs14 site/);
});
