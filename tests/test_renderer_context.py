import html

import pytest

from marko.block import Document
from marko.renderer import Renderer


@pytest.mark.parametrize("reuse_renderer", [False, True])
@pytest.mark.parametrize("raise_inside", [False, True])
def test_nested_renderer_preserves_outer_context(reuse_renderer, raise_inside):
    outer = Renderer()
    inner = outer if reuse_renderer else Renderer()
    original = html._charref

    with outer:
        document = Document()
        outer.root_node = document
        assert html.unescape("&copy") == "&copy"

        try:
            with inner:
                if raise_inside:
                    raise ValueError("render failed")
        except ValueError:
            pass

        assert html.unescape("&copy") == "&copy"
        assert outer.root_node is document

    assert html._charref is original
    assert outer.root_node is None
