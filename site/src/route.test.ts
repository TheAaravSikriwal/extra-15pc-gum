import { parseHash } from "./route";

test("a hash route splits into its parts", () => {
  expect(parseHash("#/flights/base/hover")).toEqual(["flights", "base", "hover"]);
  expect(parseHash("#/flights/V%2BC/hover")).toEqual(["flights", "V+C", "hover"]);
  expect(parseHash("")).toEqual([]);
  expect(parseHash("#/")).toEqual([]);
});
