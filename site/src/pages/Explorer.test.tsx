import { fireEvent, render, screen } from "@testing-library/react";

import type { Parts, Wires } from "../data/types";
import { combinationFor, ExplorerView, type ViewState } from "./Explorer";

const PARTS: Parts = {
  schema_version: 1,
  glb: "drone.glb",
  pieces: [
    { name: "ark-gps", kind: "bought", module: "V", mass_g: 16, part_id: "ark-gps", moving: false,
      catalog: { role: "ark-gps", module: "V", id: "ark-gps", maker: "ARK Electronics",
                 model: "ARK GPS", mass_g: 16, price_usd: 225, link: null, count: 1 } },
  ],
};
const WIRES: Wires = { schema_version: 1, routes: [] };

test("the modules switched on name the combination", () => {
  expect(combinationFor(new Set())).toBe("base");
  expect(combinationFor(new Set(["V", "P"]))).toBe("mission");
  expect(combinationFor(new Set(["P", "V", "C"]))).toBe("max");
});

test("the panel switches modules, pulls the drone apart, and shows the picked part's card", () => {
  let seen: ViewState | null = null;
  render(
    <ExplorerView
      parts={PARTS}
      wires={WIRES}
      view={(s) => {
        seen = s;
        return <button type="button" onClick={() => s.select("ark-gps")}>pick the GPS</button>;
      }}
    />,
  );
  expect(seen!.combination).toBe("max");
  fireEvent.click(screen.getByLabelText("P"));
  expect(seen!.combination).toBe("V+C");
  fireEvent.change(screen.getByLabelText("pulled apart"), { target: { value: "0.5" } });
  expect(seen!.explode).toBe(0.5);
  fireEvent.click(screen.getByText("pick the GPS"));
  expect(screen.getByRole("heading", { name: "ARK Electronics ARK GPS" })).toBeInTheDocument();
  expect(screen.getByText("$225.00")).toBeInTheDocument();
});
