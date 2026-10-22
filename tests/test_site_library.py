"""The site's library, raw data and math, on a small made-up repo."""

import json

from pcs14.site import library, schema

PLAN = (
    "| Step | What it's for | Status | Outcome |\n|---|---|---|---|\n"
    "| 1. Sizing and parts | Real parts | Done | Picked |\n"
    "| 2. The virtual drone (CAD) | Every part | Done | Built |\n"
)


def made_up_repo(root):
    (root / "docs" / "log").mkdir(parents=True)
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "docs" / "reports" / "sizing" / "charts").mkdir(parents=True)
    (root / "README.md").write_text(
        "# Extra 15pc Gum\n\nSee [the log](docs/log/2026-10-21-sizing-x.md#what-broke), "
        "[the build](design/build.yaml) and ![a chart](docs/reports/sizing/charts/a.png).\n\n"
        + PLAN
    )
    (root / "docs" / "log" / "2026-10-21-sizing-x.md").write_text(
        "# 2026-10-21: A day\n\n## What broke\n\nBack to [the start](../../README.md).\n"
    )
    (root / "docs" / "log" / "2026-10-17-cad-talk.md").write_text("# 2026-10-17: Talk\n")
    (root / "docs" / "specs" / "2026-10-17-sizing.md").write_text(
        "# The sizing spec\n\n*Partly superseded: its order, by [the next](2026-10-21-x.md).*\n\n"
        "*Written 2026-10-17.*\n"
    )
    (root / "cad").mkdir()
    (root / "cad" / "README.md").write_text("# cad/\n\nThe drone as code.\n")
    (root / "CLAUDE.md").write_text("# CLAUDE.md\n\nNotes.\n")
    (root / "docs" / "reports" / "sizing" / "charts" / "a.png").write_bytes(b"png")
    (root / "docs" / "reports" / "sizing" / "sizing.json").write_text(
        json.dumps({"verdict": "pass", "setups": [1, 2, 3]})
    )
    src = root / "src" / "pcs14" / "sizing"
    src.mkdir(parents=True)
    (src / "flight.py").write_text(
        '"""Flight time from the pack."""\n\n\ndef _helper(x):\n    return x\n\n\n'
        "def hover_minutes(wh, watts):\n"
        '    """Minutes of hover: the energy over the power."""\n    return wh / watts * 60\n'
    )
    site = root / "src" / "pcs14" / "site"
    site.mkdir(parents=True)
    (site / "pages.py").write_text('"""The site\'s pages: not math."""\n')
    fw = root / "firmware" / "core" / "src"
    fw.mkdir(parents=True)
    (fw / "mixer.cpp").write_text("// The mixer: torques to motor speeds.\n\nint x;\n")


def test_every_doc_is_a_page_with_its_links_kept_on_the_site(tmp_path):
    root, out = tmp_path / "repo", tmp_path / "out"
    root.mkdir()
    made_up_repo(root)
    library.write_library(root, out)
    index = json.loads((out / "library.json").read_text())
    page = json.loads((out / "library" / "README.json").read_text())
    assert 'href="#/library/docs/log/2026-10-21-sizing-x~what-broke"' in page["html"]
    assert "github.com" in page["html"] and "design/build.yaml" in page["html"]
    assert 'src="./data/library/files/docs/reports/sizing/charts/a.png"' in page["html"]
    assert (
        out / "library" / "files" / "docs" / "reports" / "sizing" / "charts" / "a.png"
    ).is_file()
    back = json.loads((out / "library" / "docs" / "log" / "2026-10-21-sizing-x.json").read_text())
    assert 'href="#/library/README"' in back["html"]
    schema.Library.model_validate(index)


def test_the_work_goes_by_topic_newest_first_and_the_notes_go_last(tmp_path):
    root, out = tmp_path / "repo", tmp_path / "out"
    root.mkdir()
    made_up_repo(root)
    library.write_library(root, out)
    sections = json.loads((out / "library.json").read_text())["sections"]
    names = [s["name"] for s in sections]
    # the project, then each step's topic by its newest doc, then the folders, then the notes
    assert names == ["The project", "1. Sizing and parts", "2. The virtual drone (CAD)",
                     "The repo's folders", "Behind the scenes"]  # fmt: skip
    sizing = sections[1]
    assert sizing["group"] == "The work, by topic" and sizing["step"] == "sizing"
    assert [(d["kind"], d["date"]) for d in sizing["docs"]] == [("log", "2026-10-21"),
                                                                ("spec", "2026-10-17")]  # fmt: skip
    assert sizing["docs"][0]["title"] == "A day"  # its date is shown beside it, not in it
    spec = sizing["docs"][1]
    assert spec["superseded"] == "Partly superseded: its order, by the next."
    assert (
        sections[3]["docs"][0]["title"] == "cad/: the drone as code"
    )  # a folder says what it holds
    assert sections[4]["group"] == "Behind the scenes" and sections[4]["about"]


def test_the_data_says_what_each_file_holds_and_its_size(tmp_path):
    root, out = tmp_path / "repo", tmp_path / "out"
    root.mkdir()
    made_up_repo(root)
    library.write_raw(root, out)
    raw = json.loads((out / "raw" / "sizing.json").read_text())
    assert raw["data"] == {"verdict": "pass", "setups": [1, 2, 3]}
    (out / "steps.json").write_text("{}")
    (out / "flights").mkdir()
    (out / "flights" / "a.json").write_text("{}")
    (out / "flights" / "a.js").write_text("x" * 100)  # its twin, not counted
    library.write_data_index(root, out)
    index = schema.RawIndex.model_validate_json((out / "raw.json").read_text())
    (sizing,) = index.files
    assert sizing.title == "The sizing report's data" and sizing.about
    assert sizing.holds == ["verdict", "setups (3)"]
    assert (
        sizing.size_bytes == (root / "docs" / "reports" / "sizing" / "sizing.json").stat().st_size
    )
    site = {f.name: f for f in index.site}
    assert (
        site["steps.json"].about.startswith("A page per step")
        and site["steps.json"].view == "steps"
    )
    assert site["flights/"].files == 1 and site["flights/"].size_bytes == 2
    assert site["flights/"].view is None


def test_the_math_is_the_math_in_step_order_its_explained_functions_first(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    made_up_repo(root)
    math = library.math_data(root, commit="abc1234")
    assert [p.key for p in math.packages] == ["sizing", "firmware"]  # the site's code isn't math
    assert math.commit == "abc1234"
    sizing = math.packages[0]
    assert sizing.step == "1"
    module = sizing.modules[0]
    assert module.doc == "Flight time from the pack."
    assert [i.name for i in module.items] == ["hover_minutes", "_helper"]
    assert module.items[0].signature == "hover_minutes(wh, watts)"
    assert module.url.endswith("/blob/abc1234/src/pcs14/sizing/flight.py")  # pinned
    firmware = math.packages[1]
    assert firmware.modules[0].doc == "The mixer: torques to motor speeds."
