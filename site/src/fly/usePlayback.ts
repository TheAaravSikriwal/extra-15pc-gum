// One run's playback file, loaded when there's one to play.
import { useEffect, useState } from "react";

import { loadData, type LoadOptions } from "../data/load";
import type { Playback } from "../data/types";

export function usePlayback(file: string | null, load?: LoadOptions): Playback | null {
  const [data, setData] = useState<Playback | null>(null);
  useEffect(() => {
    if (!file) {
      setData(null);
      return;
    }
    let live = true;
    loadData<Playback>(file, load)
      .then((d) => live && setData(d))
      .catch(() => live && setData(null));
    return () => {
      live = false;
    };
  }, [file, load]);
  return data;
}
