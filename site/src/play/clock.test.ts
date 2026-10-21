import { Clock } from "./clock";

function fakeTime() {
  let now = 0;
  return { now: () => now, advance: (ms: number) => (now += ms) };
}

test("it runs at real speed while playing, and holds still while paused", () => {
  const t = fakeTime();
  const clock = new Clock({ duration: 60, now: t.now });
  expect(clock.time()).toBe(0);
  clock.play();
  t.advance(2500);
  expect(clock.time()).toBeCloseTo(2.5);
  clock.pause();
  t.advance(5000);
  expect(clock.time()).toBeCloseTo(2.5);
});

test("the speed control scales it, and it stops at the end", () => {
  const t = fakeTime();
  const clock = new Clock({ duration: 10, now: t.now });
  clock.setSpeed(4);
  clock.play();
  t.advance(1000);
  expect(clock.time()).toBeCloseTo(4);
  t.advance(10000);
  expect(clock.time()).toBe(10);
  expect(clock.playing()).toBe(false);
});

test("the scrubber seeks, and a chapter mark jumps to its event", () => {
  const t = fakeTime();
  const clock = new Clock({
    duration: 120,
    now: t.now,
    chapters: [
      { at: 10, name: "armed" },
      { at: 43.2, name: "motor failed" },
    ],
  });
  clock.seek(30);
  expect(clock.time()).toBe(30);
  clock.jumpTo("motor failed");
  expect(clock.time()).toBeCloseTo(43.2);
  clock.seek(500);
  expect(clock.time()).toBe(120);
  expect(clock.chapterAt(50)?.name).toBe("motor failed");
  expect(clock.chapterAt(5)).toBeUndefined();
});

test("seeking while playing carries on from there", () => {
  const t = fakeTime();
  const clock = new Clock({ duration: 60, now: t.now });
  clock.play();
  t.advance(1000);
  clock.seek(20);
  t.advance(1000);
  expect(clock.time()).toBeCloseTo(21);
});
