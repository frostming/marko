from marko.elements.base import BaseElement
from marko.elements import inline, block
from marko.elements.inline import InlineElement
from marko.elements.block import BlockElement


def get_all(module):
    return (getattr(module, name) for name in module.__all__)


INLINE_ELEMENTS = get_all(inline)
BLOCK_ELEMENTS = get_all(block)

__all__ = [
    "INLINE_ELEMENTS",
    "BLOCK_ELEMENTS",
    "BaseElement",
    "BlockElement",
    "InlineElement",
]
