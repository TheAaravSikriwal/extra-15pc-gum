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
        Every scenario from steps 4 to 7, flown in Gazebo. Step 4's twelve were flown by PX4 and by
        my own firmware in all eight module combinations, graded the same way; the modules' and
        the smart features' runs from steps 6 and 7 by mine. Pick any run to watch it.
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
              rows={data.scenarios.filter((s) => runs.some((r) => r.scenario === s))}
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
