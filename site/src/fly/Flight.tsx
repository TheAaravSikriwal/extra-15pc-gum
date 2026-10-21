// The floating drone in Fly it. The drone stays where it is, in the middle, and turns with its
// logged attitude; the world moves past it instead: a faint ground grid far below, the trail
// of where it's been, and only what tells the story (the canopy once the chute fires, the wind
// streaking past, the column of rising air). Changing scenario eases from wherever the drone
// is into the next run's calm start. The loop's seam fades the whole canvas, when a run fell.
import { Grid } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { type RefObject, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";

import type { Playback } from "../data/types";
import { attitudeIn3 } from "../flights/FlightScene";
import { toThree } from "../flights/playback";
import type { Clip, Frame } from "./clip";
import { handoff, type Numbers, numbersAt, propSpeeds, type StoryProps } from "./fly";

const HANDOFF_S = 1.0; // how long the drone takes to ease from one scenario into the next
const NUMBERS_EVERY_S = 0.15;
const TRAIL_S = 4; // about how much of the loop the trail behind it shows
const LINES = "#9a9a96";
// the canopy drawn closer than its real lines hold it (the IFC-42's are a few meters), so it
// stays in the frame
const CANOPY_M = 1.1;

// the drone at rest when nothing's playing: level, its motors at an idle hover
const CALM: Frame = { t: 0, position: [0, 0, 0], attitude: [0, 0, 0, 1], motors: [300, 300, 300, 300], speed: 1, fade: 1 };

export interface Playing extends Numbers {
  motors: number[];
}

export interface FlightProps {
  drone: RefObject<THREE.Group>; // what turns with the attitude
  spins: { current: Record<string, number> | null }; // each prop's speed, for the scene
  clip: Clip | null;
  playback: Playback | null;
  story: StoryProps | null;
  onNumbers: (n: Playing) => void;
}

// a dome of light gray lines over the drone, and its lines down to it
function canopy(): THREE.Group {
  const group = new THREE.Group();
  const material = new THREE.LineBasicMaterial({ color: LINES, transparent: true, opacity: 0.8 });
  const dome = new THREE.SphereGeometry(0.53, 16, 6, 0, Math.PI * 2, 0, Math.PI / 2.4);
  const lines = new THREE.LineSegments(new THREE.WireframeGeometry(dome), material);
  lines.position.y = CANOPY_M;
  group.add(lines);
  const rim = 0.53 * Math.sin(Math.PI / 2.4);
  const rimY = CANOPY_M + 0.53 * Math.cos(Math.PI / 2.4);
  const shrouds: THREE.Vector3[] = [];
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2;
    shrouds.push(new THREE.Vector3(rim * Math.cos(a), rimY, rim * Math.sin(a)), new THREE.Vector3(0, 0.05, 0));
  }
  group.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(shrouds), material));
  return group;
}

// short streaks blowing past, around the drone
function streaks(): THREE.LineSegments {
  const points: THREE.Vector3[] = [];
  for (let k = 0; k < 18; k++) {
    const x = ((k * 37) % 11) / 11 - 0.5;
    const y = ((k * 23) % 7) / 7 - 0.5;
    const z = ((k * 53) % 13) / 13 - 0.5;
    points.push(new THREE.Vector3(x * 2.4, y * 1.2, z * 2.4), new THREE.Vector3(x * 2.4, y * 1.2, z * 2.4 - 0.35));
  }
  return new THREE.LineSegments(
    new THREE.BufferGeometry().setFromPoints(points),
    new THREE.LineBasicMaterial({ color: LINES, transparent: true, opacity: 0.7 }),
  );
}

export function Flight({ drone, spins, clip, playback, story, onNumbers }: FlightProps) {
  const gl = useThree((s) => s.gl);
  const world = useRef<THREE.Group>(null);
  const loop = useRef(0);
  const since = useRef(HANDOFF_S);
  const from = useRef<Frame | null>(null);
  const last = useRef<Frame>(CALM);
  const told = useRef(0);
  const trail = useMemo(
    () => new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: LINES, transparent: true, opacity: 0.6 })),
    [],
  );
  const dome = useMemo(canopy, []);
  const wind = useMemo(streaks, []);
  // the column of rising air, where the run flew into it
  const column = useMemo(() => {
    if (!playback || story?.columnFrom == null) return null;
    const k = playback.t.findIndex((t) => t >= (story.columnFrom ?? 0));
    const [x, , z] = toThree(playback.position[Math.max(k, 0)]);
    const mesh = new THREE.LineSegments(
      new THREE.WireframeGeometry(new THREE.CylinderGeometry(4, 4, 40, 12, 4, true)),
      new THREE.LineBasicMaterial({ color: LINES, transparent: true, opacity: 0.25 }),
    );
    mesh.position.set(x, 20 + (clip?.ground ?? 0), z);
    return mesh;
  }, [playback, story, clip]);

  // a new scenario starts from its beginning, easing in from wherever the drone was
  useEffect(() => {
    from.current = last.current;
    since.current = 0;
    loop.current = 0;
  }, [clip]);

  // leaving Fly it puts the drone back as it was
  useEffect(() => {
    const target = drone.current;
    return () => {
      target?.quaternion.identity();
      spins.current = null;
      gl.domElement.style.opacity = "1";
    };
  }, [drone, spins, gl]);

  useFrame((_, delta) => {
    if (clip) loop.current = (loop.current + delta) % clip.duration;
    let frame = clip ? clip.at(loop.current) : CALM;
    if (from.current && since.current < HANDOFF_S) {
      frame = handoff(from.current, frame, since.current / HANDOFF_S);
      since.current += delta;
    }
    last.current = frame;
    drone.current?.quaternion.copy(attitudeIn3(frame.attitude));
    spins.current = propSpeeds(frame.motors);
    gl.domElement.style.opacity = String(frame.fade);
    const here = toThree(frame.position);
    world.current?.position.set(-here[0], -here[1], -here[2]);
    // the trail: the run's path for the last few seconds of the loop
    if (playback && clip) {
      const back = frame.t - TRAIL_S * frame.speed;
      const points = playback.t
        .map((t, k) => (t >= back && t <= frame.t ? new THREE.Vector3(...toThree(playback.position[k])) : null))
        .filter((v): v is THREE.Vector3 => v !== null);
      points.push(new THREE.Vector3(...here));
      trail.geometry.dispose();
      trail.geometry = new THREE.BufferGeometry().setFromPoints(points);
    }
    dome.visible = story?.canopyFrom != null && frame.t >= story.canopyFrom;
    wind.visible = story?.windFrom != null && frame.t >= story.windFrom;
    if (wind.visible) wind.position.z = -(((loop.current * 2.5) % 1.2) - 0.6);
    told.current += delta;
    if (clip && told.current >= NUMBERS_EVERY_S) {
      told.current = 0;
      onNumbers({ ...numbersAt(clip, loop.current), motors: frame.motors });
    }
  });

  return (
    <>
      <group ref={world}>
        <Grid
          position={[0, clip?.ground ?? 0, 0]}
          args={[200, 200]}
          cellSize={1}
          cellThickness={0.6}
          cellColor="#d6d6d2"
          sectionSize={10}
          sectionThickness={1}
          sectionColor="#bdbdb8"
          fadeDistance={70}
          fadeStrength={1.5}
          infiniteGrid
        />
        <primitive object={trail} />
        {column && <primitive object={column} />}
      </group>
      <primitive object={dome} />
      <primitive object={wind} />
    </>
  );
}
