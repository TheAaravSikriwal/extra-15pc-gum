// The combinations in one order everywhere (as the sizing report has them), and the modules' names.
export const COMBINATIONS = ["base", "V", "P", "C", "mission", "V+C", "P+C", "max"];

export const MODULE_NAMES: Record<string, string> = {
  V: "Vision and navigation",
  P: "The parachute",
  C: "The claws",
};

// items sorted into the combinations' order; anything not a combination goes last, as it was
export function byCombination<T>(items: T[], name: (item: T) => string): T[] {
  const rank = (item: T) => {
    const k = COMBINATIONS.indexOf(name(item));
    return k < 0 ? COMBINATIONS.length : k;
  };
  return [...items].sort((a, b) => rank(a) - rank(b));
}
