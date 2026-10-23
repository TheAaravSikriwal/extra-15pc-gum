// The sections of the page that's open, for the contents down its side: read from the page's own
// headings, so nothing is listed twice and a page's sections are whatever it shows. Its main
// headings always; its sub-headings too when it has only a few main ones.
import { useEffect, useState } from "react";

export interface Section {
  id: string;
  text: string;
  level: 2 | 3;
}

const FEW = 4; // fewer main headings than this, and the sub-headings come along
const MOST_SUBS = 8;
export const BAR = 52; // the bar along the top, which a section scrolls to just under

function slug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9 -]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

// the page's headings as sections, each given an id if it hasn't one
export function readSections(root: ParentNode): Section[] {
  const mains = root.querySelectorAll("main h2").length;
  const subs = root.querySelectorAll("main h3").length;
  const both = mains < FEW && subs <= MOST_SUBS;
  const found: Section[] = [];
  const used = new Set<string>();
  root.querySelectorAll<HTMLElement>(both ? "main h2, main h3" : "main h2").forEach((h) => {
    const text = (h.textContent ?? "").trim();
    if (!text) return;
    if (!h.id) {
      let id = `section-${slug(text) || "untitled"}`;
      for (let k = 2; used.has(id) || document.getElementById(id); k++) id = `section-${slug(text)}-${k}`;
      h.id = id;
    }
    used.add(h.id);
    found.push({ id: h.id, text, level: h.tagName === "H3" ? 3 : 2 });
  });
  return found;
}

function same(a: Section[], b: Section[]): boolean {
  return a.length === b.length && a.every((s, k) => s.id === b[k].id && s.text === b[k].text);
}

// the section being read: the last one whose heading has passed under the bar
export function sectionAt(tops: number[], line = BAR + 72): number {
  let at = 0;
  tops.forEach((top, k) => {
    if (top <= line) at = k;
  });
  return at;
}

export function usePageSections(page: string): {
  sections: Section[];
  active: string | null;
  pick: (id: string) => void;
} {
  const [sections, setSections] = useState<Section[]>([]);
  const [active, setActive] = useState<string | null>(null);
  useEffect(() => {
    const root = document.querySelector(".page-main");
    if (!root) return;
    const read = () => {
      const found = readSections(root);
      setSections((before) => (same(before, found) ? before : found));
    };
    read();
    // a page fills in once its data has loaded, and changes with its own controls
    const watch = new MutationObserver(read);
    watch.observe(root, { childList: true, subtree: true, characterData: true });
    return () => watch.disconnect();
  }, [page]);
  useEffect(() => {
    const mark = () => {
      if (!sections.length) return setActive(null);
      // at the bottom of the page the last section is the one being read, however short it is
      const bottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      const tops = sections.map((s) => document.getElementById(s.id)?.getBoundingClientRect().top ?? Infinity);
      setActive(sections[bottom && window.scrollY > 0 ? sections.length - 1 : sectionAt(tops)].id);
    };
    mark();
    window.addEventListener("scroll", mark, { passive: true });
    return () => window.removeEventListener("scroll", mark);
  }, [sections]);
  // a click marks its section at once, before the scroll there finishes
  return { sections, active, pick: setActive };
}

export function goTo(id: string): void {
  const el = document.getElementById(id);
  if (!el) return;
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - BAR - 16, behavior: "smooth" });
}
