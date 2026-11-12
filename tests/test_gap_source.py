"""Gap tests for marko.source.Source internals.

Existing coverage: no-state RuntimeError (test_helpers), under_state restore
on exception (test_source_context). This file covers preprocessing, line
consumption, anchor/reset, prefix matching and the state stack.
"""

import pytest

from marko.block import Document, Quote
from marko.source import Source


def test_preprocess_normalizes_line_terminators_and_nul():
    source = Source("a\r\nb\rc\fd\x00e")
    assert source._buffer == "a\nb\nc\nd\ufffde"


def test_exhausted_flag():
    assert Source("").exhausted
    assert not Source("x").exhausted


def test_next_line_consume_advances_position():
    source = Source("hello\nworld\n")
    assert source.next_line(require_prefix=False) == "hello\n"
    source.consume()
    assert source.pos == 6
    assert source.next_line(require_prefix=False) == "world\n"
    source.consume()
    assert source.pos == 12
    assert source.exhausted


def test_anchor_and_reset():
    source = Source("hello\nworld\n")
    source.next_line(require_prefix=False)
    source.consume()
    source.anchor()
    source.next_line(require_prefix=False)
    source.consume()
    assert source.pos == 12
    source.reset()
    assert source.pos == 6


def test_pop_state_on_empty_stack_raises_index_error():
    with pytest.raises(IndexError):
        Source("x").pop_state()


def test_root_and_state_stack():
    source = Source("text")
    document = Document()
    source.push_state(document)
    assert source.root is document
    assert source.state is document
    quote = Quote()
    source.push_state(quote)
    assert source.state is quote
    assert source.root is document
    assert source.pop_state() is quote
    assert source.state is document


def test_prefix_empty_without_states():
    assert Source("x").prefix == ""


@pytest.mark.parametrize(
    "prefix, line, expected",
    [
        (r"    ", "\tcode", 1),
        (r"> ", "x", -1),
        (r"", "anything", 0),
    ],
)
def test_match_prefix(prefix, line, expected):
    assert Source.match_prefix(prefix, line) == expected


def test_initial_match_is_none_and_pos_zero():
    source = Source("hello")
    assert source.pos == 0
    assert source.match is None
