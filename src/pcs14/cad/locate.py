"""Moving a part from its own frame to its spot on the drone: turn it, then move it."""

from build123d import Pos, Rot, Vertex

from pcs14.cad.settings import Placement


def placed(shape, placement: Placement):
    return Pos(*placement.at) * Rot(*placement.turn_deg) * shape


def place_point(
    point: tuple[float, float, float], placement: Placement
) -> tuple[float, float, float]:
    """Where a point in a part's own frame ends up on the drone."""
    center = placed(Vertex(*point), placement).center()
    return (center.X, center.Y, center.Z)
