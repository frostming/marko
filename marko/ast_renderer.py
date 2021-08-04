"""
AST renderers for inspecting the markdown parsing result.
"""
import json
import html
from marko.html_renderer import HTMLRenderer

from .renderer import Renderer, force_delegate
from .helpers import camel_to_snake_case


class ASTRenderer(Renderer):
    """Render as AST structure.

    Example::

        >>> print(markdown('# heading', ASTRenderer))
        {'footnotes': [],
         'link_ref_defs': {},
         'children': [{'level': 1, 'children': ['heading'], 'element': 'heading'}],
         'element': 'document'}
    """

    delegate = False

    @force_delegate
    def render_raw_text(self, element):
        return {
            "element": "raw_text",
            "children": html.unescape(element.children)
            if element.escape
            else element.children,
            "escape": element.escape,
        }

    def render_children(self, element):
        if isinstance(element, list):
            return [self.render(e) for e in element]
        if isinstance(element, str):
            return element
        rv = {k: v for k, v in element.__dict__.items() if not k.startswith("_")}
        if "children" in rv:
            rv["children"] = self.render(rv["children"])
        rv["element"] = camel_to_snake_case(element.__class__.__name__)
        return rv


class XMLRenderer(Renderer):
    """Render as XML format AST.

    It will render the parsed result and XML string and you can print it or
    write it to a file.

    Example::

        >>> print(markdown('# heading', XMLRenderer))
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE document SYSTEM "CommonMark.dtd">
        <document footnotes="[]" link_ref_defs="{}">
        <heading level="1">
            heading
        </heading>
        </document>
    """

    delegate = False

    def __enter__(self):
        self.indent = 0
        return super().__enter__()

    def __exit__(self, *args):
        self.indent = 0
        return super().__exit__(*args)

    def render_children(self, element):
        lines = []
        if element is self.root_node:
            lines.append(" " * self.indent + '<?xml version="1.0" encoding="UTF-8"?>')
            lines.append(
                " " * self.indent + '<!DOCTYPE document SYSTEM "CommonMark.dtd">'
            )
        attrs = {
            k: v
            for k, v in element.__dict__.items()
            if not k.startswith("_") and k != "children"
        }
        attr_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
        element_name = camel_to_snake_case(element.__class__.__name__)
        lines.append(" " * self.indent + f"<{element_name}{attr_str}>")
        if getattr(element, "children", None):
            self.indent += 2
            if isinstance(element.children, str):
                lines.append(
                    " " * self.indent
                    + HTMLRenderer.escape_html(json.dumps(element.children)[1:-1])
                )
            else:
                lines.extend(self.render(child) for child in element.children)
            self.indent -= 2
            lines.append(" " * self.indent + f"</{element_name}>")
        else:
            lines[-1] = lines[-1][:-1] + " />"
        return "\n".join(lines)
