import { byCombination, COMBINATIONS } from "./order";

test("the combinations sort into one order, the sizing report's, whatever order they came in", () => {
  const found = ["max", "C", "mission", "base", "P+C", "V", "V+C", "P"];
  expect(byCombination(found, (x) => x)).toEqual(COMBINATIONS);
  expect(byCombination(["once", "V", "base"], (x) => x)).toEqual(["base", "V", "once"]);
});
