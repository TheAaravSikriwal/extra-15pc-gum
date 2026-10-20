"""PX4's flight log, turned into what the graders take: a FlightLog and the IMU samples.

PX4 writes a ULog of every flight. Everything graded comes from Gazebo's ground truth, which
PX4's Gazebo bridge logs next to its own estimates, so a grade says what the drone did rather
than what PX4 thought it did:

- position and velocity: vehicle_local_position_groundtruth, in PX4's north-east-down frame,
  turned to east-north-up with the height measured from where the flight started
- attitude: vehicle_attitude_groundtruth, PX4's body (forward-right-down) to north-east-down,
  turned to forward-left-up to east-north-up, the frame Rerun and the CAD use
- rotor speeds: esc_status, which the bridge fills with each motor's commanded speed in rad/s
  (despite the field's name, esc_rpm)
- the IMU: sensor_combined, the flight controller's own, standing in for the safety monitor's
- events: arming, PX4's mode changes, take-off and landing, the failsafes that matter here, and
  the motors stopping (every motor commanded to nothing after they've spun), plus whatever the
  scenario script marked itself

Every time is PX4's clock in seconds since it booted. In the sim that's Gazebo's clock, so the
scenario's own marks line up with the log's.

The reading itself (pyulog) is one small function; the rest works on plain arrays, so the tests
run anywhere.
"""

import numpy as np

from pcs14.flight.grade import FlightLog
from pcs14.safety.triggers import ImuSample

TOPICS = (
    "vehicle_local_position_groundtruth",
    "vehicle_attitude_groundtruth",
    "esc_status",
    "sensor_combined",
    "vehicle_status",
    "vehicle_land_detected",
    "failsafe_flags",
    "battery_status",
)
ARMED = 2  # vehicle_status.arming_state
MODES = {  # vehicle_status.nav_state, the ones the scenarios care about
    0: "manual",
    1: "altitude",
    2: "position",
    3: "mission",
    4: "hold",
    5: "return",
    12: "descend",
    13: "termination",
    14: "offboard",
    15: "stabilized",
    17: "takeoff",
    18: "land",
}
FAILSAFES = {  # failsafe_flags fields, and the event each one's rising edge makes
    "gcs_connection_lost": "link lost",
    "global_position_invalid": "position lost",
    "fd_critical_failure": "critical failure",
    "fd_motor_failure": "motor failure",
}
STOPPED = 1.0  # rad/s: a motor commanded under this is stopped
# the two frame changes, as quaternions (w, x, y, z): north-east-down to east-north-up is half a
# turn about (1, 1, 0); forward-left-up to forward-right-down is half a turn about x
_ENU_NED = np.array([0.0, 1 / np.sqrt(2), 1 / np.sqrt(2), 0.0])
_FRD_FLU = np.array([0.0, 1.0, 0.0, 0.0])


def read(path, topics=TOPICS) -> dict[str, dict[str, np.ndarray]]:
    """A ULog file's topics as plain arrays: {topic: {field: values}}. The first instance of
    each topic, which is the only one in the sim."""
    from pyulog import ULog

    log = ULog(str(path), message_name_filter_list=list(topics))
    out: dict[str, dict[str, np.ndarray]] = {}
    for data in log.data_list:
        if data.name not in out:
            out[data.name] = {k: np.asarray(v) for k, v in data.data.items()}
    return out


def _seconds(topic) -> np.ndarray:
    return np.asarray(topic["timestamp"], dtype=float) / 1e6


def _multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Quaternion products, (w, x, y, z), row by row; either side can be a single quaternion."""
    aw, ax, ay, az = np.moveaxis(np.broadcast_to(a, np.broadcast_shapes(a.shape, b.shape)), -1, 0)
    bw, bx, by, bz = np.moveaxis(np.broadcast_to(b, np.broadcast_shapes(a.shape, b.shape)), -1, 0)
    return np.stack(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        axis=-1,
    )


def enu_attitude(q_ned: np.ndarray) -> np.ndarray:
    """PX4's attitude quaternions, (w, x, y, z) forward-right-down to north-east-down, as
    (x, y, z, w) forward-left-up to east-north-up."""
    q = _multiply(_multiply(_ENU_NED, np.asarray(q_ned, dtype=float)), _FRD_FLU)
    q /= np.linalg.norm(q, axis=-1, keepdims=True)
    return np.concatenate([q[..., 1:], q[..., :1]], axis=-1)


def px4_euler(attitude: np.ndarray) -> np.ndarray:
    """(roll, pitch, yaw) in rad the way PX4 means them (forward-right-down to north-east-down,
    turned z then y then x), from the log's (x, y, z, w) attitudes. Both frame changes are half
    turns, which are their own inverses, so going back is the same two products."""
    q = np.asarray(attitude, dtype=float)
    q = np.concatenate([q[..., 3:], q[..., :3]], axis=-1)
    w, x, y, z = np.moveaxis(_multiply(_multiply(_ENU_NED, q), _FRD_FLU), -1, 0)
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return np.stack([roll, pitch, yaw], axis=-1)


def tilt_of(attitude: np.ndarray) -> np.ndarray:
    """rad from level, from the log's (x, y, z, w) attitudes."""
    q = np.asarray(attitude, dtype=float)
    return tilt(np.concatenate([q[..., 3:], q[..., :3]], axis=-1))


def tilt(q_ned: np.ndarray) -> np.ndarray:
    """rad from level, from PX4's attitude quaternions (w, x, y, z)."""
    q = np.asarray(q_ned, dtype=float)
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    return np.arccos(np.clip(1 - 2 * (q[..., 1] ** 2 + q[..., 2] ** 2), -1.0, 1.0))


def _rises(t, flags, name: str) -> list[tuple[float, str]]:
    """(time, name) wherever `flags` turns true. A flag already up when the log starts (no
    ground station yet, no GPS fix yet at boot) isn't an event."""
    flags = np.asarray(flags).astype(bool)
    previous = np.r_[True, flags[:-1]]
    return [(float(t[k]), name) for k in np.flatnonzero(flags & ~previous)]


def events(topics, t=None, rotor_speed=None) -> list[tuple[float, str]]:
    """Everything PX4's log says happened, in order. With the rotor speeds (on times `t`), the
    motors stopping too."""
    out: list[tuple[float, str]] = []
    status = topics.get("vehicle_status")
    if status is not None:
        ts = _seconds(status)
        armed = np.asarray(status["arming_state"]) == ARMED
        out += _rises(ts, armed, "armed")
        out += _rises(ts, ~armed, "disarmed")
        modes = np.asarray(status["nav_state"])
        for k in range(len(modes)):
            if k == 0 or modes[k] != modes[k - 1]:
                name = MODES.get(int(modes[k]))
                if name is not None:
                    out.append((float(ts[k]), name))
    land = topics.get("vehicle_land_detected")
    if land is not None:
        ts = _seconds(land)
        landed = np.asarray(land["landed"]).astype(bool)
        flown = False
        for k in range(1, len(landed)):
            if landed[k - 1] and not landed[k]:
                out.append((float(ts[k]), "took off"))
                flown = True
            elif flown and landed[k] and not landed[k - 1]:
                out.append((float(ts[k]), "landed"))
    flags = topics.get("failsafe_flags")
    if flags is not None:
        ts = _seconds(flags)
        for field, name in FAILSAFES.items():
            if field in flags:
                out += _rises(ts, flags[field], name)
        if "battery_warning" in flags:
            out += _rises(ts, np.asarray(flags["battery_warning"]) >= 1, "low battery")
    if t is not None and rotor_speed is not None:
        spinning = (np.asarray(rotor_speed) >= STOPPED).any(axis=1)
        if spinning.any():
            first = int(np.argmax(spinning))
            after = np.flatnonzero(~spinning[first:])
            if len(after):
                out.append((float(t[first + after[0]]), "motors stopped"))
    return sorted(out, key=lambda e: e[0])


def rotor_speeds(topics, t: np.ndarray, rotors: int = 4) -> np.ndarray:
    """rad/s, each motor's commanded speed on times `t`; zero before the first report."""
    esc = topics.get("esc_status")
    if esc is None:
        return np.zeros((len(t), rotors))
    ts = _seconds(esc)
    columns = []
    for k in range(rotors):
        values = np.asarray(esc[f"esc[{k}].esc_rpm"], dtype=float)
        columns.append(np.interp(t, ts, values, left=0.0))
    return np.column_stack(columns)


def flight_log(topics, marks=()) -> FlightLog:
    """The FlightLog on the ground truth's own times, with the scenario's `marks` ((s, name)
    pairs) among the events."""
    truth = topics["vehicle_local_position_groundtruth"]
    t = _seconds(truth)
    north, east, down = (np.asarray(truth[k], dtype=float) for k in ("x", "y", "z"))
    position = np.column_stack([east, north, -(down - down[0])])
    velocity = np.column_stack(
        [np.asarray(truth[k], dtype=float) for k in ("vy", "vx")] + [-np.asarray(truth["vz"])]
    )
    rotors = rotor_speeds(topics, t)
    attitude = None
    if "vehicle_attitude_groundtruth" in topics:
        att = topics["vehicle_attitude_groundtruth"]
        ta = _seconds(att)
        q = np.column_stack([np.interp(t, ta, att[f"q[{k}]"]) for k in range(4)])
        attitude = enu_attitude(q)
    found = events(topics, t, rotors) + [(float(s), n) for s, n in marks]
    return FlightLog(
        t=t,
        position=position,
        velocity=velocity,
        rotor_speed=rotors,
        events=sorted(found, key=lambda e: e[0]),
        attitude=attitude,
    )


def imu_samples(topics) -> list[ImuSample]:
    """The flight controller's IMU, with the tilt from the ground truth's attitude, for the
    safety monitor's triggers."""
    imu = topics["sensor_combined"]
    t = _seconds(imu)
    accel = np.column_stack([imu[f"accelerometer_m_s2[{k}]"] for k in range(3)])
    gyro = np.column_stack([imu[f"gyro_rad[{k}]"] for k in range(3)])
    tilts = np.zeros(len(t))
    if "vehicle_attitude_groundtruth" in topics:
        att = topics["vehicle_attitude_groundtruth"]
        ta = _seconds(att)
        q = np.column_stack([np.interp(t, ta, att[f"q[{k}]"]) for k in range(4)])
        tilts = tilt(q)
    return [
        ImuSample(float(t[k]), tuple(accel[k]), tuple(gyro[k]), float(tilts[k]))
        for k in range(len(t))
    ]
