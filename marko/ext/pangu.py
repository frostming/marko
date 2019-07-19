# -*- coding: utf-8 -*-
"""
Pangu Extension
~~~~~~~~~~~~~~~

Separate CJK characters with latin letters.

Reference: `vinta's pangu project <https://github.com/vinta/pangu.js>`_

Example::

    input: 中国有13亿人口
    output: 中国有<span class="pangu"></span>13<span class="pangu"></span>亿人口

    from marko import Markdown

    markdown = Markdown(extensions=[PanguExtension])
    print(markdown(text))
"""
from __future__ import unicode_literals
import re

CJK_RE = (
    r"\u2e80-\u2eff\u2f00-\u2fdf\u3040-\u309f\u30a0-\u30ff\u3100-\u312f"
    r"\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
)
LATIN_RE = r"a-zA-Z0-9"
PANGU_RE = re.compile(
    r"((?<=[{cjk}])(?=[{latin}])|(?<=[{latin}])(?=[{cjk}]))".format(
        cjk=CJK_RE, latin=LATIN_RE
    )
)


class PanguRendererMixin(object):
    def render_raw_text(self, element):
        rv = super(PanguRendererMixin, self).render_raw_text(element)
        return PANGU_RE.sub('<span class="pangu"></span>', rv)


class PanguExtension:
    renderer_mixins = [PanguRendererMixin]
