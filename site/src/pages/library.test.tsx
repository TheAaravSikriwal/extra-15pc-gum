import { fireEvent, render, screen, within } from "@testing-library/react";

import { Catalog } from "./Catalog";
import { Data } from "./Data";
import { Library, splitPath } from "./Library";
import { MathPage } from "./MathPage";
import { leaf, Tree } from "./Tree";

function serving(files: Record<string, unknown>): typeof fetch {
  return (async (url: string) => {
    const name = String(url).replace("./data/", "");
    if (!(name in files)) return { ok: false, json: async () => ({}) };
    return { ok: true, json: async () => files[name] };
  }) as unknown as typeof fetch;
}

const LIBRARY = {
  schema_version: 1,
  sections: [
    {
      name: "The log",
      docs: [{ path: "docs/log/2026-10-21-x", title: "A day", section: "The log", url: "https://x", date: "2026-10-21" }],
    },
  ],
};
const PAGE = { schema_version: 1, path: "docs/log/2026-10-21-x", title: "A day", url: "https://x", html: '<h1 id="a-day">A day</h1><p>Words.</p>' };

test("the library lists every doc by section, and a doc renders its own HTML", async () => {
  const load = { fromDisk: false, fetcher: serving({ "library.json": LIBRARY, "library/docs/log/2026-10-21-x.json": PAGE }) };
  const { unmount } = render(<Library load={load} />);
  const log = await screen.findByRole("region", { name: "The log" });
  expect(within(log).getByRole("link", { name: "A day" })).toHaveAttribute("href", "#/library/docs/log/2026-10-21-x");
  unmount();
  render(<Library path={["docs", "log", "2026-10-21-x"]} load={load} />);
  expect(await screen.findByText("Words.")).toBeInTheDocument();
  expect(splitPath(["docs", "decisions~the-unproven-list"])).toEqual({ path: "docs/decisions", heading: "the-unproven-list" });
});

test("every catalog part opens to all its fields", async () => {
  const catalog = {
    schema_version: 1,
    parts: [{ id: "m", type: "motor", maker: "Emax", model: "E3 2814", mass_g: 82, price_usd: 37.99, link: null,
              record: { kv: 850, source: { kind: "manufacturer" } } }],
  };
  render(<Catalog load={{ fromDisk: false, fetcher: serving({ "catalog.json": catalog }) }} />);
  const motors = await screen.findByRole("region", { name: "Motors" });
  expect(within(motors).getByText("Emax")).toBeInTheDocument();
  expect(within(motors).getByText("850")).toBeInTheDocument();
});

test("the data lists each report's file and shows one as a tree", async () => {
  const files = {
    "raw.json": { schema_version: 1, files: [{ name: "cad", title: "The CAD", source: "docs/reports/cad/cad.json", url: "x" }] },
    "raw/cad.json": { schema_version: 1, name: "cad", source: "docs/reports/cad/cad.json", data: { verdict: "pass", pieces: [{ name: "frame" }] } },
  };
  const { unmount } = render(<Data load={{ fromDisk: false, fetcher: serving(files) }} />);
  expect(await screen.findByRole("link", { name: "The CAD" })).toHaveAttribute("href", "#/data/cad");
  unmount();
  render(<Data name="cad" load={{ fromDisk: false, fetcher: serving(files) }} />);
  expect(await screen.findByText("pass")).toBeInTheDocument();
});

test("the math shows each module's explanation and its functions", async () => {
  const math = {
    schema_version: 1,
    packages: [{ name: "Sizing", key: "sizing", modules: [{ path: "src/pcs14/sizing/flight.py", language: "Python",
      doc: "Flight time from the pack.", url: "https://x", items: [{ name: "hover", kind: "function",
      signature: "hover(wh, watts)", doc: "Minutes of hover.", line: 4 }] }] }],
  };
  render(<MathPage load={{ fromDisk: false, fetcher: serving({ "math.json": math }) }} />);
  const sizing = await screen.findByRole("region", { name: "Sizing" });
  expect(within(sizing).getByText("Flight time from the pack.")).toBeInTheDocument();
  expect(within(sizing).getByRole("link", { name: "hover(wh, watts)" })).toHaveAttribute("href", "https://x#L4");
});

test("a tree builds a branch only once it's opened", () => {
  render(<Tree value={{ a: 1, b: 2, c: 3, d: { deep: "inside" } }} />);
  expect(screen.queryByText("inside")).toBeNull();
  fireEvent.click(screen.getByText("d"));
  expect(leaf(0.1234567891)).toBe("0.123457");
});
