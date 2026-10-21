import { fireEvent, render, screen } from "@testing-library/react";

import { Clock } from "./clock";
import { Controls, formatTime } from "./Controls";

function makeClock() {
  let now = 0;
  const clock = new Clock({
    duration: 90,
    now: () => now,
    chapters: [{ at: 43.2, name: "motor failed" }],
  });
  return { clock, advance: (ms: number) => (now += ms) };
}

test("times read as minutes and seconds", () => {
  expect(formatTime(0)).toBe("0:00.0");
  expect(formatTime(83.25)).toBe("1:23.3");
});

test("a page can bring its own speeds and its own time format", () => {
  const { clock } = makeClock();
  render(<Controls clock={clock} speeds={[0.01, 0.05]} format={(t) => `${Math.round(t * 1000)} ms`} />);
  expect(screen.getByText("0 ms / 90000 ms")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("speed"), { target: { value: "0.05" } });
  expect(clock.getSpeed()).toBe(0.05);
});

test("play starts the clock and pause stops it", () => {
  const { clock } = makeClock();
  render(<Controls clock={clock} />);
  fireEvent.click(screen.getByRole("button", { name: "Play" }));
  expect(clock.playing()).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Pause" }));
  expect(clock.playing()).toBe(false);
});

test("the scrubber seeks, the speed sets, and an event's button jumps to it", () => {
  const { clock } = makeClock();
  render(<Controls clock={clock} />);
  fireEvent.change(screen.getByLabelText("scrubber"), { target: { value: "30" } });
  expect(clock.time()).toBe(30);
  fireEvent.change(screen.getByLabelText("speed"), { target: { value: "4" } });
  expect(clock.getSpeed()).toBe(4);
  fireEvent.click(screen.getByRole("button", { name: /motor failed/ }));
  expect(clock.time()).toBeCloseTo(43.2);
});
