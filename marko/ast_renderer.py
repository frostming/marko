"""
AST renderers for inspecting the markdown parsing result.
"""
import json
from .base_renderer import BaseRenderer
from ._compat import string_types
from .helpers import camel_to_snake_case


class ASTRenderer(BaseRenderer):
    """Render as AST structure.

    Example::

        >>> print(markdown('# heading', ASTRenderer))
        {'footnotes': [],
         'link_ref_defs': {},
         'children': [{'level': 1, 'children': ['heading'], 'element': 'heading'}],
         'element': 'document'}
    """

    def render_children(self, element):
        if isinstance(element, list):
            return [self.render_children(e) for e in element]
        if isinstance(element, string_types):
            return element
        rv = {k: v for k, v in element.__dict__.items() if not k.startswith('_')}
        if 'children' in rv:
            rv['children'] = self.render(rv['children'])
        rv['element'] = camel_to_snake_case(element.__class__.__name__)
        return rv


class XMLRenderer(BaseRenderer):
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

    def markdown(self, text):
        self.indent = 0
        return super(XMLRenderer, self).markdown(text)

    def render_children(self, element):
        if isinstance(element, string_types):
            return ' ' * self.indent + json.dumps(element)[1:-1]
        lines = []
        if element is self.root_node:
            lines.append(' ' * self.indent + '<?xml version="1.0" encoding="UTF-8"?>')
            lines.append(
                ' ' * self.indent + '<!DOCTYPE document SYSTEM "CommonMark.dtd">'
            )
        attrs = {
            k: v
            for k, v in element.__dict__.items()
            if not k.startswith('_') and k != 'children'
        }
        attr_str = ''.join(' {}="{}"'.format(k, v) for k, v in attrs.items())
        element_name = camel_to_snake_case(element.__class__.__name__)
        lines.append(' ' * self.indent + '<{}{}>'.format(element_name, attr_str))
        if getattr(element, 'children', None):
            self.indent += 2
            lines.extend(self.render(child) for child in element.children)
            self.indent -= 2
            lines.append(' ' * self.indent + '</{}>'.format(element_name))
        else:
            lines[-1] = lines[-1][:-1] + ' />'
        return '\n'.join(lines)
