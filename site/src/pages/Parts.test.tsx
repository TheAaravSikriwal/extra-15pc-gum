import { fireEvent, render, screen, within } from "@testing-library/react";

import type { PartsList } from "../data/types";
import { linked, Parts } from "./Parts";

const motor = { id: "emax-e3-2814-850kv", type: "motor", maker: "Emax", model: "E3 2814 850KV", mass_g: 82, price_usd: 37.99, link: null, record: { kv: 850 } };
const LIST: PartsList = {
  schema_version: 1,
  generated: "2026-10-21",
  lines: [
    { module: "base", group: "bought", name: "Motor", qty: 4, unit: "", maker: "Emax", model: "E3 2814 850KV", link: "https://x/motor",
      price_each_usd: 37.99, total_usd: 151.96, checked: "2026-10-21", fallback: "[iFlight XING 2814](https://x/xing): the same mount",
      note: "out of stock on the day", catalog_id: "emax-e3-2814-850kv", mass_g: 82 },
    { module: "base", group: "hardware", name: "M3 x 10 screw, nylon", qty: 8, unit: "", maker: "Any", model: "M3 x 10 screw",
      fallback: "", note: "" },
    { module: "V", group: "printed", name: "v housing", qty: 1, unit: "", maker: "Printed", model: "PETG-CF", fallback: "", note: "" },
  ],
  used: [motor],
  alternatives: [{ id: "molicel-p42a", type: "cell", maker: "Molicel", model: "INR-21700-P42A", mass_g: 66.5, price_usd: 5.99, link: null, record: {} }],
}; // prettier-ignore

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("everything on the drone, by module and kind, the screws and the prints too", async () => {
  render(<Parts load={{ fromDisk: false, fetcher: answering(LIST) }} />);
  const base = await screen.findByRole("region", { name: "Base" });
  expect(within(base).getByRole("table", { name: "Base: Bought" })).toHaveTextContent("Motor");
  expect(within(base).getByRole("table", { name: "Base: Screws, nuts and the rest" })).toHaveTextContent("M3 x 10 screw");
  expect(screen.getByRole("table", { name: "V: vision and navigation: Printed" })).toHaveTextContent("v housing");
  expect(within(base).getByText("$37.99")).toBeInTheDocument();
  expect(within(base).getByText("82 g")).toBeInTheDocument();
});

test("a line opens to its note, its fallback with its links, and its catalog entry", async () => {
  render(<Parts load={{ fromDisk: false, fetcher: answering(LIST) }} />);
  fireEvent.click(await screen.findByText("Motor"));
  expect(screen.getByText("out of stock on the day")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "iFlight XING 2814" })).toHaveAttribute("href", "https://x/xing");
  expect(screen.getByText("Its catalog entry, every field")).toBeInTheDocument();
});

test("the rest of the catalog is there too, as what wasn't picked", async () => {
  render(<Parts load={{ fromDisk: false, fetcher: answering(LIST) }} />);
  const rest = await screen.findByRole("region", { name: "not on the drone" });
  expect(within(rest).getByRole("region", { name: "Cells" })).toHaveTextContent("INR-21700-P42A");
});

test("Markdown links in a fallback become links, the rest stays text", () => {
  render(<p>{linked("[A](https://a) or [B](https://b), either")}</p>);
  expect(screen.getByRole("link", { name: "A" })).toHaveAttribute("href", "https://a");
  expect(screen.getByText(/either/)).toBeInTheDocument();
});
