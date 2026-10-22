// The wind tunnel's flow around the drone, in Fly it, moving: a few thousand particles carried
// through the recorded flow, each a dot with a short tail, fading in as it's released and out as
// it goes, colored in turbo by the air's speed, and the speed on a slice through the drone playing frame
// by frame, blended on the GPU, so the wake is seen shedding and flapping. All of it runs on one
// loop of the air's own time, slowed down twenty times, and sits in the drone's own frame (the
// CAD's, z up) inside the group that turns with the drone.
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import { type LoadOptions, loadBinary } from "../data/load";
import type { TunnelFlow } from "../data/types";
import { decodeParticles, frameAt, trailsAt, trailVertices } from "./particles";
import { turbo } from "./turbo";

const FADE_IN_S = 0.8;
const SLICE_OPACITY = 0.85;

// turbo as a texture, for the slice's shader, a little deeper to read on white
function turboTexture(): THREE.DataTexture {
  const data = new Uint8Array(256 * 4);
  for (let k = 0; k < 256; k++) {
    const [r, g, b] = turbo(k / 255);
    data.set([r * 217, g * 217, b * 217, 255], k * 4);
  }
  const texture = new THREE.DataTexture(data, 256, 1);
  texture.magFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

const SLICE_VERTEX = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

// the slice's speed at this moment, blended between its frames, in turbo, and clear where the air
// goes at the wind's own speed (in the hover, where it's still), so the wake and speedups stand out
const SLICE_FRAGMENT = /* glsl */ `
precision highp sampler3D;
uniform sampler3D uFrames;
uniform sampler2D uTurbo;
uniform float uFrame;
uniform float uCount;
uniform float uWind;
uniform float uTop;
uniform float uOpacity;
varying vec2 vUv;
void main() {
  float share = texture(uFrames, vec3(vUv.x, 1.0 - vUv.y, (uFrame + 0.5) / uCount)).r;
  float speed = share * uTop;
  float off = uWind > 0.0 ? abs(speed - uWind) / (0.6 * uWind) : speed / (0.5 * uTop);
  // soft edges all round, and a long fade where the flow leaves it: the wind's far end, or the
  // bottom in the hover, where the downwash goes
  float edges = smoothstep(0.0, 0.12, vUv.x) * smoothstep(0.0, 0.12, 1.0 - vUv.x)
              * smoothstep(0.0, 0.15, vUv.y) * smoothstep(0.0, 0.15, 1.0 - vUv.y);
  float away = uWind > 0.0 ? smoothstep(0.0, 0.45, 1.0 - vUv.x) : smoothstep(0.0, 0.4, vUv.y);
  float alpha = pow(clamp(off, 0.0, 1.0), 0.8) * edges * away * uOpacity;
  gl_FragColor = vec4(texture(uTurbo, vec2(share, 0.5)).rgb, alpha);
}`;

function useBytes(file: string, load?: LoadOptions): ArrayBuffer | null {
  const [bytes, setBytes] = useState<ArrayBuffer | null>(null);
  useEffect(() => {
    let live = true;
    setBytes(null);
    loadBinary(file, load)
      .then((b) => live && setBytes(b))
      .catch(() => live && setBytes(null));
    return () => {
      live = false;
    };
  }, [file, load]);
  return bytes;
}

export function Airflow({ flow, slice, load }: { flow: TunnelFlow; slice: boolean; load?: LoadOptions }) {
  const particleBytes = useBytes(flow.particles.file, load);
  const sliceBytes = useBytes(flow.slice.file, load);
  const set = useMemo(
    () => (particleBytes ? decodeParticles(particleBytes, flow.color_max, flow.speed) : null),
    [particleBytes, flow],
  );
  const clock = useRef(0);
  const fade = useRef(0);

  const trails = useMemo(() => {
    if (!set) return null;
    const vertices = trailVertices(set);
    const geometry = new THREE.BufferGeometry();
    const position = new THREE.BufferAttribute(new Float32Array(vertices * 3), 3).setUsage(THREE.DynamicDrawUsage);
    const color = new THREE.BufferAttribute(new Float32Array(vertices * 4), 4).setUsage(THREE.DynamicDrawUsage);
    geometry.setAttribute("position", position);
    geometry.setAttribute("color", color);
    const material = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, opacity: 0 });
    const lines = new THREE.LineSegments(geometry, material);
    lines.frustumCulled = false;
    lines.renderOrder = 2;
    // and a dot at each one's head
    const dots = new THREE.BufferGeometry();
    dots.setAttribute("position", new THREE.BufferAttribute(new Float32Array(set.count * 3), 3).setUsage(THREE.DynamicDrawUsage));
    dots.setAttribute("color", new THREE.BufferAttribute(new Float32Array(set.count * 4), 4).setUsage(THREE.DynamicDrawUsage));
    const heads = new THREE.Points(
      dots,
      new THREE.PointsMaterial({ size: 3, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false, opacity: 0 }),
    );
    heads.frustumCulled = false;
    heads.renderOrder = 3;
    lines.add(heads);
    return lines;
  }, [set]);

  const plane = useMemo(() => {
    if (!sliceBytes) return null;
    const { width, height, corners } = flow.slice;
    const frames = new THREE.Data3DTexture(new Uint8Array(sliceBytes), width, height, flow.frames);
    frames.format = THREE.RedFormat;
    frames.type = THREE.UnsignedByteType;
    frames.minFilter = frames.magFilter = THREE.LinearFilter;
    frames.wrapR = THREE.RepeatWrapping; // the last frame blends into the first
    frames.unpackAlignment = 1;
    frames.needsUpdate = true;
    const [a, b, c, d] = corners;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array([...a, ...b, ...c, ...d]), 3));
    geometry.setAttribute("uv", new THREE.BufferAttribute(new Float32Array([0, 1, 1, 1, 1, 0, 0, 0]), 2));
    geometry.setIndex([0, 3, 1, 1, 3, 2]);
    const material = new THREE.ShaderMaterial({
      vertexShader: SLICE_VERTEX,
      fragmentShader: SLICE_FRAGMENT,
      uniforms: {
        uFrames: { value: frames },
        uTurbo: { value: turboTexture() },
        uFrame: { value: 0 },
        uCount: { value: flow.frames },
        uWind: { value: flow.speed },
        uTop: { value: flow.color_max },
        uOpacity: { value: 0 },
      },
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = 1;
    return mesh;
  }, [sliceBytes, flow]);

  useEffect(
    () => () => {
      if (trails) {
        for (const o of [trails, ...trails.children] as (THREE.LineSegments | THREE.Points)[]) {
          o.geometry.dispose();
          (o.material as THREE.Material).dispose();
        }
      }
      if (plane) {
        const m = plane.material as THREE.ShaderMaterial;
        m.uniforms.uFrames.value.dispose();
        m.uniforms.uTurbo.value.dispose();
        plane.geometry.dispose();
        m.dispose();
      }
    },
    [trails, plane],
  );

  useFrame((_, delta) => {
    clock.current += delta;
    fade.current = Math.min(1, fade.current + delta / FADE_IN_S);
    const frame = frameAt(clock.current, flow.loop_s, flow.frames);
    if (trails && set) {
      const heads = trails.children[0] as THREE.Points;
      const position = trails.geometry.attributes.position as THREE.BufferAttribute;
      const color = trails.geometry.attributes.color as THREE.BufferAttribute;
      const dot = heads.geometry.attributes.position as THREE.BufferAttribute;
      const dotColor = heads.geometry.attributes.color as THREE.BufferAttribute;
      trailsAt(set, frame, position.array as Float32Array, color.array as Float32Array, dot.array as Float32Array, dotColor.array as Float32Array);
      for (const a of [position, color, dot, dotColor]) a.needsUpdate = true;
      (trails.material as THREE.LineBasicMaterial).opacity = fade.current;
      (heads.material as THREE.PointsMaterial).opacity = fade.current;
    }
    if (plane) {
      const u = (plane.material as THREE.ShaderMaterial).uniforms;
      u.uFrame.value = frame;
      const target = slice ? SLICE_OPACITY * fade.current : 0;
      u.uOpacity.value += (target - u.uOpacity.value) * Math.min(1, delta * 4);
      plane.visible = u.uOpacity.value > 0.01;
    }
  });

  return (
    <>
      {trails && <primitive object={trails} />}
      {plane && <primitive object={plane} />}
    </>
  );
}
