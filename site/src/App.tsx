// The pages, by route, under one quiet line of links.
import { lazy, type ReactNode, Suspense } from "react";

import { Build } from "./pages/Build";
import { Flights } from "./pages/Flights";
import { Home } from "./pages/Home";
import { Spec } from "./pages/Spec";
import { StepPage, Steps } from "./pages/Steps";
import { Tunnel } from "./pages/Tunnel";
import { Unproven } from "./pages/Unproven";
import { Wiring } from "./pages/Wiring";
import { useRoute } from "./route";

// the 3D page brings three.js, about a megabyte, so it loads only when someone opens it
const Explorer = lazy(() => import("./pages/Explorer").then((m) => ({ default: m.Explorer })));
const FlightRun = lazy(() => import("./pages/FlightRun").then((m) => ({ default: m.FlightRun })));

export const PAGES: { route: string; name: string }[] = [
  { route: "", name: "Extra 15pc Gum" },
  { route: "drone", name: "The drone in 3D" },
  { route: "spec", name: "Spec sheet" },
  { route: "wiring", name: "The wiring" },
  { route: "flights", name: "Every flight" },
  { route: "steps", name: "Every step" },
  { route: "tunnel", name: "The wind tunnel" },
  { route: "unproven", name: "What it can't prove" },
  { route: "build", name: "Build it" },
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
    case "flights":
      if (route.length >= 3) {
        return (
          <Suspense fallback={<p>Loading the flight</p>}>
            <FlightRun setup={route[1]} scenario={route[2]} />
          </Suspense>
        );
      }
      return <Flights />;
    case "steps":
      return route[1] ? <StepPage id={route[1]} /> : <Steps />;
    case "tunnel":
      return <Tunnel />;
    case "unproven":
      return <Unproven />;
    case "build":
      return <Build />;
    case "wiring":
      return <Wiring board={route[1]} />;
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
