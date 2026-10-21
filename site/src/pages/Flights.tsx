// Every flight: both firmwares' matrices, each flown cell a link to its run's playback.
import { Matrix } from "../charts/Matrix";
import type { LoadOptions } from "../data/load";
import type { Flights as FlightsData } from "../data/types";
import { useData } from "../data/useData";
import { cellFor } from "../flights/playback";

export function runLink(setup: string, scenario: string): string {
  return `#/flights/${encodeURIComponent(setup)}/${encodeURIComponent(scenario)}`;
}

const NAMES: Record<string, string> = { px4: "PX4 v1.17.0", mine: "My firmware" };

export function Flights({ load }: { load?: LoadOptions }) {
  const { data, problem } = useData<FlightsData>("flights.json", load);
  if (problem) return <p role="alert">{problem}</p>;
  if (!data) return <p>Loading</p>;
  return (
    <main className="wide">
      <h1>Every flight</h1>
      <p>
        Twelve scenarios in eight module combinations, flown in Gazebo by PX4 and by my own
        firmware, graded the same way. Pick any run to watch it.
      </p>
      {["px4", "mine"].map((firmware) => {
        const runs = data.runs.filter((r) => r.firmware === firmware);
        const passed = runs.filter((r) => r.passed).length;
        return (
          <section key={firmware} aria-label={NAMES[firmware]}>
            <h2>
              {NAMES[firmware]}: {passed} of {runs.length} pass
            </h2>
            <Matrix
              title={`${NAMES[firmware]} runs`}
              rows={data.scenarios}
              columns={data.setups}
              cell={(scenario, setup) =>
                runs.some((r) => r.scenario === scenario && r.setup === setup)
                  ? cellFor(data, firmware, scenario, setup)
                  : ""
              }
              link={(scenario, setup) => runLink(setup, scenario)}
            />
          </section>
        );
      })}
    </main>
  );
}
