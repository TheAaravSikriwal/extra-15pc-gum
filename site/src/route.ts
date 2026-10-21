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

export function useRoute(): string[] {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const follow = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);
  return route;
}
