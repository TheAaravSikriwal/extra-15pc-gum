import { fireEvent, render, screen } from "@testing-library/react";

import type { Parts, SpecSheet, Wires } from "../data/types";
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

test("a part can be picked from the keyboard too, not only by a click in 3D", () => {
  let seen: ViewState | null = null;
  render(
    <ExplorerView
      parts={PARTS}
      wires={WIRES}
      view={(s) => {
        seen = s;
        return null;
      }}
    />,
  );
  fireEvent.change(screen.getByLabelText("part"), { target: { value: "ark-gps" } });
  expect(seen!.selected).toBe("ark-gps");
  expect(screen.getByText(/ARK Electronics/)).toBeInTheDocument();
  // a part whose module is switched off isn't on the list
  fireEvent.click(screen.getByLabelText("V"));
  expect(screen.queryByRole("option", { name: "ark-gps" })).toBeNull();
});

const SPEC = {
  schema_version: 1,
  combinations: [
    ["max", 2620.3, 22.8, 19.7, "fail"],
    ["V+C", 2398.4, 25.1, 21.9, "pass"],
  ].map(([name, mass, hover, worst, verdict]) => ({
    name,
    verdict,
    mass_g: mass,
    cad_mass_g: null,
    checks: [{ name: "Hover time", unit: "min", nominal: hover, pessimistic: worst, verdict: "pass" }],
  })),
} as unknown as SpecSheet;

test("the weight, the hover time and the verdict follow the modules switched on", () => {
  render(<ExplorerView parts={PARTS} wires={WIRES} spec={SPEC} view={() => null} />);
  expect(screen.getByText(/max: 2620 g, hovers 22.8 min \(19.7 pessimistic\), fail/)).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText("P"));
  expect(screen.getByText(/V\+C: 2398 g, hovers 25.1 min \(21.9 pessimistic\), pass/)).toBeInTheDocument();
});

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
