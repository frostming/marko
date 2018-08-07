"""
AST renderer
"""
from .base_renderer import BaseRenderer
from ._compat import string_types, camel_to_snake_case


class ASTRenderer(BaseRenderer):
    """Render as AST json representation"""
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
