// The docs' contents: every page that isn't the drone view, grouped like a manual. Over the drone
// view it's the corner menu, one click away and out of the way; on a page it's the contents down
// the side, always there, with the page you're on marked (the menu button stands in for it on a
// screen too narrow for both).
import { useState } from "react";

import { MENU_GROUPS } from "./modes";

function Groups({ current, onPick }: { current?: string; onPick?: () => void }) {
  return (
    <>
      {MENU_GROUPS.map((g) => (
        <li key={g.name} className="menu-group">
          <span className="menu-group-name">{g.name}</span>
          <ul aria-label={g.name}>
            {g.pages.map((p) => (
              <li key={p.route}>
                <a href={`#/${p.route}`} aria-current={p.route === current ? "page" : undefined} onClick={onPick}>
                  {p.name}
                </a>
              </li>
            ))}
          </ul>
        </li>
      ))}
    </>
  );
}

export function Menu({ current }: { current?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="stage-menu">
      <button type="button" aria-expanded={open} aria-controls="stage-menu-list" onClick={() => setOpen(!open)}>
        Menu
      </button>
      {open && (
        <ul id="stage-menu-list" aria-label="pages">
          <Groups current={current} onPick={() => setOpen(false)} />
        </ul>
      )}
    </div>
  );
}

export function Contents({ current }: { current: string }) {
  return (
    <nav className="page-contents" aria-label="contents">
      <ul>
        <Groups current={current} />
      </ul>
    </nav>
  );
}
