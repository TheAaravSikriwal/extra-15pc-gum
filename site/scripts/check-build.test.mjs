import { absoluteLinks, namedFiles } from "./check-build.mjs";

test("relative links pass, and absolute ones are caught", () => {
  const html =
    '<script src="./assets/index.js"></script><link href="./assets/a.css">' +
    '<script src="/assets/x.js"></script><a href="https://example.com/">x</a>';
  expect(absoluteLinks(html)).toEqual(["/assets/x.js", "https://example.com/"]);
});

test("the files the page names are its scripts and stylesheets", () => {
  const html =
    '<script type="module" src="./assets/index-1.js"></script>' +
    '<link rel="stylesheet" href="./assets/index-2.css"><link rel="icon" href="./favicon.svg">';
  expect(namedFiles(html)).toEqual(["assets/index-1.js", "assets/index-2.css"]);
});
