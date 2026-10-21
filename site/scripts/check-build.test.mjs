import { absoluteLinks } from "./check-build.mjs";

test("relative links pass, and absolute ones are caught", () => {
  const html =
    '<script src="./assets/index.js"></script><link href="./assets/a.css">' +
    '<script src="/assets/x.js"></script><a href="https://example.com/">x</a>';
  expect(absoluteLinks(html)).toEqual(["/assets/x.js", "https://example.com/"]);
});
