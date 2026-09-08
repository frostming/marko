import pytest

from marko.block import Document, Quote
from marko.source import Source


def test_under_state_restores_parent_after_exception():
    source = Source("text")
    document = Document()
    source.push_state(document)

    with pytest.raises(ValueError, match="parser failed"):
        with source.under_state(Quote()):
            raise ValueError("parser failed")

    assert source.state is document
    assert source.prefix == ""


def test_nested_under_state_unwinds_after_exception():
    source = Source("text")

    with pytest.raises(ValueError, match="parser failed"):
        with source.under_state(Document()):
            with source.under_state(Quote()):
                raise ValueError("parser failed")

    with pytest.raises(RuntimeError, match="Need to push a state first"):
        _ = source.state
