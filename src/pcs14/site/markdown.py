"""Markdown to HTML for the site's library: the repo's own docs, so only what they use.

Headings (with GitHub's anchors), paragraphs, bullet and numbered lists (nested by two spaces),
task boxes, tables, fenced code, block quotes, rules, and the raw `<details>` and `<summary>`
blocks the electrical report folds its long lists into. Inline: code, bold, italics, links,
images and `<br>`. Everything else is escaped. No library: none is installed, and these docs
don't need one.
"""

import html as _html
import re

RAW_BLOCK = re.compile(r"^\s*</?(details|summary)\b.*$")
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
LIST_ITEM = re.compile(r"^( *)([-*]|\d+\.) (.*)$")
HEADING = re.compile(r"^(#{1,6}) (.*?)#*\s*$")


def anchor(text: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation out, spaces to hyphens."""
    plain = _html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"[^a-z0-9 -]", "", plain.lower()).strip().replace(" ", "-")


def _same(url: str) -> str:
    return url


def inline(text: str, link=_same, image=_same) -> str:
    """One line's or one cell's inline marks. Code spans are set aside first, so marks around
    them (an italic line with code in it) still pair up, and nothing inside them is a mark."""
    codes: list[str] = []

    def code(m):
        codes.append(f"<code>{_html.escape(m.group(1), quote=False)}</code>")
        return f"\x01{len(codes) - 1}\x01"

    text = re.sub(r"`([^`]+)`", code, text)
    out = _marks(text, link, image)
    return re.sub(r"\x01(\d+)\x01", lambda m: codes[int(m.group(1))], out)


def _marks(text: str, link, image) -> str:
    keep: list[str] = []

    def stash(s: str) -> str:
        keep.append(s)
        return f"\x00{len(keep) - 1}\x00"

    text = re.sub(r"<br\s*/?>", lambda m: stash("<br>"), text)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)\)",
        lambda m: stash(
            f'<img src="{_html.escape(image(m.group(2)))}" alt="{_html.escape(m.group(1))}">'
        ),
        text,
    )
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: stash(
        f'<a href="{_html.escape(link(m.group(2)))}">'
        f"{_marks(m.group(1), link, image)}</a>"), text)  # fmt: skip
    text = _html.escape(text, quote=True)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], text)
    return text


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def _list(lines: list[str], link, image) -> str:
    """A run of list lines, nested by indentation."""
    out: list[str] = []
    stack: list[tuple[int, str]] = []  # (indent, "ul" or "ol")
    for line in lines:
        m = LIST_ITEM.match(line)
        if m is None:  # a continuation of the item before
            if out:
                out[-1] = (
                    out[-1][: -len("</li>")] + " " + inline(line.strip(), link, image) + "</li>"
                )
            continue
        indent, mark, body = len(m.group(1)), m.group(2), m.group(3)
        kind = "ol" if mark[0].isdigit() else "ul"
        while stack and indent < stack[-1][0]:
            out.append(f"</{stack.pop()[1]}>")
            out[-1] = out[-1]  # the parent item closes after its sublist
            out.append("</li>")
        if not stack or indent > stack[-1][0]:
            if stack and out and out[-1].endswith("</li>"):
                out[-1] = out[-1][: -len("</li>")]
            stack.append((indent, kind))
            out.append(f"<{kind}>")
        box = re.match(r"\[( |x)\] (.*)$", body)
        if box:
            checked = " checked" if box.group(1) == "x" else ""
            body_html = (
                f'<input type="checkbox" disabled{checked}> {inline(box.group(2), link, image)}'
            )
        else:
            body_html = inline(body, link, image)
        out.append(f"<li>{body_html}</li>")
    while stack:
        out.append(f"</{stack.pop()[1]}>")
        if stack:
            out.append("</li>")
    text = "".join(out)
    # a sublist's closing "</li>" was emitted after its parent's: tidy the doubled ones
    return text.replace("</li></li>", "</li>")


def to_html(text: str, link=_same, image=_same) -> str:
    """The HTML for a Markdown document. `link` and `image` rewrite each URL."""
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{_html.escape(lang)}"' if lang else ""
            code = _html.escape("\n".join(body), quote=False)
            out.append(f"<pre><code{cls}>{code}</code></pre>")
            continue
        if RAW_BLOCK.match(line):
            raw = line.strip()
            m = re.match(r"<summary>(.*)</summary>$", raw)
            out.append(f"<summary>{inline(m.group(1), link, image)}</summary>" if m else raw)
            i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        m = HEADING.match(line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            body = inline(title, link, image)
            out.append(f'<h{level} id="{anchor(body)}">{body}</h{level}>')
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and TABLE_RULE.match(lines[i + 1]):
            head = _cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c, link, image)}</th>" for c in head)
            body = "".join(
                "<tr>" + "".join(f"<td>{inline(c, link, image)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>")
            continue
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i][1:].lstrip())
                i += 1
            out.append(f"<blockquote>{to_html(chr(10).join(quote), link, image)}</blockquote>")
            continue
        if LIST_ITEM.match(line):
            items = []
            while (
                i < len(lines)
                and lines[i].strip()
                and (LIST_ITEM.match(lines[i]) or lines[i].startswith("  "))
            ):
                items.append(lines[i])
                i += 1
            out.append(_list(items, link, image))
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not (
            lines[i].startswith(("```", "#", ">", "|")) or LIST_ITEM.match(lines[i])
            or RAW_BLOCK.match(lines[i])
        ):  # fmt: skip
            para.append(lines[i].strip())
            i += 1
        if not para:  # a line that looked like a block but wasn't one: a paragraph of its own
            para = [lines[i].strip()]
            i += 1
        out.append(f"<p>{inline(chr(10).join(para), link, image)}</p>")
    return "\n".join(out) + "\n"
