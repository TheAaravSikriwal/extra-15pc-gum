import { render, screen, within } from "@testing-library/react";

import type { Build as BuildData } from "../data/types";
import { Build } from "./Build";
import { money } from "./Parts";

const DATA: BuildData = {
  schema_version: 1,
  generated: "2026-10-21",
  totals: [
    { setup: "max", usd: 2172.29, unpriced: 1, printed: 14, printed_g: 140 },
    { setup: "base", usd: 876.78, unpriced: 2, printed: 9, printed_g: 74 },
    { setup: "once", usd: 361.99, unpriced: 1, printed: 0, printed_g: 0 },
  ],
  lines: [],
  guides: [{ name: "The wiring guide", url: "#/library/docs/build/wiring", about: "Every wire once." }],
  open: ["The claws"],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("what each combination costs, in the one order, what's bought once, and the guides on the site", async () => {
  render(<Build load={{ fromDisk: false, fetcher: answering(DATA) }} />);
  const costs = await screen.findByRole("region", { name: "What it costs" });
  const rows = within(costs).getAllByRole("row").slice(1);
  expect(rows.map((r) => r.firstChild?.textContent)).toEqual(["base", "max"]); // base first, whatever came first
  expect(within(costs).getByRole("cell", { name: "$876.78" })).toBeInTheDocument();
  expect(within(costs).getByText(/\$361\.99/)).toBeInTheDocument();
  const guides = screen.getByRole("region", { name: "the guides" });
  expect(within(guides).getByRole("link", { name: "The wiring guide" })).toHaveAttribute("href", "#/library/docs/build/wiring");
  expect(screen.getByRole("link", { name: "Parts" })).toHaveAttribute("href", "#/parts"); // the parts live there
});

test("money reads as dollars, and an unchecked price says so", () => {
  expect(money(1955.2)).toBe("$1,955.20");
  expect(money(null)).toBe("not priced");
});
