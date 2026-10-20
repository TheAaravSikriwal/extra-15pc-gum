"""check_ulog.py <ulog_sample.ulg>: reads the sample flight log the core's tests write (in
test_ulog.cpp) back with pyulog, the way the flight sim's graders read PX4's, and checks every
value. Where the repo's own Python is installed (the venv), it also runs the graders' reader,
pcs14.flight.ulog, over it.

ctest runs this after the core's tests whenever pyulog is installed."""

import math
import sys
import warnings

warnings.simplefilter("ignore")

from pyulog import ULog  # noqa: E402


def close(a, b, tol=1e-5):
    return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))


def main(path: str) -> int:
    log = ULog(path)
    topics = {d.name: d.data for d in log.data_list}
    wanted = {
        "vehicle_local_position_groundtruth", "vehicle_attitude_groundtruth", "esc_status",
        "sensor_combined", "vehicle_status", "vehicle_land_detected", "failsafe_flags",
        "battery_status",
    }  # fmt: skip
    problems = [f"no {t}" for t in sorted(wanted - topics.keys())]
    if problems:
        print("\n".join(problems))
        return 1
    for k in range(20):
        t = 100000 * (k + 1)
        f = float(k)
        checks = [
            (topics["vehicle_local_position_groundtruth"]["timestamp"][k], t),
            (topics["vehicle_local_position_groundtruth"]["x"][k], f),
            (topics["vehicle_local_position_groundtruth"]["y"][k], 2 * f),
            (topics["vehicle_local_position_groundtruth"]["z"][k], -0.5 * f),
            (topics["vehicle_local_position_groundtruth"]["vz"][k], -0.5),
            (topics["vehicle_attitude_groundtruth"]["q[0]"][k], math.cos(0.05 * f)),
            (topics["vehicle_attitude_groundtruth"]["q[3]"][k], math.sin(0.05 * f)),
            (topics["esc_status"]["esc[0].esc_rpm"][k], 500 + k),
            (topics["esc_status"]["esc[3].esc_rpm"][k], 503 + k),
            (topics["sensor_combined"]["gyro_rad[0]"][k], 0.01 * f),
            (topics["sensor_combined"]["accelerometer_m_s2[2]"][k], -9.80665),
            (topics["vehicle_status"]["arming_state"][k], 1 if k < 5 else 2),
            (topics["vehicle_status"]["nav_state"][k], 10),
            (topics["vehicle_land_detected"]["landed"][k], 1 if k < 8 else 0),
            (topics["failsafe_flags"]["gcs_connection_lost"][k], 1 if k >= 15 else 0),
            (topics["failsafe_flags"]["battery_warning"][k], 1 if k >= 18 else 0),
            (topics["failsafe_flags"]["geofence_breached"][k], 1 if k >= 12 else 0),
            (topics["battery_status"]["remaining"][k], 1 - 0.01 * f),
        ]
        for n, (got, expected) in enumerate(checks):
            if not close(got, expected, 1e-4):
                problems.append(f"sample {k}, check {n}: {got} against {expected}")
    if not close(log.initial_parameters["MC_ROLL_P"], 9.0):
        problems.append(f"MC_ROLL_P is {log.initial_parameters.get('MC_ROLL_P')}")
    if log.initial_parameters.get("CA_ROTOR_COUNT") != 4:
        problems.append(f"CA_ROTOR_COUNT is {log.initial_parameters.get('CA_ROTOR_COUNT')}")
    if log.msg_info_dict.get("sys_name") != "pcs14":
        problems.append(f"sys_name is {log.msg_info_dict.get('sys_name')!r}")
    if not any(m.message == "sample done" for m in log.logged_messages):
        problems.append("the logged text is missing")
    try:
        from pcs14.flight import ulog
    except ImportError:
        print("(pcs14 isn't installed here, so the graders' reader wasn't tried)")
    else:
        read = ulog.read(path)
        flight = ulog.flight_log(read)
        names = [name for _, name in flight.events]
        if names[:2] != ["armed", "took off"] or "link lost" not in names:
            problems.append(f"the graders' events: {flight.events}")
        if not close(flight.position[-1][2], 0.5 * 19, 1e-4):  # up is minus down, from the start
            problems.append(f"the graders' height at the end: {flight.position[-1][2]}")
    print("\n".join(problems) if problems else f"{path}: pyulog reads every value back")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
