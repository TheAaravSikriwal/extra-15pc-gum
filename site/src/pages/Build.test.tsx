import { render, screen, within } from "@testing-library/react";

import type { Build as BuildData } from "../data/types";
import { Build, money } from "./Build";

const LINE = { unit: "", maker: "Emax", model: "E3 2814", link: null, checked: null, fallback: "", note: "" };
const DATA: BuildData = {
  schema_version: 1,
  generated: "2026-10-21",
  totals: [
    { setup: "base", usd: 764.34, unpriced: 2, printed: 9, printed_g: 74 },
    { setup: "once", usd: 100, unpriced: 1, printed: 0, printed_g: 0 },
  ],
  lines: [
    { ...LINE, module: "base", group: "bought", name: "Motor", qty: 4, price_each_usd: 37.99, total_usd: 151.96,
      link: "https://example.com/motor", fallback: "[Other motor](https://x) : heavier" },
    { ...LINE, module: "base", group: "hardware", name: "M3 x 12 screw", qty: 8 },
    { ...LINE, module: "once", group: "ground", name: "Transmitter", qty: 1, price_each_usd: null },
  ],
  guides: [{ name: "The wiring guide", url: "https://github.com/x/docs/build/wiring.md" }],
  open: ["The claws"],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("the totals, each module's parts with a buy link, and what's bought once", async () => {
  render(<Build load={{ fromDisk: false, fetcher: answering(DATA) }} />);
  const costs = await screen.findByRole("region", { name: "What it costs" });
  expect(within(costs).getByRole("cell", { name: "$764.34" })).toBeInTheDocument();
  expect(within(costs).queryByRole("cell", { name: "once" })).toBeNull();
  const base = screen.getByRole("region", { name: "Base" });
  expect(within(base).getByRole("link", { name: "Motor" })).toHaveAttribute("href", "https://example.com/motor");
  expect(within(base).queryByText("M3 x 12 screw")).toBeNull(); // screws stay in the guide
  expect(within(base).getByText("Other motor : heavier")).toBeInTheDocument();
  const once = screen.getByRole("region", { name: "Bought once" });
  expect(within(once).getByRole("cell", { name: "?" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "The wiring guide" })).toBeInTheDocument();
});

test("money reads as dollars, and an unchecked price as a question mark", () => {
  expect(money(1955.2)).toBe("$1,955.20");
  expect(money(null)).toBe("?");
});
