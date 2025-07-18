"""
Base parser
"""

from __future__ import annotations

from typing import cast, Type
from pydantic import BaseModel, Field, model_validator, ConfigDict

from marko.parser import inline_parsing
from marko.source import Source
from marko.elements import (
    BlockElement,
    InlineElement,
    BaseElement,
    INLINE_ELEMENTS,
    BLOCK_ELEMENTS,
)
from marko.elements.block import Document


BlockElementType = Type[BlockElement]
InlineElementType = Type[InlineElement]
BaseElementType = Type[BaseElement]


class Parser(BaseModel):
    """All elements defined in CommonMark's spec are included in the parser by default."""

    block_elements: dict[str, BlockElementType] = Field(default_factory=dict)
    """Block elements: give only custom ones."""
    inline_elements: dict[str, InlineElementType] = Field(default_factory=dict)
    """Inline elements: give only custom ones."""

    extra_elements: list[BaseElementType] = Field(default_factory=list)
    """Non-CommonMark elements."""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="before")
    @classmethod
    def add_default_elements(cls, data: dict) -> dict:
        """Add CommonMark elements."""

        block_elements = {}
        inline_elements = {}

        for element in data.get("extra_elements", []):
            # Add an element to the parser
            dest: dict[str, BaseElementType] = {}
            if issubclass(element, InlineElement):
                dest = inline_elements  # type: ignore
            elif issubclass(element, BlockElement):
                dest = block_elements  # type: ignore
            else:
                raise TypeError(
                    "The element should be a subclass of either `BlockElement` or "
                    "`InlineElement`."
                )
            dest[element.get_type()] = element

        inline_elements = {
            **inline_elements,
            **data.get("inline_elements", {}),
        }

        block_elements = {
            **block_elements,
            **data.get("block_elements", {}),
        }

        extra_elements: list[BaseElementType] = list(inline_elements.values()) + list(
            block_elements.values()
        )

        return {
            "inline_elements": {
                **INLINE_ELEMENTS,
                **inline_elements,
            },
            "block_elements": {
                **BLOCK_ELEMENTS,
                **block_elements,
            },
            "extra_elements": extra_elements,
        }

    def parse(self, text: str) -> Document:
        """Do the actual parsing and returns an AST or parsed element.

        :param text: the text to parse.
        :returns: the parsed root element
        """
        source = Source(text)
        source.parser = self
        doc = cast(Document, self.block_elements["Document"]())
        with source.under_state(doc):
            doc.children = self.parse_source(source)
            self.parse_inline(doc, source)
        return doc

    def parse_source(self, source: Source) -> list[BlockElement]:
        """Parse the source into a list of block elements."""
        element_list = self._build_block_element_list()
        ast: list[BlockElement] = []
        while not source.exhausted:
            for ele_type in element_list:
                if ele_type.match(source):
                    result = ele_type.parse(source)
                    if not hasattr(result, "priority"):
                        # In some cases ``parse()`` won't return the element, but
                        # instead some information to create one, which will be passed
                        # to ``__init__()``.
                        result = ele_type.initialize(result)  # type: ignore
                    ast.append(result)
                    break
            else:
                # Quit the current parsing and go back to the last level.
                break
        return ast

    def parse_inline(self, element: BlockElement, source: Source) -> None:
        """Inline parsing is postponed so that all link references
        are seen before that.
        """
        if element.inline_body:
            element.children = self._parse_inline(element.inline_body, source)
            # clear the inline body to avoid parsing it again.
            element.inline_body = ""
        else:
            for child in element.children:
                if isinstance(child, BlockElement):
                    self.parse_inline(child, source)

    def _parse_inline(self, text: str, source: Source) -> list[InlineElement]:
        """Parses text into inline elements.
        RawText is not considered in parsing but created as a wrapper of holes
        that don't match any other elements.

        :param text: the text to be parsed.
        :returns: a list of inline elements.
        """
        element_list = self._build_inline_element_list()
        return inline_parsing.parse(
            text, element_list, fallback=self.inline_elements["RawText"], source=source
        )

    def _build_block_element_list(self) -> list[BlockElementType]:
        """Return a list of block elements, ordered from highest priority to lowest."""
        return sorted(
            (e for e in self.block_elements.values() if not e.virtual),
            key=lambda e: e.priority,
            reverse=True,
        )

    def _build_inline_element_list(self) -> list[InlineElementType]:
        """Return a list of elements, each item is a list of elements
        with the same priority.
        """
        return [e for e in self.inline_elements.values() if not e.virtual]
