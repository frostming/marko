#! -*- coding: utf-8 -*-
"""
Base renderer class
"""
from __future__ import unicode_literals
import itertools

from .helpers import camel_to_snake_case


class Renderer(object):
    """The base class of renderers.

    A custom renderer should subclass this class and include your own render functions.

    A render function should:

    * be named as ``render_<element_name>``, where the ``element_name`` is the snake
      case form of the element class name, the renderer will search the corresponding
      function in this way.
    * accept the element instance and return any output you want.

    If no corresponding render function is found, renderer will fallback to call
    :meth:`Renderer.render_children`.
    """

    def __init__(self):
        self.root_node = None

    def __enter__(self):
        """Provide a context so that root_node can be reset after render."""
        return self

    def __exit__(self, *args):
        pass

    def render(self, element):
        """Renders the given element to string.

        :param element: a element to be rendered.
        :returns: the output string or any values.
        """
        # Store the root node to provide some context to render functions
        if not self.root_node:
            self.root_node = element
        render_func = getattr(self, self._cls_to_func_name(element.__class__), None)
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
        return "".join(rendered)

    def _cls_to_func_name(self, klass):
        from .block import parser

        element_types = itertools.chain(
            parser.block_elements.items(), parser.inline_elements.items()
        )
        for name, cls in element_types:
            if cls is klass:
                return "render_" + camel_to_snake_case(name)

        return "render_children"
