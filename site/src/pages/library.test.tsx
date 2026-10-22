import { fireEvent, render, screen, within } from "@testing-library/react";

import { Data, size } from "./Data";
import { grouped, Library, splitPath } from "./Library";
import { MathPage } from "./MathPage";
import { leaf, Tree } from "./Tree";

function serving(files: Record<string, unknown>): typeof fetch {
  return (async (url: string) => {
    const name = String(url).replace("./data/", "");
    if (!(name in files)) return { ok: false, json: async () => ({}) };
    return { ok: true, json: async () => files[name] };
  }) as unknown as typeof fetch;
}

const doc = (path: string, title: string, extra: object = {}) => ({ path, title, section: "", url: "https://x", ...extra });
const LIBRARY = {
  schema_version: 1,
  sections: [
    { name: "The project", docs: [doc("README", "Extra 15pc Gum")] },
    {
      name: "1. Sizing and parts",
      group: "The work, by topic",
      step: "sizing",
      docs: [
        doc("docs/log/2026-10-21-x", "A day", { kind: "log", date: "2026-10-21" }),
        doc("docs/specs/2026-10-17-s", "The spec", { kind: "spec", date: "2026-10-17", superseded: "Partly superseded: by the next." }),
      ],
    },
    { name: "2. The CAD", group: "The work, by topic", step: "cad", docs: [doc("docs/log/2026-10-18-c", "A body")] },
    { name: "Behind the scenes", group: "Behind the scenes", about: "Notes for my machines.", docs: [doc("CLAUDE", "CLAUDE.md")] },
  ],
};
const PAGE = { schema_version: 1, path: "docs/log/2026-10-21-x", title: "A day", url: "https://x", html: '<h1 id="a-day">A day</h1><p>Words.</p>' };

test("the library groups the work by topic, each topic linking to its step", async () => {
  const load = { fromDisk: false, fetcher: serving({ "library.json": LIBRARY }) };
  render(<Library load={load} />);
  const work = await screen.findByRole("region", { name: "The work, by topic" });
  expect(within(work).getByRole("heading", { name: /1\. Sizing and parts/ })).toBeInTheDocument();
  expect(within(work).getAllByRole("link", { name: "the step" })[0]).toHaveAttribute("href", "#/steps/sizing");
  expect(within(work).getByRole("link", { name: "A day" })).toHaveAttribute("href", "#/library/docs/log/2026-10-21-x");
  expect(within(work).getByText("log, 2026-10-21")).toBeInTheDocument();
  expect(within(work).getByText("partly superseded")).toHaveAttribute("title", "Partly superseded: by the next.");
  const notes = screen.getByRole("region", { name: "Behind the scenes" });
  expect(within(notes).getByText("Notes for my machines.")).toBeInTheDocument();
  expect(grouped(LIBRARY.sections).map((g) => g.name)).toEqual(["The project", "The work, by topic", "Behind the scenes"]);
});

test("a doc renders its own HTML", async () => {
  const load = { fromDisk: false, fetcher: serving({ "library/docs/log/2026-10-21-x.json": PAGE }) };
  render(<Library path={["docs", "log", "2026-10-21-x"]} load={load} />);
  expect(await screen.findByText("Words.")).toBeInTheDocument();
  expect(splitPath(["docs", "decisions~the-unproven-list"])).toEqual({ path: "docs/decisions", heading: "the-unproven-list" });
});

const RAW = {
  schema_version: 1,
  files: [
    {
      name: "cad",
      title: "The CAD report's data",
      source: "docs/reports/cad/cad.json",
      url: "x",
      about: "Every combination's weight.",
      holds: ["verdict", "pieces (86)"],
      size_bytes: 2048,
    },
  ],
  site: [
    { name: "steps.json", about: "A page per step.", size_bytes: 5000, view: "steps" },
    { name: "flights/", about: "One run each.", size_bytes: 3 * 1024 * 1024, files: 198 },
  ],
};

test("the data lists each report's file and the site's own, with what each holds and its size", async () => {
  const files = {
    "raw.json": RAW,
    "raw/cad.json": { schema_version: 1, name: "cad", source: "docs/reports/cad/cad.json", data: { verdict: "pass", pieces: [{ name: "frame" }] } },
    "steps.json": { schema_version: 1, steps: [] },
  };
  const { unmount } = render(<Data load={{ fromDisk: false, fetcher: serving(files) }} />);
  expect(await screen.findByRole("link", { name: "The CAD report's data" })).toHaveAttribute("href", "#/data/cad");
  expect(screen.getByText("verdict, pieces (86)")).toBeInTheDocument();
  expect(screen.getByRole("cell", { name: "2 kB" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "steps.json" })).toHaveAttribute("href", "#/data/site/steps");
  expect(screen.getByRole("cell", { name: "3.0 MB, 198 files" })).toBeInTheDocument();
  unmount();
  const { unmount: done } = render(<Data name="cad" load={{ fromDisk: false, fetcher: serving(files) }} />);
  expect(await screen.findByText("pass")).toBeInTheDocument();
  done();
  render(<Data view="../../secrets" load={{ fromDisk: false, fetcher: serving(files) }} />);
  expect(screen.getByRole("alert")).toHaveTextContent("No data file called ../../secrets");
  expect(size(512)).toBe("512 B");
});

test("the math shows each module's explanation, its explained functions, then the rest by name", async () => {
  const math = {
    schema_version: 1,
    commit: "abc1234",
    packages: [{ name: "Sizing", key: "sizing", step: "1", modules: [{ path: "src/pcs14/sizing/flight.py", language: "Python",
      doc: "Flight time from the pack.", url: "https://x", items: [
        { name: "hover", kind: "function", signature: "hover(wh, watts)", doc: "Minutes of hover.", line: 4 },
        { name: "_helper", kind: "function", signature: "_helper(x)", doc: "", line: 2 },
      ] }] }],
  };
  render(<MathPage load={{ fromDisk: false, fetcher: serving({ "math.json": math }) }} />);
  const sizing = await screen.findByRole("region", { name: "Sizing" });
  expect(within(sizing).getByText("step 1")).toBeInTheDocument();
  expect(within(sizing).getByText("Flight time from the pack.")).toBeInTheDocument();
  expect(within(sizing).getByRole("link", { name: "hover(wh, watts)" })).toHaveAttribute("href", "https://x#L4");
  expect(within(sizing).getByText(/Without an explanation yet/)).toBeInTheDocument();
  expect(within(sizing).getByRole("link", { name: "_helper" })).toHaveAttribute("href", "https://x#L2");
  expect(screen.getByText(/commit abc1234/)).toBeInTheDocument();
});

test("a tree builds a branch only once it's opened", () => {
  render(<Tree value={{ a: 1, b: 2, c: 3, d: { deep: "inside" } }} />);
  expect(screen.queryByText("inside")).toBeNull();
  fireEvent.click(screen.getByText("d"));
  expect(leaf(0.1234567891)).toBe("0.123457");
});
