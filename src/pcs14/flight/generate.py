"""The Gazebo model, world and PX4 parameters for each module combination.

Each combination's model is generated from the build, the sizing model and the CAD:

- base_link: the CAD's mass, center of gravity and inertia for that combination, with the pack
  at its trim and the props left out (each rotor link carries its own). Its looks are the CAD's
  mesh of that combination; it touches the ground through a box around the frame's plates and a
  sphere at each printed leg's foot, because contacts on a full mesh are slow and jittery.
- four rotor links at the frame's motor mounts, at the props' height, in PX4's x500 order and
  spin directions (0 front right and 1 back left counterclockwise, 2 front left and 3 back right
  clockwise), each with Gazebo's multicopter motor model from pcs14.flight.motor. A prop's
  inertia is three thin blades from hub to tip.
- the sensors PX4 needs, with the x500's noise figures (an air pressure sensor, a magnetometer,
  an IMU and a navsat receiver)
- our drag plugin (sim/plugins/pcs14_drag) with that combination's drag area from the sizing
  model, and in P, the parachute; in C, a detachable joint for the payload

PX4 stays unmodified: it runs its stock x500 airframe, and the runner loads these parameters
over it. The world copies PX4's default world (its physics step, magnetic field, ground and
origin, which is PX4's, not anywhere of mine) and adds the wind our plugin starts from.
"""

import math
from dataclasses import dataclass, field

from pcs14.flight.drag import Chute
from pcs14.flight.motor import MotorModel

PREFIX = "pcs14_"
FOOT_RADIUS = 0.008  # m, the printed legs' feet (pcs14.cad.printed)
IDLE_SHARE = 0.15  # of the top speed, where PX4 idles a motor (the x500: 150 of 1000 rad/s)
TOP_SPEED_LIMIT = 25.0  # m/s, PX4's speed limits for the capability tests (80 km/h is 22.2)
CHUTE_TOPIC = "/pcs14/chute/fire"
WIND_TOPIC = "/pcs14/wind"
PAYLOAD_TOPICS = ("/pcs14/payload/attach", "/pcs14/payload/detach")
# PX4's quad X: (front?, left?, direction) for rotors 0 to 3
ORDER = ((True, False, "ccw"), (False, True, "ccw"), (True, True, "cw"), (False, False, "cw"))
# the x500's sensor noise (models/x500_base/model.sdf in PX4-gazebo-models b6127f4)
SENSORS = """      <sensor name="air_pressure_sensor" type="air_pressure">
        <gz_frame_id>base_link</gz_frame_id>
        <always_on>1</always_on>
        <update_rate>50</update_rate>
        <air_pressure>
          <pressure><noise type="gaussian"><mean>0</mean><stddev>3</stddev></noise></pressure>
        </air_pressure>
      </sensor>
      <sensor name="magnetometer_sensor" type="magnetometer">
        <gz_frame_id>base_link</gz_frame_id>
        <always_on>1</always_on>
        <update_rate>100</update_rate>
        <magnetometer>
          <x><noise type="gaussian"><stddev>0.0001</stddev></noise></x>
          <y><noise type="gaussian"><stddev>0.0001</stddev></noise></y>
          <z><noise type="gaussian"><stddev>0.0001</stddev></noise></z>
        </magnetometer>
      </sensor>
      <sensor name="imu_sensor" type="imu">
        <gz_frame_id>base_link</gz_frame_id>
        <always_on>1</always_on>
        <update_rate>250</update_rate>
        <imu>
          <angular_velocity>
            <x><noise type="gaussian"><mean>0</mean><stddev>0.0008726646</stddev></noise></x>
            <y><noise type="gaussian"><mean>0</mean><stddev>0.0008726646</stddev></noise></y>
            <z><noise type="gaussian"><mean>0</mean><stddev>0.0008726646</stddev></noise></z>
          </angular_velocity>
          <linear_acceleration>
            <x><noise type="gaussian"><mean>0</mean><stddev>0.00637</stddev></noise></x>
            <y><noise type="gaussian"><mean>0</mean><stddev>0.00637</stddev></noise></y>
            <z><noise type="gaussian"><mean>0</mean><stddev>0.00686</stddev></noise></z>
          </linear_acceleration>
        </imu>
      </sensor>
      <sensor name="navsat_sensor" type="navsat">
        <gz_frame_id>base_link</gz_frame_id>
        <always_on>1</always_on>
        <update_rate>30</update_rate>
      </sensor>
"""


def _n(value: float) -> str:
    return f"{value:.9g}"


def _v(values) -> str:
    return " ".join(_n(v) for v in values)


@dataclass(frozen=True)
class RotorSpot:
    number: int
    position: tuple[float, float, float]  # m, in the model's frame (x forward, y left, z up)
    direction: str  # ccw or cw, seen from above
    mass: float  # kg, the prop
    radius: float  # m, the prop's

    @property
    def inertia(self) -> tuple[float, float, float]:
        """Three thin blades from hub to tip: m r^2 / 3 about the shaft, half that across."""
        spin = self.mass * self.radius**2 / 3
        return (spin / 2, spin / 2, spin)


@dataclass(frozen=True)
class FlightModel:
    name: str  # the Gazebo model's name
    setup: str
    modules: frozenset[str]
    mass: float  # kg, base_link: everything but the props
    center: tuple[float, float, float]  # m, base_link's center of gravity
    inertia: tuple[tuple[float, float, float], ...]  # kg m^2, about the center
    rotors: tuple[RotorSpot, ...]
    body_center: tuple[float, float, float]  # m, the plates' collision box
    body_size: tuple[float, float, float]
    feet: tuple[tuple[float, float, float], ...]  # m, each foot's lowest point
    motor: MotorModel
    drag_area: float  # m^2
    chute: Chute | None = None
    payload: float = 0.0  # kg, in C
    params: dict = field(default_factory=dict)  # PX4's, loaded over the x500 airframe
    mesh: str | None = None  # the looks, relative to the model's folder

    @property
    def total_mass(self) -> float:
        return self.mass + sum(r.mass for r in self.rotors)

    @property
    def lift_off(self) -> float:
        """m: how high the model's origin sits when its feet rest on the ground."""
        return FOOT_RADIUS - min(z for _, _, z in self.feet)

    def sdf(self) -> str:
        i = self.inertia
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            "<!-- Generated by pcs14 flight-sim from the build, the sizing model and the CAD. "
            "Don't edit it: change design/ and regenerate. -->",
            '<sdf version="1.9">',
            f'  <model name="{self.name}">',
            f"    <pose>0 0 {_n(self.lift_off)} 0 0 0</pose>",
            "    <self_collide>false</self_collide>",
            "    <static>false</static>",
            '    <link name="base_link">',
            "      <inertial>",
            f"        <pose>{_v(self.center)} 0 0 0</pose>",
            f"        <mass>{_n(self.mass)}</mass>",
            "        <inertia>",
            f"          <ixx>{_n(i[0][0])}</ixx><ixy>{_n(i[0][1])}</ixy><ixz>{_n(i[0][2])}</ixz>",
            f"          <iyy>{_n(i[1][1])}</iyy><iyz>{_n(i[1][2])}</iyz><izz>{_n(i[2][2])}</izz>",
            "        </inertia>",
            "      </inertial>",
            "      <gravity>true</gravity>",
        ]
        if self.mesh:
            lines += [
                '      <visual name="body">',
                f"        <geometry><mesh><uri>model://{self.name}/{self.mesh}</uri></mesh>"
                "</geometry>",
                "      </visual>",
            ]
        lines += [
            '      <collision name="plates">',
            f"        <pose>{_v(self.body_center)} 0 0 0</pose>",
            f"        <geometry><box><size>{_v(self.body_size)}</size></box></geometry>",
            "      </collision>",
        ]
        for k, (x, y, z) in enumerate(self.feet):
            lines += [
                f'      <collision name="foot_{k}">',
                f"        <pose>{_v((x, y, z + FOOT_RADIUS))} 0 0 0</pose>",
                f"        <geometry><sphere><radius>{_n(FOOT_RADIUS)}</radius></sphere></geometry>",
                "      </collision>",
            ]
        lines.append(SENSORS.rstrip("\n"))
        lines.append("    </link>")
        for r in self.rotors:
            ixx, iyy, izz = r.inertia
            lines += [
                f'    <link name="rotor_{r.number}">',
                f"      <pose>{_v(r.position)} 0 0 0</pose>",
                "      <inertial>",
                f"        <mass>{_n(r.mass)}</mass>",
                f"        <inertia><ixx>{_n(ixx)}</ixx><iyy>{_n(iyy)}</iyy><izz>{_n(izz)}</izz>"
                "</inertia>",
                "      </inertial>",
                f'      <visual name="rotor_{r.number}_visual">',
                f"        <geometry><cylinder><radius>{_n(r.radius)}</radius><length>0.002"
                "</length></cylinder></geometry>",
                "        <transparency>0.7</transparency>",
                "      </visual>",
                "    </link>",
                f'    <joint name="rotor_{r.number}_joint" type="revolute">',
                "      <parent>base_link</parent>",
                f"      <child>rotor_{r.number}</child>",
                "      <axis><xyz>0 0 1</xyz><limit><lower>-1e+16</lower><upper>1e+16</upper>"
                "</limit></axis>",
                "    </joint>",
            ]
        m = self.motor
        for r in self.rotors:
            lines += [
                '    <plugin filename="gz-sim-multicopter-motor-model-system"',
                '      name="gz::sim::systems::MulticopterMotorModel">',
                f"      <jointName>rotor_{r.number}_joint</jointName>",
                f"      <linkName>rotor_{r.number}</linkName>",
                f"      <turningDirection>{r.direction}</turningDirection>",
                f"      <timeConstantUp>{_n(m.time_constant_up)}</timeConstantUp>",
                f"      <timeConstantDown>{_n(m.time_constant_down)}</timeConstantDown>",
                f"      <maxRotVelocity>{_n(m.max_rot_velocity)}</maxRotVelocity>",
                f"      <motorConstant>{_n(m.motor_constant)}</motorConstant>",
                f"      <momentConstant>{_n(m.moment_constant)}</momentConstant>",
                "      <commandSubTopic>command/motor_speed</commandSubTopic>",
                f"      <motorNumber>{r.number}</motorNumber>",
                "      <rotorDragCoefficient>"
                f"{_n(m.rotor_drag_coefficient)}</rotorDragCoefficient>",
                "      <rollingMomentCoefficient>"
                f"{_n(m.rolling_moment_coefficient)}</rollingMomentCoefficient>",
                "      <rotorVelocitySlowdownSim>10</rotorVelocitySlowdownSim>",
                "      <motorType>velocity</motorType>",
                "    </plugin>",
            ]
        lines += [
            '    <plugin filename="pcs14-drag" name="pcs14::systems::Drag">',
            "      <link_name>base_link</link_name>",
            f"      <drag_area>{_n(self.drag_area)}</drag_area>",
            f"      <wind_topic>{WIND_TOPIC}</wind_topic>",
        ]
        if self.chute is not None:
            c = self.chute
            lines += [
                "      <chute>",
                f"        <canopy_area>{_n(c.canopy_area)}</canopy_area>",
                f"        <ejection_s>{_n(c.ejection_s)}</ejection_s>",
                f"        <opening_s>{_n(c.opening_s)}</opening_s>",
                f"        <fire_topic>{CHUTE_TOPIC}</fire_topic>",
                "      </chute>",
            ]
        lines.append("    </plugin>")
        if self.payload > 0:
            attach, detach = PAYLOAD_TOPICS
            lines += [
                '    <plugin filename="gz-sim-detachable-joint-system"',
                '      name="gz::sim::systems::DetachableJoint">',
                "      <parent_link>base_link</parent_link>",
                f"      <child_model>{PREFIX}payload</child_model>",
                "      <child_link>link</child_link>",
                f"      <attach_topic>{attach}</attach_topic>",
                f"      <detach_topic>{detach}</detach_topic>",
                "    </plugin>",
            ]
        lines += ["  </model>", "</sdf>", ""]
        return "\n".join(lines)


def payload_sdf(mass: float, size: float = 0.08) -> str:
    """The claws' payload: a box of `mass` kg, `size` m across."""
    inertia = mass * size**2 / 6
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<sdf version="1.9">',
            f'  <model name="{PREFIX}payload">',
            '    <link name="link">',
            f"      <inertial><mass>{_n(mass)}</mass><inertia><ixx>{_n(inertia)}</ixx>"
            f"<iyy>{_n(inertia)}</iyy><izz>{_n(inertia)}</izz></inertia></inertial>",
            f'      <collision name="box"><geometry><box><size>{_v((size,) * 3)}</size></box>'
            "</geometry></collision>",
            f'      <visual name="box"><geometry><box><size>{_v((size,) * 3)}</size></box>'
            "</geometry></visual>",
            "    </link>",
            "  </model>",
            "</sdf>",
            "",
        ]
    )


def world_sdf(name: str = "pcs14", wind=(0.0, 0.0, 0.0)) -> str:
    """PX4's default world, plus the wind our drag plugin starts from."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by pcs14 flight-sim: PX4's default world (PX4-gazebo-models b6127f4), with wind.
     The origin is PX4's own. -->
<sdf version="1.9">
  <world name="{name}">
    <physics type="ode">
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>250</real_time_update_rate>
    </physics>
    <gravity>0 0 -9.8</gravity>
    <magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field>
    <atmosphere type="adiabatic"/>
    <wind><linear_velocity>{_v(wind)}</linear_velocity></wind>
    <scene>
      <grid>false</grid>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.04 0.04 0.04 1</background>
      <shadows>true</shadows>
    </scene>
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>1 1</size></plane></geometry>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>500 500</size></plane></geometry>
          <material>
            <ambient>0.17 0.17 0.16 1</ambient>
            <diffuse>0.17 0.17 0.16 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    <light name="sun" type="directional">
      <pose>0 0 500 0 0 0</pose>
      <cast_shadows>true</cast_shadows>
      <intensity>1</intensity>
      <direction>0.001 0.625 -0.78</direction>
      <diffuse>0.904 0.904 0.904 1</diffuse>
      <specular>0.271 0.271 0.271 1</specular>
    </light>
    <spherical_coordinates>
      <surface_model>EARTH_WGS84</surface_model>
      <world_frame_orientation>ENU</world_frame_orientation>
      <latitude_deg>47.397971057728974</latitude_deg>
      <longitude_deg>8.546163739800146</longitude_deg>
      <elevation>0</elevation>
    </spherical_coordinates>
  </world>
</sdf>
"""


def px4_params(model: FlightModel, build, targets) -> dict:
    """PX4's parameters for this model, over the x500 airframe: the rotor geometry about the
    center of gravity (PX4's frame: x forward, y right, z down), the motors' speed range, the
    hover throttle, and limits that let the capability tests reach what the hardware can do.
    The legal limits are a separate profile, as always."""
    from pcs14.sizing.rotor import MAX_TILT

    cx, cy, cz = model.center
    m = model.motor
    low = round(IDLE_SHARE * m.max_rot_velocity)
    high = round(m.max_rot_velocity)
    params: dict = {"CA_ROTOR_COUNT": 4}
    for r in model.rotors:
        x, y, z = r.position
        n = r.number
        params[f"CA_ROTOR{n}_PX"] = round(x - cx, 4)
        params[f"CA_ROTOR{n}_PY"] = round(-(y - cy), 4)
        params[f"CA_ROTOR{n}_PZ"] = round(-(z - cz), 4)
        sign = 1 if r.direction == "ccw" else -1
        params[f"CA_ROTOR{n}_KM"] = round(sign * m.moment_constant, 4)
        params[f"SIM_GZ_EC_FUNC{n + 1}"] = 101 + n
        params[f"SIM_GZ_EC_MIN{n + 1}"] = low
        params[f"SIM_GZ_EC_MAX{n + 1}"] = high
    hover = (m.hover_rot_velocity - low) / (high - low)
    params["MPC_THR_HOVER"] = round(min(max(hover, 0.1), 0.8), 3)
    params["MPC_TILTMAX_AIR"] = round(math.degrees(MAX_TILT), 1)
    params["MPC_XY_VEL_MAX"] = TOP_SPEED_LIMIT
    params["MPC_VEL_MANUAL"] = TOP_SPEED_LIMIT
    params["MPC_XY_CRUISE"] = targets.cruise_speed
    pack = build.pack
    params["BAT1_N_CELLS"] = pack.series
    params["BAT1_CAPACITY"] = round(pack.cell.capacity_mah * pack.parallel)
    params["NAV_DLL_ACT"] = 2  # lost link: return, the x500's own
    return params


def flight_model(drone, build, targets, setup, mesh: str | None = "meshes/body.stl"):
    """One combination's model, from the CAD (`drone`, a pcs14.cad.assembly.Drone)."""
    from pcs14.cad.checks import trim
    from pcs14.cad.mass import mass_properties
    from pcs14.flight.motor import motor_model
    from pcs14.sizing.drag import drag_area

    assembly = trim(drone, setup.modules)
    body = [p for p in assembly.pieces if p.kind != "prop"]
    props = mass_properties(body)
    rotor_mass = build.prop.mass
    hub_z = build.motor.cad.size("bell_length_mm") + 0.002  # where the CAD seats the props
    mounts = drone.frame.motor_mounts
    rotors = []
    for number, (front, left, direction) in enumerate(ORDER):
        x, y, z = next(m for m in mounts if (m[0] > 0) == front and (m[1] > 0) == left)
        rotors.append(
            RotorSpot(number, (x, y, z + hub_z), direction, rotor_mass, build.prop.radius)
        )
    plates = drone.frame.body.bounding_box()
    legs = [p for p in assembly.pieces if p.part_id == "landing-legs"]
    feet = []
    for leg in legs:
        box = leg.solid.bounding_box()
        feet.append((box.center().X, box.center().Y, box.min.Z))
    chute = None
    for part in build.modules.get("P", ()):
        if "P" in setup.modules and getattr(part, "parachute", None) is not None:
            chute = Chute.from_part(part)
    model = FlightModel(
        name=f"{PREFIX}{setup.name.replace('+', '_').lower()}",
        setup=setup.name,
        modules=frozenset(setup.modules),
        mass=props.mass,
        center=tuple(props.center),
        inertia=tuple(tuple(row) for row in props.inertia),
        rotors=tuple(rotors),
        body_center=(plates.center().X, plates.center().Y, plates.center().Z),
        body_size=(plates.size.X, plates.size.Y, plates.size.Z),
        feet=tuple(feet),
        motor=motor_model(build, targets, setup, mass=props.mass + 4 * rotor_mass + setup.payload),
        drag_area=drag_area(build, setup),
        chute=chute,
        payload=setup.payload if "C" in setup.modules else 0.0,
        mesh=mesh,
    )
    from dataclasses import replace

    return replace(model, params=px4_params(model, build, targets))


def _config(name: str, what: str) -> str:
    return "\n".join(
        [
            '<?xml version="1.0"?>',
            "<model>",
            f"  <name>{name}</name>",
            "  <version>1.0</version>",
            '  <sdf version="1.9">model.sdf</sdf>',
            "  <author><name>Extra 15pc Gum (pcs14)</name></author>",
            f"  <description>Extra 15pc Gum, {what}: generated by pcs14 flight-sim</description>",
            "</model>",
            "",
        ]
    )


def model_config(model: FlightModel) -> str:
    return _config(model.name, model.setup)


def write_models(folder, drone, build, targets, setups, meshes: bool = True) -> list:
    """Every combination's model folder (model.config, model.sdf, PX4's parameters as
    params.json and, with `meshes`, the CAD's mesh), the world and the payload, under `folder`.
    Returns the models."""
    import json
    from pathlib import Path

    from pcs14.cad.checks import trim
    from pcs14.cad.export import export_gazebo

    folder = Path(folder)
    out = []
    for setup in setups:
        model = flight_model(
            drone, build, targets, setup, mesh="meshes/body.stl" if meshes else None
        )
        home = folder / "models" / model.name
        home.mkdir(parents=True, exist_ok=True)
        (home / "model.config").write_text(model_config(model), encoding="utf-8")
        (home / "model.sdf").write_text(model.sdf(), encoding="utf-8")
        params = json.dumps(model.params, indent=1, sort_keys=True) + "\n"
        (home / "params.json").write_text(params, encoding="utf-8")
        if meshes:
            pieces = [p for p in trim(drone, setup.modules).pieces if p.kind != "prop"]
            export_gazebo(pieces, home / "meshes" / "body.stl")
        out.append(model)
    payloads = [m.payload for m in out if m.payload > 0]
    if payloads:
        home = folder / "models" / f"{PREFIX}payload"
        home.mkdir(parents=True, exist_ok=True)
        (home / "model.sdf").write_text(payload_sdf(max(payloads)), encoding="utf-8")
        (home / "model.config").write_text(_config(f"{PREFIX}payload", "the payload"), "utf-8")
    worlds = folder / "worlds"
    worlds.mkdir(parents=True, exist_ok=True)
    (worlds / "pcs14.sdf").write_text(world_sdf(), encoding="utf-8")
    return out
