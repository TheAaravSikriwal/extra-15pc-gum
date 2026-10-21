// The pages, by route, under one quiet line of links.
import { lazy, type ReactNode, Suspense } from "react";

import { Home } from "./pages/Home";
import { Spec } from "./pages/Spec";
import { useRoute } from "./route";

// the 3D page brings three.js, about a megabyte, so it loads only when someone opens it
const Explorer = lazy(() => import("./pages/Explorer").then((m) => ({ default: m.Explorer })));

export const PAGES: { route: string; name: string }[] = [
  { route: "", name: "Extra 15pc Gum" },
  { route: "drone", name: "The drone in 3D" },
  { route: "spec", name: "Spec sheet" },
];

export function pageFor(route: string[]): ReactNode {
  switch (route[0] ?? "") {
    case "":
      return <Home />;
    case "drone":
      return (
        <Suspense fallback={<p>Loading the drone</p>}>
          <Explorer />
        </Suspense>
      );
    case "spec":
      return <Spec />;
    default:
      return (
        <main>
          <p>No page at {route.join("/")} yet.</p>
          <a href="#/">Back to the start</a>
        </main>
      );
  }
}

export function App() {
  const route = useRoute();
  return (
    <>
      <nav aria-label="pages">
        {PAGES.map((p) => (
          <a key={p.route} href={`#/${p.route}`} aria-current={route[0] === p.route || (!route[0] && !p.route) ? "page" : undefined}>
            {p.name}
          </a>
        ))}
      </nav>
      {pageFor(route)}
    </>
  );
}
