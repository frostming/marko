from marko import Markdown
from tests import SpecTestSuite


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

    def test_parse_nbsp_no_crash(self):
        md = "- \xa0A"
        html = "<ul>\n<li>A</li>\n</ul>"
        self.assert_case(md, html)

    def test_line_break_in_link_text(self):
        md = "![foo\nbar\nbaz](/image.png)"
        html = '<p><img src="/image.png" alt="foo\nbar\nbaz" /></p>'
        self.assert_case(md, html)


TestCommonMark.load_spec("commonmark")

GFM_IGNORE = ["autolinks_015", "autolinks_018", "autolinks_019"]


class TestGFM(SpecTestSuite):
    @classmethod
    def setup_class(cls):
        cls.markdown = Markdown(extensions=["gfm"])

    @classmethod
    def ignore_case(cls, n):
        return n in GFM_IGNORE

    def test_parse_table_with_backslashes(self):
        md = "\\\n\n| \\ |\n| - |\n| \\ |"
        html = "<p>\\</p><table><thead><tr><th>\\</th></tr></thead><tbody><tr><td>\\</td></tr></tbody></table>"
        self.assert_case(md, html)

    def test_strikethrough_link(self):
        md = "~~[google](https://google.com)~~"
        html = '<p><del><a href="https://google.com">google</a></del></p>'
        self.assert_case(md, html)

    def test_strikethrough_inside_link(self):
        md = "[~~google~~](https://google.com)"
        html = '<p><a href="https://google.com"><del>google</del></a></p>'
        self.assert_case(md, html)

    def test_strikethrough_single_tilde(self):
        md = "hello ~google~"
        html = "<p>hello <del>google</del></p>"
        self.assert_case(md, html)

    def test_strikethrough_spec_wont_strike(self):
        content = "This will ~~~not~~~ strike."
        expected = "<p>This will ~~~not~~~ strike.</p>"
        assert self.markdown(content).strip() == expected

    def test_gfm_autolink(self):
        content = "地址：https://google.com"
        assert (
            self.markdown(content).strip()
            == '<p>地址：<a href="https://google.com">https://google.com</a></p>'
        )
        content = "地址：www.baidu.com"
        assert (
            self.markdown(content).strip()
            == '<p>地址：<a href="http://www.baidu.com">www.baidu.com</a></p>'
        )


TestGFM.load_spec("gfm")
