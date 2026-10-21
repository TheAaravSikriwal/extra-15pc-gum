// The corner menu: every page that isn't the drone view, one click away and out of the way.
import { useState } from "react";

import { MENU } from "./modes";

export function Menu() {
  const [open, setOpen] = useState(false);
  return (
    <div className="stage-menu">
      <button type="button" aria-expanded={open} aria-controls="stage-menu-list" onClick={() => setOpen(!open)}>
        Menu
      </button>
      {open && (
        <ul id="stage-menu-list" aria-label="pages">
          {MENU.map((p) => (
            <li key={p.route}>
              <a href={`#/${p.route}`} onClick={() => setOpen(false)}>
                {p.name}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
