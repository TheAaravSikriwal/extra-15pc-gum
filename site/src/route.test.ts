import { parseHash, tellParent } from "./route";

test("a hash route splits into its parts", () => {
  expect(parseHash("#/flights/base/hover")).toEqual(["flights", "base", "hover"]);
  expect(parseHash("#/flights/V%2BC/hover")).toEqual(["flights", "V+C", "hover"]);
  expect(parseHash("")).toEqual([]);
  expect(parseHash("#/")).toEqual([]);
});

test("framed on the portfolio, the route is told to the page around it, on this origin only", () => {
  const said: [unknown, string][] = [];
  const parent = { postMessage: (data: unknown, origin: string) => said.push([data, origin]) } as unknown as Window;
  tellParent("#/flights", parent);
  expect(said).toEqual([[{ type: "drone:route", hash: "#/flights" }, window.location.origin]]);
  tellParent("#/spec", window, window); // not framed: nothing to tell
  expect(said).toHaveLength(1);
});
