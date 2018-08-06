#! -*- coding: utf-8 -*-
"""
Base renderer class
"""
from ._compat import camel_to_snake_case


class BaseRenderer(object):
    def __init__(self):
        self.root_node = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.root_node = None

    def render(self, element):
        """Renders the given element to string.

        :param element: a element to be rendered"""
        # Store the root node to provide some context to render functions
        if not self.root_node:
            self.root_node = element
        render_func = getattr(
            self, camel_to_snake_case(element.__class__.__name__), None)
        if not render_func:
            render_func = self.render_children
        return render_func(element)

    def render_children(self, element):
        """
        Recursively renders child elements. Joins the rendered
        strings with no space in between.

        If newlines / spaces are needed between elements, add them
        in their respective templates, or override this function
        in the renderer subclass, so that whitespace won't seem to
        appear magically for anyone reading your program.

        :param element: a branch node who has children attribute.
        """
        rendered = [self.render(child) for child in element.children]
        return ''.join(rendered)
