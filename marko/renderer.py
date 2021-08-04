"""
Base renderer class
"""
import html
import itertools
import re

from .helpers import camel_to_snake_case, is_type_check

if is_type_check():
    from typing import Any, Union
    from .inline import InlineElement
    from .block import BlockElement
    from .parser import ElementType

    Element = Union[BlockElement, InlineElement]


class Renderer:
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

    #: Whether to delegate rendering to specific render functions
    delegate: bool = True

    _charref = re.compile(
        r"&(#[0-9]{1,7};" r"|#[xX][0-9a-fA-F]{1,6};" r"|[^\t\n\f <&#;]{1,32};)"
    )

    def __init__(self):  # type: () -> None
        self.root_node = None

    def __enter__(self):  # type: () -> Renderer
        """Provide a context so that root_node can be reset after render."""
        self._charref_bak = html._charref
        html._charref = self._charref
        return self

    def __exit__(self, *args):  # type: (Any) -> None
        html._charref = self._charref_bak

    def render(self, element):  # type: (Element) -> str
        """Renders the given element to string.

        :param element: a element to be rendered.
        :returns: the output string or any values.
        """
        # Store the root node to provide some context to render functions
        if not self.root_node:
            self.root_node = element  # type: ignore
        render_func = getattr(self, self._cls_to_func_name(element.__class__), None)
        if render_func is not None and (
            getattr(render_func, "_force_delegate", False) or self.delegate
        ):
            return render_func(element)
        return self.render_children(element)

    def render_children(self, element):  # type: (Element) -> str
        """
        Recursively renders child elements. Joins the rendered
        strings with no space in between.

        If newlines / spaces are needed between elements, add them
        in their respective templates, or override this function
        in the renderer subclass, so that whitespace won't seem to
        appear magically for anyone reading your program.

        :param element: a branch node who has children attribute.
        """
        rendered = [self.render(child) for child in element.children]  # type: ignore
        return "".join(rendered)

    def _cls_to_func_name(self, klass):  # type: (ElementType) -> str
        from .block import parser

        element_types = itertools.chain(
            parser.block_elements.items(),  # type: ignore
            parser.inline_elements.items(),  # type: ignore
        )
        for name, cls in element_types:
            if cls is klass:
                return "render_" + camel_to_snake_case(name)

        return "render_children"


def force_delegate(func):
    """
    A decorator to allow delegation for the specified method even if cls.delegate = False
    """
    func._force_delegate = True
    return func
