// One data file for a page: loading, then the data or the problem with it.
import { useEffect, useState } from "react";

import { loadData, type LoadOptions } from "./load";

// a data file that's only sometimes wanted: nothing while there's no name, and nothing if it fails
export function useOptionalData<T extends { schema_version: number }>(name: string | null, options?: LoadOptions): T | null {
  const [data, setData] = useState<T | null>(null);
  useEffect(() => {
    if (!name) {
      setData(null);
      return;
    }
    let live = true;
    loadData<T>(name, options)
      .then((d) => live && setData(d))
      .catch(() => live && setData(null));
    return () => {
      live = false;
    };
  }, [name, options]);
  return data;
}

export function useData<T extends { schema_version: number }>(
  name: string,
  options?: LoadOptions,
): { data: T | null; problem: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    loadData<T>(name, options)
      .then((d) => live && setData(d))
      .catch((e: Error) => live && setProblem(e.message));
    return () => {
      live = false;
    };
  }, [name, options]);
  return { data, problem };
}
