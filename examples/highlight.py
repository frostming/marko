"""A markdown syntax highlighter built on marko's source mapping feature.

It parses a markdown document and renders the *source text* back as a
standalone HTML page where every element is colored according to its type,
using the ``source_span`` / ``syntax_spans`` / ``dest_span`` / ``title_span``
attributes provided by marko (see issue #273).

Usage::

    python examples/highlight.py input.md [output.html] [--gfm] [--title T]

Example::

    python examples/highlight.py examples/demo.md examples/demo.html --gfm
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from marko import Markdown
from marko import block as block_mod
from marko.element import Element

CSS = """\
:root {
  color-scheme: dark;
  --bg: #0d1117;
  --fg: #c9d1d9;
  --muted: #8b949e;
  --line-num: #3d444d;
  --syntax: #6e7681;
  --heading: #e6edf3;
  --heading-mark: #9da7b3;
  --link: #58a6ff;
  --link-dest: #7d8590;
  --link-title: #3fb950;
  --image-alt: #f778ba;
  --code-fg: #ffa657;
  --code-bg: #161b22;
  --code-chip: #21262d;
  --emphasis: #d2a8ff;
  --quote: #8b949e;
  --quote-border: #30363d;
  --html: #7ee787;
  --literal: #e3b341;
  --strike: #8b949e;
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #ffffff;
    --fg: #1f2328;
    --muted: #59636e;
    --line-num: #afb8c1;
    --syntax: #89929b;
    --heading: #1f2328;
    --heading-mark: #59636e;
    --link: #0969da;
    --link-dest: #59636e;
    --link-title: #1a7f37;
    --image-alt: #bf3989;
    --code-fg: #cf222e;
    --code-bg: #f6f8fa;
    --code-chip: #eff1f3;
    --emphasis: #8250df;
    --quote: #59636e;
    --quote-border: #d1d9e0;
    --html: #116329;
    --literal: #9a6700;
    --strike: #59636e;
  }
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--fg);
  margin: 0;
  padding: 2rem 1rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
}
main { max-width: 960px; margin: 0 auto; }
.page-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0 0 0.75rem;
  padding-left: 0.25rem;
}
.hl {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
    "Liberation Mono", monospace;
  font-size: 13.5px;
  line-height: 1.6;
  border: 1px solid var(--line-num);
  border-radius: 8px;
  padding: 0.6rem 0;
  overflow-x: auto;
}
.hl-line { white-space: pre; padding: 0 0.6rem; }
.hl-line:hover { background: color-mix(in srgb, var(--fg) 4%, transparent); }
.hl-ln {
  display: inline-block;
  width: 3.2em;
  margin-right: 1.2em;
  text-align: right;
  color: var(--line-num);
  user-select: none;
}

/* ---- generic ---- */
.tok-syntax { color: var(--syntax); }
.tok-dest { color: var(--link-dest); }
.tok-title { color: var(--link-title); }
.tok-link-ref-def { color: var(--muted); }

/* ---- headings ---- */
.tok-heading, .tok-setext-heading { color: var(--heading); font-weight: 700; }
.tok-heading { font-size: 1.25em; }
.tok-heading.tok-level-1 { font-size: 1.7em; }
.tok-heading.tok-level-2 { font-size: 1.5em; }
.tok-heading.tok-level-3 { font-size: 1.35em; }
.tok-heading.tok-level-4 { font-size: 1.25em; }
.tok-heading.tok-level-5, .tok-heading.tok-level-6 { font-size: 1.15em; }
.tok-setext-heading.tok-level-1 { font-size: 1.5em; }
.tok-setext-heading.tok-level-2 { font-size: 1.35em; }

/* ---- inline text ---- */
.tok-emphasis { font-style: italic; color: var(--emphasis); }
.tok-strong-emphasis { font-weight: 700; }
.tok-strong-emphasis .tok-emphasis { color: var(--emphasis); }
.tok-code-span {
  color: var(--code-fg);
  background: var(--code-chip);
  border-radius: 4px;
  padding: 0.05em 0.35em;
}
.tok-literal { color: var(--literal); }
.tok-strikethrough { color: var(--strike); text-decoration: line-through; }

/* ---- links & images ---- */
.tok-link { color: var(--link); }
.tok-link .tok-raw-text { color: var(--link); text-decoration: underline; }
.tok-auto-link { color: var(--link); text-decoration: underline; }
.tok-image .tok-raw-text { color: var(--image-alt); font-style: italic; }

/* ---- code blocks ---- */
.tok-fenced-code, .tok-code-block {
  background: var(--code-bg);
  color: var(--fg);
}

/* ---- quotes ---- */
.tok-quote, .tok-alert { color: var(--quote); }
.tok-quote .tok-raw-text, .tok-alert .tok-raw-text { color: var(--quote); }
.tok-quote, .tok-alert {
  border-left: 3px solid var(--quote-border);
  padding-left: 0.75em;
}

/* ---- misc blocks ---- */
.tok-thematic-break { color: var(--syntax); }
.tok-html-block, .tok-inline-html { color: var(--html); }
.tok-list-item .tok-syntax { color: var(--syntax); }

/* ---- legend ---- */
details.legend {
  margin-top: 1.25rem;
  font-size: 0.85rem;
  color: var(--muted);
}
details.legend summary { cursor: pointer; margin-bottom: 0.5rem; }
.legend-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.35rem 1rem; }
.legend-grid span { white-space: nowrap; }
.swatch { font-family: ui-monospace, Menlo, Consolas, monospace; margin-right: 0.4em; }
"""

#: (kind, css class) pairs shown in the page legend.
LEGEND = [
    ("# H1 heading", "tok-heading tok-level-1"),
    ("## H2 heading", "tok-heading tok-level-2"),
    ("Setext heading", "tok-setext-heading tok-level-1"),
    ("*emphasis*", "tok-emphasis"),
    ("**strong**", "tok-strong-emphasis"),
    ("~~strike~~", "tok-strikethrough"),
    ("`code span`", "tok-code-span"),
    ("``` code block", "tok-fenced-code"),
    ("[link](dest)", "tok-link"),
    ("dest / url", "tok-dest"),
    ('"title"', "tok-title"),
    ("![alt](img)", "tok-image"),
    ("<autolink>", "tok-auto-link"),
    (r"\escape", "tok-literal"),
    ("> quote", "tok-quote"),
    ("| table |", "tok-table"),
    ("<html>", "tok-html-block"),
    ("---- rule", "tok-thematic-break"),
    ("[ref]: url", "tok-link-ref-def"),
    ("` # * > | markers", "tok-syntax"),
]


class HtmlBuilder:
    """Collects HTML fragments, then splits them into lines at the end while
    keeping nested span tags balanced across line breaks."""

    _SPAN_RE = re.compile(r'<span class="([^"]*)">')

    def __init__(self) -> None:
        self.fragments: list[str] = []
        self.ends_with_newline = False

    def open(self, cls: str) -> None:
        self.fragments.append(f'<span class="{cls}">')

    def close(self) -> None:
        self.fragments.append("</span>")

    def emit_text(self, text: str) -> None:
        if text:
            self.fragments.append(html.escape(text))
            self.ends_with_newline = text.endswith("\n")

    def render(self) -> str:
        html_text = "".join(self.fragments)
        lines: list[str] = []
        stack: list[str] = []
        buf: list[str] = []
        i, n = 0, len(html_text)
        while i < n:
            ch = html_text[i]
            if ch == "<":
                m = re.match(r"<span[^>]*>|</span>", html_text[i:])
                assert m is not None
                token = m.group(0)
                i += len(token)
                if token == "</span>":
                    stack.pop()
                    buf.append(token)
                else:
                    buf.append(token)
                    stack.append(self._SPAN_RE.match(token).group(1))  # type: ignore[union-attr]
            else:
                j = i
                while j < n and html_text[j] not in "<\n":
                    j += 1
                if j > i:
                    buf.append(html_text[i:j])
                if j < n and html_text[j] == "\n":
                    # one newline ends the current line: close every open tag
                    # and reopen them on the next line so colors continue.
                    buf.extend("</span>" for _ in reversed(stack))
                    lines.append("".join(buf))
                    buf = [f'<span class="{cls}">' for cls in stack]
                    i = j + 1
                    continue
                i = j
        if buf:
            lines.append("".join(buf))
        if self.ends_with_newline and lines:
            # the final newline does not open a new line
            lines.pop()
        return "\n".join(
            f'<div class="hl-line"><span class="hl-ln">{i}</span>{frags}</div>'
            for i, frags in enumerate(lines, 1)
        )


def tok_class(el: Element) -> str:
    name = el.get_type(snake_case=True)
    cls = "tok-" + name.replace("_", "-")
    level = getattr(el, "level", None)
    if name in ("heading", "setext_heading") and isinstance(level, int):
        cls += f" tok-level-{level}"
    return cls


def element_children(el: Element) -> list[Element]:
    children = getattr(el, "children", None)
    if isinstance(children, list):
        return [c for c in children if isinstance(c, Element)]
    return []


def _fence_spans(el: Element, text: str, s: int, e: int) -> list[tuple[int, int]]:
    """Return the spans of the opening/closing fences of a fenced code block."""
    lines = text[s:e].splitlines(keepends=True)
    if not lines:
        return []
    spans = [(s, s + len(lines[0]))]
    last = lines[-1]
    if re.match(r" {,3}(?:`+|~+)[^\n\S]*$", last.rstrip("\n")):
        spans.append((e - len(last), e))
    return spans


def render_element(el: Element, text: str, b: HtmlBuilder) -> None:
    span = el.source_span
    if span is None:
        for child in element_children(el):
            render_element(child, text, b)
        return
    s, e = span
    if e <= s:
        return

    b.open(tok_class(el))

    # Special sub-spans that should override the element's own color.
    special: list[tuple[int, int, str]] = []
    for attr, cls in (("dest_span", "tok-dest"), ("title_span", "tok-title")):
        sp = getattr(el, attr, None)
        if sp is not None:
            special.append((sp[0], sp[1], cls))
    if isinstance(el, block_mod.FencedCode):
        special.extend((a, c, "tok-syntax") for a, c in _fence_spans(el, text, s, e))

    children = element_children(el)
    child_spans = [c.source_span for c in children if c.source_span is not None]

    if not child_spans and el.syntax_spans:
        # Elements without element children (e.g. code span, literal escape):
        # emit the explicit syntax parts and leave the rest to the element color.
        pos = s
        for a, c in sorted(el.syntax_spans):
            if pos < a:
                b.emit_text(text[pos:a])
            b.open("tok-syntax")
            b.emit_text(text[a:c])
            b.close()
            pos = max(pos, c)
        if pos < e:
            b.emit_text(text[pos:e])
        b.close()
        return

    # Cut the element's span at every child/special boundary, then render each
    # interval: a child recurses, a special span gets its own class, and any
    # leftover region (markers like `#`, `>`, `|`, interleaved prefixes) is
    # treated as syntax.
    cuts = sorted(
        {s, e}
        | {a for a, _ in child_spans}
        | {c for _, c in child_spans}
        | {a for a, _, _ in special}
        | {c for _, c, _ in special}
    )
    for a, c in zip(cuts, cuts[1:]):
        if a >= c:
            continue
        matching_child = next(
            (ch for ch, (cs, ce) in zip(children, child_spans) if cs <= a and ce >= c),
            None,
        )
        if matching_child is not None:
            render_element(matching_child, text, b)
            continue
        spcls = next((k for x, y, k in special if x <= a and y >= c), None)
        if spcls is not None:
            b.open(spcls)
            b.emit_text(text[a:c])
            b.close()
        elif child_spans:
            # A leftover region inside an element with children (e.g. the
            # markers of a heading, a quote prefix, table pipes) is syntax.
            b.open("tok-syntax")
            b.emit_text(text[a:c])
            b.close()
        else:
            # A leaf element: the remaining text keeps the element's color.
            b.emit_text(text[a:c])
    b.close()


def highlight(text: str, gfm: bool = False) -> str:
    md = Markdown(extensions=["gfm"]) if gfm else Markdown()
    doc = md.parse(text)
    b = HtmlBuilder()
    render_element(doc, text, b)
    return b.render()


def render_page(title: str, body: str) -> str:
    legend = "".join(
        f'<span><span class="swatch {cls}">{label}</span></span>'
        for label, cls in LEGEND
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
{CSS}
</style>
</head>
<body>
<main>
<h1 class="page-title">{html.escape(title)}</h1>
<div class="hl">
{body}
</div>
<details class="legend">
<summary>Legend</summary>
<div class="legend-grid">{legend}</div>
</details>
</main>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a markdown document as highlighted HTML source."
    )
    parser.add_argument("input", type=Path, help="input markdown file")
    parser.add_argument("output", type=Path, nargs="?", help="output html file")
    parser.add_argument("--gfm", action="store_true", help="enable GFM extensions")
    parser.add_argument("--title", help="page title (defaults to the input filename)")
    args = parser.parse_args(argv)

    text = args.input.read_text(encoding="utf-8")
    title = args.title or args.input.name
    body = highlight(text, gfm=args.gfm)
    page = render_page(title, body)

    if args.output:
        args.output.write_text(page, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
