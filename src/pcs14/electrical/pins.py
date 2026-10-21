"""Where a pin sits: a wire end in the connection list (BOARD.CONNECTOR.PIN) found on its part's
cad connectors. A connector plugged into another one (the module bus harness's plug in the
flight controller's CAN port) sits where its mate does, so it's looked up through the mate."""

from dataclasses import dataclass

from pcs14.catalog.cad import CadConnector


@dataclass(frozen=True)
class Place:
    board: str  # the board that holds it, which is the mate's for a plug in a socket
    part_id: str
    connector: CadConnector
    pin: str
    x_mm: float
    y_mm: float


def row(names: list[str], first: tuple[float, float], pitch_mm: float,
        runs: tuple[float, float]) -> dict[str, tuple[float, float]]:  # fmt: skip
    """A row of pins from its first one, `pitch_mm` apart along the unit direction `runs`."""
    return {name: (round(first[0] + k * pitch_mm * runs[0], 3),
                   round(first[1] + k * pitch_mm * runs[1], 3))
            for k, name in enumerate(names)}  # fmt: skip


def _own(parts: dict, connections, board: str, connector: str, pin: str) -> Place | None:
    found = connections.boards.get(board)
    part = parts.get(found.part) if found else None
    if part is None or part.cad is None:
        return None
    for c in part.cad.connectors:
        if c.name == connector and pin in c.pins:
            x, y = c.pins[pin]
            return Place(board, part.id, c, pin, x, y)
    return None


def place(catalog, connections, end: str) -> Place | None:
    """Where the pin `end` sits, or None where nothing places it."""
    board, connector, pin = end.split(".", 2)
    parts = {p.id: p for p in catalog.all_parts()}
    found = _own(parts, connections, board, connector, pin)
    if found:
        return found
    here = f"{board}.{connector}"
    for mate in connections.mates:
        other = mate.b if mate.a == here else mate.a if mate.b == here else None
        if other:
            b, c = other.split(".", 1)
            found = _own(parts, connections, b, c, pin)
            if found:
                return found
    return None
