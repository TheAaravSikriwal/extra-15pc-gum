// The pages, by route.
import { Home } from "./pages/Home";
import { useRoute } from "./route";

export function App() {
  const route = useRoute();
  if (route.length === 0) return <Home />;
  return (
    <main>
      <p>No page at {route.join("/")} yet.</p>
      <a href="#/">Back to the start</a>
    </main>
  );
}
