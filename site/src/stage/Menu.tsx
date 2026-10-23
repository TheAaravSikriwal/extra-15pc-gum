// The docs' contents: every page that isn't the drone view, grouped like a manual. Over the drone
// view it's the corner menu, one click away and out of the way; on a page it's the contents down
// the side, always there, with the page you're on marked and its sections under it (the menu
// button stands in for it on a screen too narrow for both).
import { type ReactNode, useState } from "react";

import { MENU_GROUPS } from "./modes";
import { goTo, usePageSections } from "./sections";

function Groups({ current, onPick, under }: { current?: string; onPick?: () => void; under?: ReactNode }) {
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
                {p.route === current && under}
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

// the open page's sections, under its name: a click scrolls to one, and the one being read is marked
function Sections({ page }: { page: string }) {
  const { sections, active, pick } = usePageSections(page);
  if (!sections.length) return null;
  return (
    <ul className="page-sections" aria-label="this page's sections">
      {sections.map((s) => (
        <li key={s.id} className={s.level === 3 ? "sub" : undefined}>
          <a
            href={window.location.hash || "#/"}
            aria-current={s.id === active ? "location" : undefined}
            onClick={(e) => {
              e.preventDefault();
              pick(s.id);
              goTo(s.id);
            }}
          >
            {s.text}
          </a>
        </li>
      ))}
    </ul>
  );
}

export function Contents({ current, at = current }: { current: string; at?: string }) {
  return (
    <nav className="page-contents" aria-label="contents">
      <ul>
        <Groups current={current} under={<Sections page={at} />} />
      </ul>
    </nav>
  );
}
