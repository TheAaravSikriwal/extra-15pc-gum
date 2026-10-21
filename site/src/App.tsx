// The drone view, always there, and the pages that open over it, by route.
import { lazy, type ReactNode, Suspense } from "react";

import { Build } from "./pages/Build";
import { Catalog } from "./pages/Catalog";
import { Data } from "./pages/Data";
import { Flights } from "./pages/Flights";
import { Library } from "./pages/Library";
import { MathPage } from "./pages/MathPage";
import { Spec } from "./pages/Spec";
import { StepPage, Steps } from "./pages/Steps";
import { Tunnel } from "./pages/Tunnel";
import { Unproven } from "./pages/Unproven";
import { Wiring } from "./pages/Wiring";
import { useRoute } from "./route";
import { Menu } from "./stage/Menu";
import { modeOf } from "./stage/modes";
import { Stage } from "./stage/Stage";

// the flight pages bring three.js, about a megabyte, so they load only when opened
const FlightRun = lazy(() => import("./pages/FlightRun").then((m) => ({ default: m.FlightRun })));

export function pageFor(route: string[]): ReactNode {
  switch (route[0] ?? "") {
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
    case "library":
      return <Library path={route.slice(1)} />;
    case "catalog":
      return <Catalog />;
    case "data":
      return <Data name={route[1]} />;
    case "math":
      return <MathPage />;
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
  const mode = modeOf(route);
  return (
    <>
      <Stage route={route} />
      {mode === "page" && (
        <div className="page-over">
          <nav className="page-back" aria-label="back">
            <a href="#/">Back to the drone</a>
            <Menu />
          </nav>
          {pageFor(route)}
        </div>
      )}
    </>
  );
}
