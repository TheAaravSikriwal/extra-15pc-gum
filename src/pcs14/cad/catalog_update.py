"""Closing the loop: the printed parts' weights, worked out from their geometry, go back into
the catalog so the sizing model counts them.

Parts sharing a catalog entry (the four legs) add up into it. An entry the catalog already
has gets its weight and source replaced; everything else in the file stays as it was. An
entry it doesn't have yet becomes a new part file and joins the build in its module.
"""

from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

FOLDER = "components"


def _source_line(names: list[str], material: str) -> str:
    parts = ", ".join(sorted(names))
    note = (
        f"From the CAD: {parts}, weighed from their geometry in {material} at the density and "
        "fill in design/cad.yaml"
    )
    return f'source: {{kind: cad, checked: {date.today().isoformat()}, note: "{note}"}}'


def _replace_top_level(text: str, key: str, line: str) -> str:
    lines = text.splitlines()
    for i, existing in enumerate(lines):
        if existing.startswith(f"{key}:"):
            lines[i] = line
            return "\n".join(lines) + "\n"
    raise ValueError(f"no top-level {key} to replace")


def _new_part(catalog_id: str, names: list[str], material: str, grams: float) -> str:
    title = catalog_id.replace("-", " ").capitalize()
    cad = {
        "shape": "printed",
        "source": {"kind": "estimate", "note": "My own part, designed in pcs14.cad.printed"},
        "existing": {
            "found": "none",
            "checked": date.today().isoformat(),
            "note": "My own part, so there's nothing to look for",
        },
    }
    return "\n".join(
        [
            "# A printed part of my own, added by pcs14 cad --update-catalog.",
            "type: component",
            f"id: {catalog_id}",
            "maker: Printed",
            f"model: {title}",
            _source_line(names, material),
            f"mass_g: {round(grams, 1)}",
            yaml.safe_dump({"cad": cad}, sort_keys=False, width=100).rstrip(),
            "",
        ]
    )


def _add_to_build(build_path: Path, catalog_id: str, module: str, why: str = "printed") -> bool:
    """Add a part to the build in its module. Returns whether the build changed."""
    lines = build_path.read_text(encoding="utf-8").splitlines()
    data = yaml.safe_load("\n".join(lines))
    if module == "base":
        if catalog_id in data["base"]:
            return False
        start = lines.index("base:")
        end = next(i for i in range(start + 1, len(lines)) if not lines[i].startswith("  -"))
        lines.insert(end, f"  - {catalog_id} # {why}")
    else:
        if catalog_id in data["modules"].get(module, []):
            return False
        start = lines.index(f"  {module}:")
        end = next(
            (i for i in range(start + 1, len(lines)) if not lines[i].startswith("    -")),
            len(lines),
        )
        lines.insert(end, f"    - {catalog_id} # {why}")
    build_path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    return True


def update_catalog(printed, catalog_root: Path, build_path: Path) -> list[Path]:
    """Write the printed parts' weights into the catalog. Returns the files it changed."""
    catalog_root, build_path = Path(catalog_root), Path(build_path)
    groups = defaultdict(list)
    for part in printed:
        groups[part.catalog_id].append(part)
    changed = []
    for catalog_id, parts in groups.items():
        grams = sum(p.mass for p in parts) * 1000
        names = [p.name for p in parts]
        material = parts[0].material
        path = catalog_root / FOLDER / f"{catalog_id}.yaml"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = _replace_top_level(text, "source", _source_line(names, material))
            text = _replace_top_level(text, "mass_g", f"mass_g: {round(grams, 1)}")
        else:
            text = _new_part(catalog_id, names, material, grams)
            _add_to_build(build_path, catalog_id, parts[0].module)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_bytes(text.encode("utf-8"))
            changed.append(path)
    return changed


def _hardware_source(count: int | None) -> str:
    items = f"{count} pieces" if count else "the pieces"
    note = (
        f"From the hardware list in design/cad.yaml (pcs14 cad --update-catalog): {items}, each "
        "weighed from its standard size and its material's density. The counts come from the "
        "CAD's screw holes; the lengths and materials are my picks, and the grommets' and the "
        "patch's grams are guesses"
    )
    return f'source: {{kind: estimate, checked: {date.today().isoformat()}, note: "{note}"}}'


def _new_hardware(part_id: str, module: str, grams: float, count: int | None) -> str:
    where = "Base" if module == "base" else f"Module {module}"
    cad = {
        "shape": "fasteners",
        "source": {
            "kind": "estimate",
            "note": "The hardware list in design/cad.yaml, on the parts it holds",
        },
        "existing": {
            "found": "none",
            "checked": date.today().isoformat(),
            "note": "Standard screws, nuts and spacers, weighed from their sizes",
        },
    }
    return "\n".join(
        [
            f"# {where}'s screws, nuts and spacers, added by pcs14 cad --update-catalog.",
            "type: component",
            f"id: {part_id}",
            "maker: Various",
            f"model: {where}'s screws, nuts and spacers",
            _hardware_source(count),
            f"mass_g: {round(grams, 1)}",
            yaml.safe_dump({"cad": cad}, sort_keys=False, width=100).rstrip(),
            "",
        ]
    )


def update_hardware(masses: dict, catalog_root: Path, build_path: Path, counts=None) -> list:
    """Write each module's hardware (kg, from pcs14.cad.hardware.by_module) into its catalog
    entry, and add new entries to the build. Returns the files it changed."""
    from pcs14.cad.hardware import HARDWARE_PARTS

    catalog_root, build_path = Path(catalog_root), Path(build_path)
    counts = counts or {}
    changed = []
    for module, kg in masses.items():
        if kg <= 0:
            continue
        part_id = HARDWARE_PARTS[module]
        grams = kg * 1000
        path = catalog_root / FOLDER / f"{part_id}.yaml"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            new = _replace_top_level(text, "source", _hardware_source(counts.get(module)))
            new = _replace_top_level(new, "mass_g", f"mass_g: {round(grams, 1)}")
        else:
            text, new = None, _new_hardware(part_id, module, grams, counts.get(module))
        if new != text:
            path.write_bytes(new.encode("utf-8"))
            changed.append(path)
        if _add_to_build(build_path, part_id, module, "its screws, nuts and spacers"):
            if build_path not in changed:
                changed.append(build_path)
    return changed
