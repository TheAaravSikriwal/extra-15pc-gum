// The corner menu: the docs, every page that isn't the drone view, grouped like a manual, one click
// away and out of the way.
import { useState } from "react";

import { MENU_GROUPS } from "./modes";

export function Menu() {
  const [open, setOpen] = useState(false);
  return (
    <div className="stage-menu">
      <button type="button" aria-expanded={open} aria-controls="stage-menu-list" onClick={() => setOpen(!open)}>
        Menu
      </button>
      {open && (
        <ul id="stage-menu-list" aria-label="pages">
          {MENU_GROUPS.map((g) => (
            <li key={g.name} className="menu-group">
              <span className="menu-group-name">{g.name}</span>
              <ul aria-label={g.name}>
                {g.pages.map((p) => (
                  <li key={p.route}>
                    <a href={`#/${p.route}`} onClick={() => setOpen(false)}>
                      {p.name}
                    </a>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
