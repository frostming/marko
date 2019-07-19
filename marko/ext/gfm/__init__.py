"""
Github flavored markdown
~~~~~~~~~~~~~~~~~~~~~~~~

https://github.github.com/gfm

Unlike other extensions, GFM provides a self-contained subclass of ``Markdown``
with parser and renderer already set.
User may also use the parser and renderer as bases for further extension.

Example usage::

    from marko.ext.gfm import gfm
    print(gfm(text))

"""
from __future__ import unicode_literals
import re
from marko import Markdown
from . import elements


class GFMParserMixin(object):
    def __init__(self, *extras):
        super(GFMParserMixin, self).__init__(*extras)

        self.add_element(elements.Paragraph, True)
        self.add_element(elements.ListItem, True)
        self.add_element(elements.Strikethrough)
        self.add_element(elements.Url)
        self.add_element(elements.Table)
        self.add_element(elements.TableRow)
        self.add_element(elements.TableCell)


class GFMRendererMixin(object):
    tagfilter = re.compile(
        r"<(title|texarea|style|xmp|iframe|noembed|noframes|script|plaintext)",
        flags=re.I,
    )
    tagfilter_no_open = re.compile(
        r"(?<!^)( *)<(title|texarea|style|xmp|iframe|noembed|noframes|script|plaintext)",
        flags=re.I,
    )

    def render_paragraph(self, element):
        children = self.render_children(element)
        template = '<input{} disabled="" type="checkbox">{}'
        if hasattr(element, "checked"):
            children = template.format(
                ' checked=""' if element.checked else "", children
            )
        if element._tight:
            return children
        else:
            return "<p>{}</p>\n".format(children)

    def render_strikethrough(self, element):
        return "<del>{}</del>".format(self.render_children(element))

    def render_inline_html(self, element):
        return self.tagfilter.sub(r"&lt;\1", element.children)

    def render_html_block(self, element):
        return self.tagfilter_no_open.sub(r"\1&lt;\2", element.children)

    def render_table(self, element):
        header, body = element.children[0], element.children[1:]
        theader = "<thead>\n{}</thead>".format(self.render(header))
        tbody = ""
        if body:
            tbody = "\n<tbody>\n{}</tbody>".format(
                "".join(self.render(row) for row in body)
            )
        return "<table>\n{}{}</table>".format(theader, tbody)

    def render_table_row(self, element):
        return "<tr>\n{}</tr>\n".format(self.render_children(element))

    def render_table_cell(self, element):
        tag = "th" if element.header else "td"
        align = ""
        if element.align:
            align = ' align="{}"'.format(element.align)
        return "<{tag}{align}>{children}</{tag}>\n".format(
            tag=tag, children=self.render_children(element), align=align
        )

    def render_url(self, element):
        return self.render_link(element)


class GFMExtension:
    parser_mixins = [GFMParserMixin]
    renderer_mixins = [GFMRendererMixin]


gfm = Markdown()
gfm.use(GFMExtension)
