"""Writing the report folder: README.md, charts/ and sizing.json."""

import json
from pathlib import Path

from pcs14.report import charts, markdown
from pcs14.report.data import to_data

REAL_REPORTS = Path(__file__).resolve().parents[3] / "docs" / "reports"


def write_report(
    out: Path,
    design,
    sweep=None,
    margin=None,
    made_up: bool = False,
    generated: str | None = None,
    draw_charts: bool = True,
) -> Path:
    """Write the report into `out`. A report made from made-up parts can't go in docs/reports/,
    which is where the real ones live."""
    out = Path(out).resolve()
    if made_up and (out == REAL_REPORTS or REAL_REPORTS in out.parents):
        raise ValueError(
            "a made-up report can't go in docs/reports/, which is only for real parts. "
            "Write it somewhere like outputs/ instead."
        )
    out.mkdir(parents=True, exist_ok=True)
    text = markdown.render(design, sweep, margin, made_up=made_up, generated=generated)
    (out / "README.md").write_bytes(text.encode("utf-8"))
    data = to_data(design, sweep, margin, made_up=made_up, generated=generated)
    (out / "sizing.json").write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
    if draw_charts:
        charts.draw_all(design, sweep, margin, out / "charts", made_up)
    return out
