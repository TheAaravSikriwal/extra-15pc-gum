import { render, screen } from "@testing-library/react";

import { Bars, passes } from "./Bars";
import { Matrix } from "./Matrix";
import { TimeChart, visibleSpan } from "./TimeChart";

const HEIGHT = { name: "height", t: [0, 10, 20, 30], v: [0, 10, 10, 0] };

test("the time chart draws each series and puts the cursor at the clock's moment", () => {
  const { container } = render(
    <TimeChart title="Height" unit="m" series={[HEIGHT]} time={15} duration={30} width={300} />,
  );
  expect(container.querySelector('[data-series="height"]')?.getAttribute("d")).toMatch(/^M/);
  // 15 s of 30, between the margins at 44 and 288
  const cursor = Number(container.querySelector("[data-cursor]")?.getAttribute("x1"));
  expect(cursor).toBeCloseTo(44 + (288 - 44) / 2);
  expect(screen.getByRole("img", { name: "Height" })).toBeInTheDocument();
});

test("with a window it scrolls along with the clock, and holds at the ends", () => {
  expect(visibleSpan(5, 100, 20)).toEqual([0, 20]);
  expect(visibleSpan(50, 100, 20)).toEqual([30, 50]);
  expect(visibleSpan(120, 100, 20)).toEqual([80, 100]);
  expect(visibleSpan(50, 100)).toEqual([0, 100]);
});

test("the matrix shows each cell and links the flown ones", () => {
  render(
    <Matrix
      title="flights"
      rows={["hover", "payload grab"]}
      columns={["base", "C"]}
      cell={(r, c) => (r === "payload grab" && c === "base" ? "" : r === "hover" ? "pass" : "fail")}
      link={(r, c) => `#/flights/${c}/${r}`}
    />,
  );
  const cells = screen.getAllByRole("cell");
  expect(cells.map((c) => c.textContent)).toEqual(["pass", "pass", "", "fail"]);
  expect(screen.getAllByRole("link")[0]).toHaveAttribute("href", "#/flights/base/hover");
});

test("a bar passes on the right side of its limit", () => {
  expect(passes({ name: "hover", value: 33, limit: 21, unit: "min", higherIsBetter: true })).toBe(
    true,
  );
  expect(passes({ name: "current", value: 95, limit: 90, unit: "A", higherIsBetter: false })).toBe(
    false,
  );
  const { container } = render(
    <Bars
      title="checks"
      bars={[{ name: "Hover time", value: 33, limit: 21, unit: "min", higherIsBetter: true }]}
    />,
  );
  expect(container.querySelector('[data-bar="Hover time"]')?.getAttribute("data-passes")).toBe(
    "yes",
  );
});
