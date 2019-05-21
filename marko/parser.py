"""
Base parser
"""
import itertools
from . import block, inline, inline_parser
from .helpers import string_types


class Parser(object):
    """
    All elements defined in CommonMark's spec are included in the parser
    by default. To add your custom elements, you can either:

    1. pass the element classes as ``extras`` arguments to the constructor.
    2. or subclass to your own parser and call :meth:`Parser.add_element`
       inside the ``__init__`` body, especially when you want to override
       the default element.

    Attributes:
        block_elements(dict): a dict of name: block_element pairs
        inlin_elements(dict): a dict of name: inlin_element pairs

    :param \*extras: extra elements to be included in parsing process.
    """

    def __init__(self, *extras):
        self.block_elements = {}
        self.inline_elements = {}
        # Create references in block and inline modules to avoid cyclic import.

        for element in itertools.chain(
            (getattr(block, name) for name in block.__all__),
            (getattr(inline, name) for name in inline.__all__),
            extras,
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
                "The element should be a subclass of either `BlockElement` or "
                "`InlineElement`."
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

    def parse(self, source_or_text):
        """Do the actual parsing and returns an AST or parsed element.

        :param source_or_text: the text or source object.
            Based on the type, it will do following:
            - text: returns the parsed Document element.
            - source: parse the source and returns the parsed children as a list.
        """
        if isinstance(source_or_text, string_types):
            block.parser = self
            inline.parser = self
            return self.block_elements["Document"](source_or_text)
        element_list = self._build_block_element_list()
        ast = []
        while not source_or_text.exhausted:
            for ele_type in element_list:
                if ele_type.match(source_or_text):
                    result = ele_type.parse(source_or_text)
                    if not hasattr(result, "priority"):
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
        element_list = self._build_inline_element_list()
        return inline_parser.parse(
            text, element_list, fallback=self.inline_elements["RawText"]
        )

    def _build_block_element_list(self):
        """Return a list of block elements, ordered from highest priority to lowest.
        """
        return sorted(
            [e for e in self.block_elements.values() if not e.virtual],
            key=lambda e: e.priority,
            reverse=True,
        )

    def _build_inline_element_list(self):
        """Return a list of elements, each item is a list of elements
        with the same priority.
        """
        return [e for e in self.inline_elements.values() if not e.virtual]
