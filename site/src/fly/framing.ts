// Where the camera sits for Fly it: farther back than inside the drone and lower, so the drone
// floats with the ground grid below it and room above for a canopy, looking the same way it
// already looked.
type Vec3 = [number, number, number];

export const FLY_PULL = 2.2; // times as far from the drone as inside it
export const FLY_ELEVATION_DEG = 14; // how far above level it looks down from
export const MODE_S = 1.2; // the change between the two, background, camera and interface together

export function flyFraming(position: Vec3, target: Vec3): { position: Vec3; target: Vec3 } {
  const d = position.map((v, i) => v - target[i]);
  const distance = Math.hypot(...d) * FLY_PULL;
  const heading = Math.atan2(d[2], d[0]);
  const up = (FLY_ELEVATION_DEG * Math.PI) / 180;
  const flat = distance * Math.cos(up);
  return {
    position: [target[0] + flat * Math.cos(heading), target[1] + distance * Math.sin(up), target[2] + flat * Math.sin(heading)],
    target,
  };
}
