// The CAD's GLB, loaded once per page: the 3D page and the flight pages both use it.
import { useEffect, useState } from "react";
import type * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { loadBinary, type LoadOptions } from "../data/load";

export function useModel(name: string, load?: LoadOptions) {
  const [root, setRoot] = useState<THREE.Object3D | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    loadBinary(name, load)
      .then((bytes) => new GLTFLoader().parseAsync(bytes, ""))
      .then((gltf) => live && setRoot(gltf.scene))
      .catch((e: Error) => live && setProblem(e.message));
    return () => {
      live = false;
    };
  }, [name, load]);
  return { root, problem };
}
