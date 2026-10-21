"""The site's library, catalog, raw data and math, on a small made-up repo."""

import json

from pcs14.site import library


def made_up_repo(root):
    (root / "docs" / "log").mkdir(parents=True)
    (root / "docs" / "reports" / "sizing" / "charts").mkdir(parents=True)
    (root / "README.md").write_text(
        "# Extra 15pc Gum\n\nSee [the log](docs/log/2026-10-21-x.md#what-broke), "
        "[the build](design/build.yaml) and ![a chart](docs/reports/sizing/charts/a.png).\n"
    )
    (root / "docs" / "log" / "2026-10-21-x.md").write_text(
        "# A day\n\n## What broke\n\nBack to [the start](../../README.md).\n"
    )
    (root / "docs" / "reports" / "sizing" / "charts" / "a.png").write_bytes(b"png")
    (root / "docs" / "reports" / "sizing" / "sizing.json").write_text(
        json.dumps({"verdict": "pass"})
    )
    src = root / "src" / "pcs14" / "sizing"
    src.mkdir(parents=True)
    (src / "flight.py").write_text(
        '"""Flight time from the pack."""\n\n\ndef hover_minutes(wh, watts):\n'
        '    """Minutes of hover: the energy over the power."""\n    return wh / watts * 60\n'
    )
    fw = root / "firmware" / "core" / "src"
    fw.mkdir(parents=True)
    (fw / "mixer.cpp").write_text("// The mixer: torques to motor speeds.\n\nint x;\n")


def test_every_doc_is_a_page_with_its_links_kept_on_the_site(tmp_path):
    root, out = tmp_path / "repo", tmp_path / "out"
    root.mkdir()
    made_up_repo(root)
    library.write_library(root, out)
    index = json.loads((out / "library.json").read_text())
    names = {s["name"]: [d["title"] for d in s["docs"]] for s in index["sections"]}
    assert names == {"The project": ["Extra 15pc Gum"], "The log": ["A day"]}
    page = json.loads((out / "library" / "README.json").read_text())
    assert 'href="#/library/docs/log/2026-10-21-x~what-broke"' in page["html"]
    assert "github.com" in page["html"] and "design/build.yaml" in page["html"]
    assert 'src="./data/library/files/docs/reports/sizing/charts/a.png"' in page["html"]
    assert (
        out / "library" / "files" / "docs" / "reports" / "sizing" / "charts" / "a.png"
    ).is_file()
    back = json.loads((out / "library" / "docs" / "log" / "2026-10-21-x.json").read_text())
    assert 'href="#/library/README"' in back["html"]


def test_the_raw_data_and_the_math_come_along(tmp_path):
    root, out = tmp_path / "repo", tmp_path / "out"
    root.mkdir()
    made_up_repo(root)
    library.write_raw(root, out)
    raw = json.loads((out / "raw" / "sizing.json").read_text())
    assert raw["data"] == {"verdict": "pass"}
    math = library.math_data(root)
    sizing = next(p for p in math.packages if p.key == "sizing")
    module = sizing.modules[0]
    assert module.doc == "Flight time from the pack."
    assert module.items[0].signature == "hover_minutes(wh, watts)"
    firmware = next(p for p in math.packages if p.key == "firmware")
    assert firmware.modules[0].doc == "The mixer: torques to motor speeds."
