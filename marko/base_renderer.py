#! -*- coding: utf-8 -*-
"""
Base renderer class
"""
import itertools

from . import block, inline
from ._compat import string_types
from .helpers import camel_to_snake_case, scan_inline


class BaseRenderer(object):
    """The base class of renderers.

    A custom renderer should subclass this class and include your own render functions.

    A render function should:

    * be named as ``render_<element_name>``, where the ``element_name`` is the snake
      case form of the element class name, the renderer will search the corresponding
      function in this way.
    * accept the element instance and return any output you want.

    If no corresponding render function is found, renderer will fallback to call
    :meth:`BaseRenderer.render_children`.

    All elements defined in CommonMark's spec are included in the base renderer
    by default. To add your custom elements, you can either:

    1. pass the element classes as ``extras`` arguments to the constructor.
    2. or call :meth:`BaseRenderer.add_element` by yourself inside the ``__init__``
       method body, especially when you want to override the default element.

    Suppose you have a custom renderer called ``MyRenderer``, to use it::

        renderer = MyRenderer()
        renderer.markdown(text)

    Attributes:
        block_elements(dict): a dict of name: block_element pairs
        inlin_elements(dict): a dict of name: inlin_element pairs

    :param \*extras: extra elements to be included in parsing process.
    """

    def __init__(self, *extras):
        self.root_node = None
        self.block_elements = {}
        self.inline_elements = {}
        # Create references in block and inline modules to avoid cyclic import.
        block._renderer = self
        inline._renderer = self

        for element in itertools.chain(
            (getattr(block, name) for name in block.__all__),
            (getattr(inline, name) for name in inline.__all__),
            extras
        ):
            self.add_element(element)

    def add_element(self, element, override=False):
        """Add an element to the parser.

        :param element: the element class.
        :param override: whether to replace the default element based on.

        .. note:: If one needs to call it inside ``__init__()``, please call it after
             ``super().__init__()`` is called.
        """
        if issubclass(element, inline.InlineElement):
            dest = self.inline_elements
        elif issubclass(element, block.BlockElement):
            dest = self.block_elements
        else:
            raise TypeError(
                'The element should be a subclass of either `BlockElement` or '
                '`InlineElement`.'
            )
        if not override:
            dest[element.__name__] = element
        else:
            for cls in element.__bases__:
                if cls in dest.values():
                    dest[cls.__name__] = element
                    break
            else:
                dest[element.__name__] = element

    def markdown(self, text):
        """Parse and render the givin markdown text."""
        self.root_node = self.block_elements['Document'](text)
        return self.render(self.root_node)

    def parse(self, source_or_text):
        """Do the actual parsing and returns an AST or parsed element.

        :param source_or_text: the text or source object.
            Based on the type, it will do following:
            - text: returns the parsed Document element.
            - source: parse the source and returns the parsed children as a list.
        """
        element_list = self._get_element_list(self.block_elements)
        if isinstance(source_or_text, string_types):
            return self.block_elements['Document'](source_or_text)
        ast = []
        while not source_or_text.exhausted:
            for name, ele_type in element_list:
                if ele_type.match(source_or_text):
                    result = ele_type.parse(source_or_text)
                    if not hasattr(result, 'priority'):
                        result = ele_type(result)
                    ast.append(result)
                    break
            else:
                # Quit the current parsing and go back to the last level.
                break
        return ast

    def parse_inline(self, text):
        """Parses text into inline elements.
        RawText is not considered in parsing but created as a wrapper of holes
        that don't match any other elements.

        :param text: the text to be parsed.
        :returns: a list of inline elements.
        """
        element_list = self._get_element_list(self.inline_elements)
        ast = []
        for element in scan_inline(text, element_list):
            if isinstance(element, string_types):
                ast.append(inline.RawText(element))
            else:
                ast.append(element)
        return ast

    def render(self, element):
        """Renders the given element to string.

        :param element: a element to be rendered.
        :returns: the output string or any values.
        """
        # Store the root node to provide some context to render functions
        if not self.root_node:
            self.root_node = element
        render_func = getattr(
            self, self._cls_to_func_name(element.__class__), None)
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

    def _cls_to_func_name(self, klass):
        element_types = itertools.chain(
            self.block_elements.items(),
            self.inline_elements.items()
        )
        for name, cls in element_types:
            if cls is klass:
                return 'render_' + camel_to_snake_case(name)

    @staticmethod
    def _get_element_list(elements):
        return sorted(elements.items(), key=lambda e: e[1].priority, reverse=True)
