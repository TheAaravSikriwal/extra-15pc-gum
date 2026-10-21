"""DroneCAN's data type signatures and the Fix2 test vector in firmware/h743/tests, remade.

My firmware decodes DroneCAN with libcanard, which needs each multi-frame message's data type
signature, and its Fix2 test checks the decoder against frames pydronecan makes. Both come from
pydronecan reading the DSDL, pinned:

    dronecan/pydronecan  092d09cb9e6b115e262efe4cb42f7b65e6054f26  (MIT)
    dronecan/DSDL        b4653c7abc3c47cb31b16efa24ea755232774756  (MIT)

Unpack pydronecan somewhere, put the DSDL next to it as DSDL/ (pydronecan loads it from there on
import), and run:

    python scripts/dronecan-vectors.py <pydronecan folder>
"""

import sys
from pathlib import Path

sys.path.append(str(Path(sys.argv[1]).resolve()))

import dronecan  # noqa: E402

TYPES = (
    "uavcan.protocol.NodeStatus",
    "uavcan.equipment.gnss.Fix2",
    "uavcan.equipment.ahrs.MagneticFieldStrength2",
    "uavcan.equipment.air_data.StaticPressure",
    "uavcan.equipment.air_data.StaticTemperature",
)

for name in TYPES:
    t = dronecan.TYPENAMES[name]
    print(f"{name}: id {t.default_dtid}, signature 0x{t.get_data_type_signature():016x}")

# the test's fix: Boston-ish, a 3D DGPS fix, a little covariance
fix = dronecan.uavcan.equipment.gnss.Fix2()
fix.timestamp.usec = 123456789
fix.gnss_timestamp.usec = 987654321
fix.gnss_time_standard = 2
fix.num_leap_seconds = 18
fix.longitude_deg_1e8 = -7112345678
fix.latitude_deg_1e8 = 4234567890
fix.height_ellipsoid_mm = 12345
fix.height_msl_mm = 45678
fix.ned_velocity = [1.5, -0.25, 0.125]
fix.sats_used = 17
fix.status = 3
fix.mode = 1
fix.sub_mode = 1
fix.covariance = [0.5, 0.25, 4.0]
fix.pdop = 1.25

transfer = dronecan.transport.Transfer(payload=fix, source_node_id=10, transfer_id=5,
                                       transfer_priority=24)  # fmt: skip
for frame in transfer.to_frames():
    print(f"frame 0x{frame.message_id:08x} {bytes(frame.bytes).hex()}")
