from __future__ import annotations

import itertools
import re
from pathlib import Path
from typing import Generator

import pytest

from marko import Markdown
from tests.normalize import normalize_html

SPEC_DIR = Path(__file__).with_name("spec")
EXAMPLE_PATTERN = re.compile(
    r"^`{32} example\b.*?\n([\s\S]*?)^\.\n([\s\S]*?)^`{32}$|^#{1,6} *(.*)$",
    flags=re.MULTILINE,
)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "markdown" in metafunc.fixturenames:
        cases = itertools.chain(parse_examples("commonmark"), COMMON_CASES, CMARK_CASES)
        metafunc.parametrize(
            "text,html", [pytest.param(case[1], case[2], id=case[0]) for case in cases]
        )
    elif "gfm" in metafunc.fixturenames:
        cases = itertools.chain(
            filter(lambda case: case[0] not in GFM_IGNORE, parse_examples("gfm")),
            COMMON_CASES,
            GFM_CASES,
        )
        metafunc.parametrize(
            "text,html", [pytest.param(case[1], case[2], id=case[0]) for case in cases]
        )


def parse_examples(spec: str) -> Generator[tuple[str, str, str], None, None]:
    with SPEC_DIR.joinpath(f"{spec}.txt").open(encoding="utf8") as f:
        text = f.read()
    data = EXAMPLE_PATTERN.findall(text)

    section = None
    count = 0
    for md, html, title in data:
        if title:
            count = 0
            section = title.lower().split("(")[0].replace(" ", "_")

        if md and html:
            count += 1
            name = "%s_%03d" % (section, count)
            md = md.replace("→", "\t")
            html = html.replace("→", "\t")
            yield name, md, html


@pytest.fixture
def markdown() -> Markdown:
    return Markdown()


@pytest.fixture
def gfm() -> Markdown:
    return Markdown(extensions=["gfm"])


COMMON_CASES = [
    (
        "mixed_tab_space_in_list_item",
        "* foo\n\t* foo.bar",
        "<ul><li>foo<ul><li>foo.bar</li></ul></li></ul>",
    )
]

CMARK_CASES = [
    (
        "greedy_consume_prefix",
        "> 1. Item 1\n>    ```code\n>       indented code\n>    ```",
        '<blockquote><ol><li>Item 1<pre><code class="language-code">'
        "   indented code\n</code></pre></li></ol></blockquote>",
    ),
    ("parse_nbsp_no_crash", "- \xa0A", "<ul>\n<li>A</li>\n</ul>"),
    (
        "line_break_in_link_text",
        "![foo\nbar\nbaz](/image.png)",
        '<p><img src="/image.png" alt="foo\nbar\nbaz" /></p>',
    ),
]


GFM_IGNORE = [
    "autolinks_015",
    "autolinks_018",
    "autolinks_019",
    # Strong emphasis don't need to be flattened
    "emphasis_and_strong_emphasis_039",
    "emphasis_and_strong_emphasis_067",
    "emphasis_and_strong_emphasis_075",
    "emphasis_and_strong_emphasis_076",
    "emphasis_and_strong_emphasis_077",
    "emphasis_and_strong_emphasis_114",
    "emphasis_and_strong_emphasis_115",
    "emphasis_and_strong_emphasis_116",
    "emphasis_and_strong_emphasis_118",
]

GFM_CASES = [
    (
        "parse_table_with_backslashes",
        "\\\n\n| \\ |\n| - |\n| \\ |",
        "<p>\\</p><table><thead><tr><th>\\</th></tr></thead><tbody><tr><td>\\</td></tr></tbody></table>",
    ),
    (
        "strikethrough_link",
        "~~[google](https://google.com)~~",
        '<p><del><a href="https://google.com">google</a></del></p>',
    ),
    (
        "strikethrough_inside_link",
        "[~~google~~](https://google.com)",
        '<p><a href="https://google.com"><del>google</del></a></p>',
    ),
    ("strikethrough_single_tilde", "hello ~google~", "<p>hello <del>google</del></p>"),
    (
        "strikethrough_spec_wont_strike",
        "This will ~~~not~~~ strike.",
        "<p>This will ~~~not~~~ strike.</p>",
    ),
    (
        "gfm_autolink",
        "地址：https://google.com",
        '<p>地址：<a href="https://google.com">https://google.com</a></p>',
    ),
    (
        "gfm_autolink_no_scheme",
        "地址：www.baidu.com",
        '<p>地址：<a href="http://www.baidu.com">www.baidu.com</a></p>',
    ),
]


def test_cmark_spec(markdown: Markdown, text: str, html: str) -> None:
    result = markdown(text)
    assert normalize_html(result) == normalize_html(html), repr(result)


def test_gfm_spec(gfm: Markdown, text: str, html: str) -> None:
    result = gfm(text)
    assert normalize_html(result) == normalize_html(html), repr(result)
