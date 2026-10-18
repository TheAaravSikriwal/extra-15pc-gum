"""The frame: a plain X from the frame's cad block.

From the bottom up: the bottom plate, the arms on it, the middle plate on the arms, the stack
bay, and the top plate on standoffs. The nose points along +x, the left side along +y, and
z = 0 is the underside of the bottom plate. The motors sit on the arms at the corners of the
wheelbase, and the flight controller stack sits on the middle plate at the center.
"""

import math
from dataclasses import dataclass

from build123d import Align, Axis, Box, Compound, Cylinder, Part, Pos, Rot, fillet

from pcs14.catalog import Frame

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
CORNER_RADIUS = 0.004  # the plates' rounded corners
SCREW = 0.0032  # M3 clearance
STANDOFF = 0.005  # aluminum M3 standoffs are about 5 mm across


@dataclass(frozen=True)
class FrameModel:
    solid: Compound  # everything: carbon and standoffs
    carbon: Part  # the plates and arms, for the weight check
    body: Part  # the three plates
    motor_mounts: tuple[tuple[float, float, float], ...]  # where each motor's base sits
    bay_floor: float  # top of the middle plate, where the stack starts
    bay_height: float
    top: float  # top of the top plate


def build_frame(frame: Frame) -> FrameModel:
    cad = frame.cad
    plate_t, arm_t = cad.size("plate_thickness_mm"), cad.size("arm_thickness_mm")
    front, back = cad.size("body_front_mm"), cad.size("body_back_mm")
    width = cad.size("body_width_mm")
    reach = frame.wheelbase / 2  # center to motor, along the diagonal
    corner = reach / math.sqrt(2)

    arms_z = plate_t
    middle_z = arms_z + arm_t
    bay_floor = middle_z + plate_t
    bay_height = cad.size("plate_gap_mm")
    top_z = bay_floor + bay_height

    nose_from, nose_width = cad.size("nose_from_mm"), cad.size("nose_width_mm")

    def plate(z: float) -> Part:
        """The full width behind nose_from, narrower in front of it, corners rounded."""
        rear = Pos((nose_from - back) / 2, 0, 0) * Box(
            nose_from + back, width, plate_t, align=BOTTOM
        )
        nose = Pos((front + nose_from) / 2, 0, 0) * Box(
            front - nose_from, nose_width, plate_t, align=BOTTOM
        )
        body = rear + nose
        outer = [
            edge
            for edge in body.edges().filter_by(Axis.Z)
            if min(abs(edge.center().X + back), abs(edge.center().X - front)) < 1e-6
        ]
        body = fillet(outer, CORNER_RADIUS)
        body = Pos(0, 0, z) * body
        half = cad.size("stack_spacing_mm") / 2
        for x, y in ((half, half), (-half, half), (-half, -half), (half, -half)):
            body -= Pos(x, y, z) * Cylinder(SCREW / 2, plate_t * 3, align=BOTTOM)
        return body

    mounts = []
    arms = None
    for k, angle in enumerate((45, -45, 135, -135)):
        arm = Box(
            reach, cad.size("arm_width_mm"), arm_t, align=(Align.MIN, Align.CENTER, Align.MIN)
        )
        arm = Rot(0, 0, angle) * arm
        x = corner * math.copysign(1, math.cos(math.radians(angle)))
        y = corner * math.copysign(1, math.sin(math.radians(angle)))
        arm += Pos(x, y, 0) * Cylinder(cad.size("motor_pad_mm") / 2, arm_t, align=BOTTOM)
        arms = arm if k == 0 else arms + arm
        mounts.append((x, y, middle_z))
    arms = Pos(0, 0, arms_z) * arms
    half_mount = 0.019 / 2  # the 19 x 19 mm motor pattern (16 x 16 holes not modeled)
    for x, y, _ in mounts:
        for dx, dy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            arms -= Pos(x + dx * half_mount, y + dy * half_mount, 0) * Cylinder(
                SCREW / 2, 1.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
            )
        arms -= Pos(x, y, 0) * Cylinder(
            0.004, 1.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
        )

    plates = plate(0) + plate(middle_z) + plate(top_z)
    plates.label = "body plates"
    arms.label = "arms"
    carbon = plates + arms

    inset_x, inset_y = 0.008, width / 2 - 0.005
    standoffs = []
    for x, y in (
        (front - inset_x, inset_y),
        (front - inset_x, -inset_y),
        (-back + inset_x, inset_y),
        (-back + inset_x, -inset_y),
    ):
        post = Pos(x, y, bay_floor) * Cylinder(STANDOFF / 2, bay_height, align=BOTTOM)
        post.label = "standoff"
        standoffs.append(post)

    solid = Compound([plates, arms, *standoffs])
    solid.label = frame.id
    return FrameModel(
        solid=solid,
        carbon=carbon,
        body=plates,
        motor_mounts=tuple(mounts),
        bay_floor=bay_floor,
        bay_height=bay_height,
        top=top_z + plate_t,
    )
