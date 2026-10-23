// Hash routing (#/flights/base/hover), so every page works from a folder on disk and from any
// folder on the portfolio, with no server rewrites.
import { useEffect, useState } from "react";

// the route's parts: "#/flights/base/hover" is ["flights", "base", "hover"], "" or "#/" is []
export function parseHash(hash: string): string[] {
  return hash
    .replace(/^#\/?/, "")
    .split("/")
    .filter((part) => part.length > 0)
    .map(decodeURIComponent);
}

// Framed on the portfolio (wearechintu.com/drone, from the same origin), the page around it
// follows the route, so the address there is the one to share. Nothing is said to a page
// that isn't this site's own.
export function tellParent(hash: string, parent: Window = window.parent, self: Window = window): void {
  if (parent === self) return;
  try {
    parent.postMessage({ type: "drone:route", hash }, self.location.origin);
  } catch {
    // a frame from somewhere else: it hears nothing
  }
}

export function useRoute(): string[] {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    tellParent(window.location.hash);
    const follow = () => {
      setRoute(parseHash(window.location.hash));
      tellParent(window.location.hash);
    };
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);
  return route;
}
