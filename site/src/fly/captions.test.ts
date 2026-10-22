import { captionAt, eventWords, firstSentence } from "./captions";

const EVENTS = [
  { at: 5, name: "armed" },
  { at: 5.2, name: "took off" },
  { at: 12, name: "hold" },
  { at: 12, name: "hold start" }, // a grader's window, not a moment
  { at: 38.9, name: "chute fired" },
  { at: 40, name: "motor failed" },
  { at: 40.5, name: "motor failed" }, // a flag raised again
  { at: 47.6, name: "landed" },
];

test("each kind of event in plain words, numbered ones counted from one", () => {
  expect(eventWords("chute fired")).toBe("The chute fires");
  expect(eventWords("step 0 start")).toBe("Stick step 1");
  expect(eventWords("waypoint 2")).toBe("Waypoint 2");
  expect(eventWords("something new")).toBe("Something new"); // anything else, as it's named
});

test("a scenario's line is its description's first sentence", () => {
  expect(firstSentence("Ten meters up, held for a minute. The baseline everything else is measured against.")).toBe(
    "Ten meters up, held for a minute.",
  );
  expect(firstSentence("From 10 m up. Flight termination in Max.")).toBe("From 10 m up.");
  expect(firstSentence("No full stop")).toBe("No full stop");
});

test("the caption is the last thing that happened, said once", () => {
  expect(captionAt(EVENTS, 3)?.text).toBeUndefined();
  expect(captionAt(EVENTS, 8)).toEqual({ at: 5.2, text: "Taking off" });
  expect(captionAt(EVENTS, 20)?.text).toBe("Holding its height");
  expect(captionAt(EVENTS, 39)?.text).toBe("The chute fires");
  expect(captionAt(EVENTS, 41)).toEqual({ at: 40, text: "Motor 1 stops" }); // the first time it's raised
  expect(captionAt(EVENTS, 60)?.text).toBe("Down");
});
