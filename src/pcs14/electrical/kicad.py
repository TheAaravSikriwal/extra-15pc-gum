"""The KiCad schematic, generated from the connection list, with KiCad's electrical rules check.

Every board is a block with its pins, half down each side, named CONNECTOR.PIN; every pin on a
shared net gets a net label, which is how KiCad joins them; unused pins get no-connect flags.
Pin types come from the catalog and the list: a supply drives from one of its pins (power
out), loads take power in, signals are inputs, outputs or both ways, and plugs and pads pass
through. All modules are drawn fitted. Everything gets an ID from its name, so regenerating the
file only changes what really changed. A small symbol library and project file go alongside,
so the folder opens cleanly in KiCad.
"""

import json
import math
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from pcs14.electrical import tools
from pcs14.electrical.model import PACK, ConnectionList
from pcs14.electrical.validate import GROUND, Wiring, listed_in

GRID = 2.54  # mm
HALF = 22.86  # half a block's width, room for two long pin names
COLUMN = 147.32  # mm between columns of blocks
PAGE_BOTTOM = 800.0
VERSION = "20231120"  # KiCad 8's format, which KiCad 9 and 10 read
FONT = "(effects (font (size 1.27 1.27)))"
HIDDEN = "(effects (font (size 1.27 1.27)) (hide yes))"


def _id(kind: str, name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"pcs14/kicad/{kind}/{name}"))


def _q(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _snap(value: float) -> float:
    return round(round(value / GRID) * GRID, 4)


@dataclass
class Schematic:
    design: ConnectionList
    wiring: Wiring
    parts: dict

    @classmethod
    def make(cls, design, catalog, build):
        parts = {p.id: p for p in catalog.all_parts()}
        pack_max = build.pack.cell.max_voltage_v * build.pack.series
        return cls(design, Wiring(design, parts, listed_in(build), set(), pack_max), parts)

    # nets and pins

    def _groups(self):
        nets = self.wiring.nets(frozenset({"V", "P", "C"}))
        groups = {}
        for ref in nets.parent:
            groups.setdefault(nets.find(ref), []).append(ref)
        return list(groups.values())

    def nets(self) -> dict[str, list[str]]:
        """Every net with more than one pin, by a readable name."""
        supplies = {f"{PACK}.XT60.+": "PACK+"}
        for board in self.wiring.boards.values():
            for output in board.block.outputs:
                if output.kind != "through":
                    for ref in output.pins:
                        supplies[board.full(ref)] = f"{board.name}.{output.name}"
        out = {}
        for refs in self._groups():
            if len(refs) < 2:
                continue
            if f"{PACK}.XT60.-" in refs:
                name = "GND"
            else:
                named = sorted(supplies[r] for r in refs if r in supplies)
                # otherwise named after the flight controller's pin, or the Teensy's, if it has one
                ranked = sorted(
                    refs,
                    key=lambda r: (
                        0 if r.startswith("fc.") else 1 if r.startswith("teensy.") else 2,
                        r,
                    ),
                )
                name = named[0] if named else ranked[0]
            while name in out:
                name += "_"
            out[name] = sorted(refs)
        return out

    def unused_pins(self) -> list[str]:
        return sorted(refs[0] for refs in self._groups() if len(refs) == 1)

    def _passes_through(self, board) -> bool:
        block = board.block
        return board.name != PACK and not (block.draws or block.outputs or block.elements)

    def pin_types(self, board_name: str) -> dict[str, str]:
        board = self.wiring.boards[board_name]
        block = board.block
        types = {}
        fed = {d.pin for d in block.draws} | {o.fed_from for o in block.outputs if o.fed_from}
        driving = {}
        for output in block.outputs:
            if output.kind != "through":
                driving[output.pins[0]] = "power_out"
                for ref in output.pins[1:]:
                    driving[ref] = "passive"
        for element in block.elements:
            if element.kind in ("diode", "fuse"):
                driving.setdefault(element.between[1], "power_out")
                driving.setdefault(element.between[0], "passive")
        for local, pin in block.pins():
            if pin.role == GROUND:
                kind = "power_out" if board_name == PACK else "power_in"
                if self._passes_through(board):
                    kind = "passive"
            elif pin.role == "power":
                if board_name == PACK:
                    kind = "power_out"
                elif local in driving:
                    kind = driving[local]
                elif local in fed:
                    kind = "power_in"
                else:
                    kind = "passive"
            elif pin.role == "bus":
                kind = "passive"
            else:
                way = board.direction(board.full(local))
                kind = {"in": "input", "out": "output"}.get(way, "bidirectional")
                if self._passes_through(board):
                    kind = "passive"
            types[local] = kind
        return types

    def _settle_drivers(self, types_by_board):
        """Two power outputs on one net would trip KiCad's check: keep the first, pass the rest."""
        for refs in self._groups():
            outs = [
                r
                for r in sorted(refs)
                if types_by_board[r.split(".", 1)[0]][r.split(".", 1)[1]] == "power_out"
            ]
            if len(outs) < 2:
                continue
            from_pack = [r for r in outs if r.startswith(f"{PACK}.")]
            keep = from_pack[0] if from_pack else outs[0]
            for ref in outs:
                if ref != keep:
                    board, local = ref.split(".", 1)
                    types_by_board[board][local] = "passive"

    # drawing

    def _layout(self):
        names = [PACK, *self.design.boards]
        x, y, placed = 50.8, 50.8, {}
        for name in names:
            pins = list(self.wiring.boards[name].block.pins())
            rows = math.ceil(len(pins) / 2)
            height = (rows + 2) * GRID
            if y + height > PAGE_BOTTOM:
                x, y = x + COLUMN, 50.8
            placed[name] = (_snap(x), _snap(y + GRID * 2))
            y += height + 4 * GRID
        return placed

    def _pin_spots(self, name):
        """Each pin's place in the symbol, in the library's coordinates (y up)."""
        pins = [local for local, _ in self.wiring.boards[name].block.pins()]
        rows = math.ceil(len(pins) / 2)
        spots = {}
        for i, local in enumerate(pins):
            side, row = (0, i) if i < rows else (1, i - rows)
            x = -(HALF + GRID) if side == 0 else HALF + GRID
            spots[local] = (x, -row * GRID, 0 if side == 0 else 180)
        return spots, rows

    def _library_symbol(self, part, board_name, types, prefix):
        spots, rows = self._pin_spots(board_name)
        top, bottom = GRID, -rows * GRID
        body = [
            f"(symbol {_q(prefix + part)} (exclude_from_sim no) (in_bom yes) (on_board yes)",
            f'(property "Reference" "U" (at 0 {top + GRID} 0) {FONT})',
            f'(property "Value" {_q(part)} (at 0 {bottom - GRID} 0) {FONT})',
            f'(property "Footprint" "" (at 0 0 0) {HIDDEN})',
            f'(property "Datasheet" "" (at 0 0 0) {HIDDEN})',
            f"(symbol {_q(part + '_0_1')} (rectangle (start {-HALF} {top}) (end {HALF} {bottom}) "
            "(stroke (width 0.254) (type default)) (fill (type background))))",
            f"(symbol {_q(part + '_1_1')}",
        ]
        for number, (local, (x, y, angle)) in enumerate(spots.items(), start=1):
            body.append(
                f"(pin {types[local]} line (at {x} {y} {angle}) (length {GRID}) "
                f"(name {_q(local)} {FONT}) (number {_q(number)} {FONT}))"
            )
        body.append("))")
        return " ".join(body)

    def text(self) -> str:
        root = _id("sheet", "electrical")
        placed = self._layout()
        types = {name: self.pin_types(name) for name in self.wiring.boards}
        self._settle_drivers(types)
        net_of = {ref: name for name, refs in self.nets().items() for ref in refs}
        unused = set(self.unused_pins())
        part_of = {
            name: (b.part if name != PACK else PACK) for name, b in self.design.boards.items()
        }
        part_of[PACK] = PACK
        symbols = {}
        for name in placed:
            part = part_of[name]
            if part not in symbols:  # one library symbol per part, drawn from its first board
                symbols[part] = self._library_symbol(part, name, types[name], "pcs14:")
        lines = [
            f'(kicad_sch (version {VERSION}) (generator "pcs14") (generator_version "0.1")',
            f'(uuid "{root}") (paper "A0")',
            "(lib_symbols " + " ".join(symbols[p] for p in sorted(symbols)) + ")",
        ]
        for number, (name, (x, y)) in enumerate(placed.items(), start=1):
            reference = f"U{number}"
            spots, rows = self._pin_spots(name)
            pins = " ".join(
                f'(pin "{i}" (uuid "{_id("pin", f"{name}.{local}")}"))'
                for i, local in enumerate(spots, start=1)
            )
            lines.append(
                f'(symbol (lib_id "pcs14:{part_of[name]}") (at {x} {y} 0) (unit 1) '
                "(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) "
                f'(uuid "{_id("symbol", name)}") '
                f'(property "Reference" "{reference}" (at {x} {_snap(y - 2 * GRID)} 0) {FONT}) '
                f'(property "Value" {_q(part_of[name])} '
                f"(at {x} {_snap(y + (rows + 1) * GRID)} 0) {FONT}) "
                f'(property "Footprint" "" (at {x} {y} 0) {HIDDEN}) '
                f'(property "Datasheet" "" (at {x} {y} 0) {HIDDEN}) '
                f'(property "Board" {_q(name)} (at {x} {_snap(y - 3 * GRID)} 0) {FONT}) '
                f"{pins} "
                f'(instances (project "electrical" '
                f'(path "/{root}" (reference "{reference}") (unit 1)))))'
            )
            for local, (px, py, angle) in spots.items():
                ref = f"{name}.{local}"
                ax, ay = _snap(x + px), _snap(y - py)
                if ref in unused:
                    lines.append(f'(no_connect (at {ax} {ay}) (uuid "{_id("nc", ref)}"))')
                elif ref in net_of:
                    turn, justify = (180, "right bottom") if angle == 0 else (0, "left bottom")
                    lines.append(
                        f"(label {_q(net_of[ref])} (at {ax} {ay} {turn}) (fields_autoplaced yes) "
                        f"(effects (font (size 1.27 1.27)) (justify {justify})) "
                        f'(uuid "{_id("label", ref)}"))'
                    )
        lines.append('(sheet_instances (path "/" (page "1")))')
        lines.append(")")
        return "\n".join(lines) + "\n"

    def library(self) -> str:
        placed = self._layout()
        types = {name: self.pin_types(name) for name in self.wiring.boards}
        self._settle_drivers(types)
        seen, symbols = set(), []
        for name in placed:
            part = self.design.boards[name].part if name != PACK else PACK
            if part not in seen:
                seen.add(part)
                symbols.append(self._library_symbol(part, name, types[name], ""))
        return (
            f'(kicad_symbol_lib (version {VERSION}) (generator "pcs14") (generator_version "0.1") '
            + " ".join(symbols)
            + ")\n"
        )

    def write(self, folder: Path) -> Path:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "electrical.kicad_sch").write_text(self.text(), encoding="utf-8")
        (folder / "pcs14.kicad_sym").write_text(self.library(), encoding="utf-8")
        (folder / "sym-lib-table").write_text(
            '(sym_lib_table (version 7) (lib (name "pcs14") (type "KiCad") '
            '(uri "${KIPRJMOD}/pcs14.kicad_sym") (options "") '
            '(descr "Extra 15pc Gum boards, generated by pcs14")))\n',
            encoding="utf-8",
        )
        (folder / "electrical.kicad_pro").write_text(
            json.dumps({"meta": {"filename": "electrical.kicad_pro", "version": 1}}) + "\n",
            encoding="utf-8",
        )
        return folder


def erc(schematic: Path) -> list[dict]:
    """KiCad's electrical rules check: every violation, warnings included."""
    schematic = Path(schematic)
    report = schematic.with_name("erc.json")
    done = subprocess.run(
        [
            str(tools.require("kicad-cli")),
            "sch",
            "erc",
            "--format",
            "json",
            "--severity-all",
            "-o",
            str(report),
            str(schematic),
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if not report.exists():
        raise OSError(f"KiCad's rules check didn't run:\n{done.stdout}\n{done.stderr}")
    data = json.loads(report.read_text(encoding="utf-8"))
    report.unlink()
    return [v for sheet in data.get("sheets", []) for v in sheet.get("violations", [])]


def export_svg(schematic: Path, folder: Path) -> list[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(tools.require("kicad-cli")),
            "sch",
            "export",
            "svg",
            "-o",
            str(folder),
            str(schematic),
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=True,
    )
    return sorted(folder.glob("*.svg"))
