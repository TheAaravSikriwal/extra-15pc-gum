import { render, screen, within } from "@testing-library/react";

import type { Unproven as UnprovenData } from "../data/types";
import { countUnproven, Unproven } from "./Unproven";

const LIST: UnprovenData = {
  schema_version: 1,
  groups: [
    {
      name: "The whole drone",
      url: "https://github.com/x/docs/decisions.md",
      items: [{ what: "Real thrust", measure: "One motor and prop on a thrust stand" }],
    },
    {
      name: "3. Electrical design",
      url: "#/library/docs/reports/electrical/README",
      step: "electrical",
      items: [
        { what: "A dead short in the battery leads", measure: "" },
        { what: "The XT60's contact mass", measure: "" },
      ],
    },
  ],
};

function answering(body: unknown): typeof fetch {
  return (async () => ({ ok: true, json: async () => body })) as unknown as typeof fetch;
}

test("every group of what the sims can't prove, with what to measure first where it's known", async () => {
  render(<Unproven load={{ fromDisk: false, fetcher: answering(LIST) }} />);
  const drone = await screen.findByRole("region", { name: "The whole drone" });
  expect(within(drone).getByRole("cell", { name: "One motor and prop on a thrust stand" })).toBeInTheDocument();
  const electrical = screen.getByRole("region", { name: "3. Electrical design" });
  expect(within(electrical).getAllByRole("listitem")).toHaveLength(2);
  expect(within(electrical).getByRole("link", { name: "the step" })).toHaveAttribute("href", "#/steps/electrical");
  expect(within(electrical).getByRole("link", { name: "where it's written" })).toHaveAttribute("href", "#/library/docs/reports/electrical/README");
  expect(countUnproven(LIST)).toBe(3);
});
