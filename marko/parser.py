"""
Base parser
"""
import itertools
from .helpers import is_type_check, Source


class Parser:
    r"""
    All elements defined in CommonMark's spec are included in the parser
    by default.

    Attributes:
        block_elements(dict): a dict of name: block_element pairs
        inline_elements(dict): a dict of name: inline_element pairs

    :param \*extras: extra elements to be included in parsing process.
    """

    def __init__(self):  # type: () -> None
        self.block_elements = {}  # type: Dict[str, BlockElementType]
        self.inline_elements = {}  # type: Dict[str, InlineElementType]

        for el in itertools.chain(
            (getattr(block, name) for name in block.__all__),
            (getattr(inline, name) for name in inline.__all__),
        ):
            self.add_element(el)

    def add_element(self, element):  # type: (ElementType) -> None
        """Add an element to the parser.

        :param element: the element class.

        .. note:: If one needs to call it inside ``__init__()``, please call it after
             ``super().__init__()`` is called.
        """
        dest = {}  # type: Dict[str, ElementType]
        if issubclass(element, inline.InlineElement):
            dest = self.inline_elements  # type: ignore
        elif issubclass(element, block.BlockElement):
            dest = self.block_elements  # type: ignore
        else:
            raise TypeError(
                "The element should be a subclass of either `BlockElement` or "
                "`InlineElement`."
            )
        dest[element.get_type()] = element

    def parse(self, source_or_text):
        # type: (Union[Source, AnyStr]) -> Union[List[block.BlockElement], block.BlockElement]
        """Do the actual parsing and returns an AST or parsed element.

        :param source_or_text: the text or source object.
            Based on the type, it will do following:
            - text: returns the parsed Document element.
            - source: parse the source and returns the parsed children as a list.
        """
        if isinstance(source_or_text, str):
            block.parser = self  # type: ignore
            inline.parser = self  # type: ignore
            return self.block_elements["Document"](source_or_text)  # type: ignore
        element_list = self._build_block_element_list()
        ast = []  # type: List[block.BlockElement]
        assert isinstance(source_or_text, Source)
        while not source_or_text.exhausted:
            for ele_type in element_list:
                if ele_type.match(source_or_text):
                    result = ele_type.parse(source_or_text)
                    if not hasattr(result, "priority"):
                        # In some cases ``parse()`` won't return the element, but
                        # instead some information to create one, which will be passed
                        # to ``__init__()``.
                        result = ele_type(result)  # type: ignore
                    ast.append(result)
                    break
            else:
                # Quit the current parsing and go back to the last level.
                break
        return ast

    def parse_inline(self, text):  # type: (str) -> List[inline.InlineElement]
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

    def _build_block_element_list(self):  # type: () -> List[BlockElementType]
        """Return a list of block elements, ordered from highest priority to lowest."""
        return sorted(
            (e for e in self.block_elements.values() if not e.virtual),
            key=lambda e: e.priority,
            reverse=True,
        )

    def _build_inline_element_list(self):  # type: () -> List[InlineElementType]
        """Return a list of elements, each item is a list of elements
        with the same priority.
        """
        return [e for e in self.inline_elements.values() if not e.virtual]


from . import block, inline, inline_parser, element  # noqa

if is_type_check():
    from typing import Type, Union, Dict, AnyStr, List

    BlockElementType = Type[block.BlockElement]
    InlineElementType = Type[inline.InlineElement]
    ElementType = Type[element.Element]
