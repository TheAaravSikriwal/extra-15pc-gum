"""Loading the parts catalog: one YAML file per part, in a folder per type."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from pcs14.catalog.schema import (
    Cell,
    Component,
    Esc,
    Frame,
    Motor,
    Part,
    Prop,
    SourceKind,
    Wire,
)

FOLDERS: dict[str, type[Part]] = {
    "motors": Motor,
    "props": Prop,
    "cells": Cell,
    "escs": Esc,
    "frames": Frame,
    "components": Component,
    "wires": Wire,
}
FOLDER_FOR_TYPE = {
    cls.model_fields["type"].annotation.__args__[0]: folder for folder, cls in FOLDERS.items()
}


class CatalogError(Exception):
    """A parts file is broken, or something asked for a part that isn't there."""


@dataclass(frozen=True)
class Catalog:
    motors: dict[str, Motor] = field(default_factory=dict)
    props: dict[str, Prop] = field(default_factory=dict)
    cells: dict[str, Cell] = field(default_factory=dict)
    escs: dict[str, Esc] = field(default_factory=dict)
    frames: dict[str, Frame] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)
    wires: dict[str, Wire] = field(default_factory=dict)

    def all_parts(self) -> list[Part]:
        return [
            *self.motors.values(),
            *self.props.values(),
            *self.cells.values(),
            *self.escs.values(),
            *self.frames.values(),
            *self.components.values(),
            *self.wires.values(),
        ]

    def motor(self, part_id: str) -> Motor:
        return _get(self.motors, "motor", part_id)

    def prop(self, part_id: str) -> Prop:
        return _get(self.props, "prop", part_id)

    def cell(self, part_id: str) -> Cell:
        return _get(self.cells, "cell", part_id)

    def esc(self, part_id: str) -> Esc:
        return _get(self.escs, "esc", part_id)

    def frame(self, part_id: str) -> Frame:
        return _get(self.frames, "frame", part_id)

    def component(self, part_id: str) -> Component:
        return _get(self.components, "component", part_id)

    def wire(self, part_id: str) -> Wire:
        return _get(self.wires, "wire", part_id)


def _get(table: dict, kind: str, part_id: str):
    if part_id not in table:
        known = ", ".join(sorted(table)) or "none yet"
        raise CatalogError(
            f"there's no {kind} called '{part_id}' in the catalog. The {kind}s are: {known}"
        )
    return table[part_id]


def load_catalog(root: Path, *, allow_made_up: bool = False) -> Catalog:
    """Load and check every parts file under `root`.

    Made-up test parts are refused unless `allow_made_up` is set, so they can never end up
    in a real report.
    """
    root = Path(root)
    if not root.is_dir():
        raise CatalogError(f"there's no catalog folder at {root}")

    tables: dict[str, dict] = {folder: {} for folder in FOLDERS}
    where: dict[str, str] = {}
    for folder, cls in FOLDERS.items():
        for path in sorted((root / folder).glob("*.yaml")):
            name = f"{folder}/{path.name}"
            part = _load_file(path, name, folder, cls)
            if not allow_made_up and any(s.kind is SourceKind.MADE_UP for s in part.sources()):
                raise CatalogError(
                    f"{name}: this part is made up for tests, and made-up parts can't go in the "
                    "real catalog"
                )
            if part.id in where:
                raise CatalogError(
                    f"{name}: the id '{part.id}' is already used by {where[part.id]}"
                )
            where[part.id] = name
            tables[folder][part.id] = part

    catalog = Catalog(**tables)
    for motor in catalog.motors.values():
        for table in motor.thrust_tables:
            if table.prop not in catalog.props:
                raise CatalogError(
                    f"{where[motor.id]}: a thrust table names the prop '{table.prop}', which isn't "
                    "in the catalog"
                )
    for part in catalog.all_parts():
        if part.electrical is None:
            continue
        for family in sorted(part.electrical.families()):
            holder = catalog.components.get(family)
            if holder is None:
                raise CatalogError(
                    f"{where[part.id]}: a connector's family is '{family}', which isn't in the "
                    "catalog (it should be the part that holds the contact rating, or 'pads')"
                )
            if holder.electrical is None or holder.electrical.rating is None:
                raise CatalogError(
                    f"{where[family]}: '{family}' is used as a connector family, so it needs an "
                    "electrical block with a rating"
                )
    return catalog


def _load_file(path: Path, name: str, folder: str, cls: type[Part]) -> Part:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise CatalogError(f"{name}: isn't valid YAML ({error})") from error
    if not isinstance(data, dict):
        raise CatalogError(f"{name}: should be a set of fields, like 'mass_g: 70'")

    kind = data.get("type")
    expected = cls.model_fields["type"].annotation.__args__[0]
    if kind != expected:
        if kind in FOLDER_FOR_TYPE:
            raise CatalogError(
                f"{name}: this is a {kind}, but it's in {folder}/ ({kind}s go in "
                f"{FOLDER_FOR_TYPE[kind]}/)"
            )
        raise CatalogError(f"{name}: 'type' should be {expected}, not {kind!r}")

    try:
        return cls.model_validate(data)
    except ValidationError as error:
        raise CatalogError(f"{name}: " + "; ".join(_explain(error, cls))) from None


def _explain(error: ValidationError, cls: type[Part]) -> list[str]:
    messages = []
    for problem in error.errors():
        where = ".".join(str(step) for step in problem["loc"]) or "the file"
        if problem["type"] == "extra_forbidden":
            field_name = str(problem["loc"][-1])
            meant = [f for f in cls.model_fields if f.startswith(f"{field_name}_")]
            if meant:
                messages.append(
                    f"'{where}' isn't a field. Numbers carry their unit in the name: did you "
                    f"mean {' or '.join(meant)}?"
                )
            else:
                messages.append(f"'{where}' isn't a field (a typo?)")
        elif problem["type"] == "missing":
            messages.append(f"{where}: missing")
        else:
            messages.append(f"{where}: {problem['msg'].removeprefix('Value error, ')}")
    return messages
