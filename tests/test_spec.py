from tests import SpecTestSuite
from marko import Markdown
from marko.ext.gfm import gfm


class TestCommonMark(SpecTestSuite):
    @classmethod
    def setup_class(cls):
        cls.markdown = Markdown()

    def test_greedy_consume_prefix(self):
        md = "> 1. Item 1\n>    ```code\n>       indented code\n>    ```"
        html = (
            '<blockquote><ol><li>Item 1<pre><code class="language-code">'
            "   indented code\n</code></pre></li></ol></blockquote>"
        )
        self.assert_case(md, html)


TestCommonMark.load_spec("commonmark")

GFM_IGNORE = ["autolinks_015", "autolinks_018", "autolinks_019"]


class TestGFM(SpecTestSuite):
    @classmethod
    def setup_class(cls):
        cls.markdown = gfm

    @classmethod
    def ignore_case(cls, n):
        return n in GFM_IGNORE

    def test_parse_table_with_backslashes(self):
        md = "\\\n\n| \\ |\n| - |\n| \\ |"
        html = "<p>\\</p><table><thead><tr><th>\\</th></tr></thead><tbody><tr><td>\\</td></tr></tbody></table>"
        self.assert_case(md, html)


TestGFM.load_spec("gfm")
