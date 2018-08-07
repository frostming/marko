#! -*- coding: utf-8 -*-
"""
Base renderer class
"""
import inspect
from ._compat import camel_to_snake_case


class BaseRenderer(object):
    """The base class of renderers.

    A custom renderer should subclass this class and add your own render functions.

    A render function should:

    * be named as ``render_<element_name>``, where the ``element_name`` is the snake
      case form of the element class name, the renderer will search the corresponding
      function in this way.
    * accept the element instance and return any output you want.

    If no corresponding render function is found, renderer will fallback to call
    :meth:`render_children`_.

    All elements defined in commonmark's spec are included in the base renderer
    by default. To add your custom elements, you can either:

    1. pass the element class to constructor.
    2. or call :func:`add_element` by yourself in the ``__init__`` method, especially
       if you want to override the default element.

    Usage::

        renderer = MyRenderer()
        with renderer() as renderer:
            renderer.render(Document(Source(text)))
    """

    def __init__(self, *extras):
        self.root_node = None

        for element_type in extras:
            inspect.getmodule(element_type.__bases__[0]).add_element(element_type)

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
            self, 'render_' + camel_to_snake_case(element.__class__.__name__), None)
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
