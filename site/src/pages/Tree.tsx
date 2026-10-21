// Any data, as a tree you open a branch at a time: a value inline, a list or a record behind
// its own toggle. A branch's insides are only built once it's opened, so the CAD's and the
// wiring's whole data files stay quick.
import { useState } from "react";

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

export function leaf(v: unknown): string {
  if (v === null || v === undefined) return "none";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : String(Math.round(v * 1e6) / 1e6);
  if (typeof v === "boolean") return v ? "yes" : "no";
  return String(v);
}

function size(v: unknown): string {
  if (Array.isArray(v)) return `${v.length} items`;
  if (isRecord(v)) return `${Object.keys(v).length} fields`;
  return "";
}

function Branch({ name, value, open: startOpen }: { name: string; value: unknown; open: boolean }) {
  const [open, setOpen] = useState(startOpen);
  return (
    <details open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary>
        <span className="tree-key">{name}</span> <span className="muted">{size(value)}</span>
      </summary>
      {open ? <Tree value={value} depth={1} /> : null}
    </details>
  );
}

export function Tree({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (!Array.isArray(value) && !isRecord(value)) {
    return <span className="tree-leaf">{leaf(value)}</span>;
  }
  const entries: [string, unknown][] = Array.isArray(value)
    ? value.map((v, k) => [String(k + 1), v])
    : Object.entries(value);
  return (
    <ul className="tree">
      {entries.map(([k, v]) =>
        Array.isArray(v) || isRecord(v) ? (
          <li key={k}>
            <Branch name={k} value={v} open={depth === 0 && entries.length <= 3} />
          </li>
        ) : (
          <li key={k}>
            <span className="tree-key">{k}</span> <span className="tree-leaf">{leaf(v)}</span>
          </li>
        ),
      )}
    </ul>
  );
}
