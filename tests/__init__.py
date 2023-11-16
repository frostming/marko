# -*- coding: utf-8 -*-
import codecs
import os
import re

from tests.normalize import normalize_html

TEST_ROOT = os.path.dirname(__file__)
EXAMPLE_PATTERN = re.compile(
    r"^`{32} example\b.*?\n([\s\S]*?)^\.\n([\s\S]*?)^`{32}$|^#{1,6} *(.*)$",
    flags=re.M,
)


def parse_examples(text):
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


class SpecTestSuite:
    @classmethod
    def load_spec(cls, spec_name):
        def attach_case(n, md, html):
            def method(self):
                self.assert_case(md, html)

            name = "test_{}".format(n)
            method.__name__ = name
            method.__doc__ = "Run spec {} - {}".format(spec_name, n)
            setattr(cls, name, method)

        spec_file = os.path.join(TEST_ROOT, "spec/{}.txt".format(spec_name))
        with codecs.open(spec_file, encoding="utf-8") as f:
            for name, md, html in parse_examples(f.read()):
                if not cls.ignore_case(name):
                    attach_case(name, md, html)

    @classmethod
    def ignore_case(cls, n):
        return False

    def assert_case(self, text, html):
        result = self.markdown(text)
        assert normalize_html(result) == normalize_html(html), repr(result)

    # Extra cases that are not included
    def test_mixed_tab_space_in_list_item(self):
        text = "* foo\n\t* foo.bar"
        html = "<ul><li>foo<ul><li>foo.bar</li></ul></li></ul>"
        self.assert_case(text, html)
