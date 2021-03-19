import pytest

from marko import helpers


@pytest.mark.parametrize(
    "raw_string",
    [
        "(hello(to)world)",
        r"(hello\)world)",
        r"he\(llo(world)",
        "",
        "hello world",
        "(hello), (world)",
    ],
)
def test_is_paired(raw_string):
    assert helpers.is_paired(raw_string)


@pytest.mark.parametrize(
    "raw_string",
    [
        "(hello(toworld)",
        "(hello)world)",
        "(",
    ],
)
def test_is_not_paired(raw_string):
    assert not helpers.is_paired(raw_string)


def test_source_no_state():
    source = helpers.Source("hello world")

    with pytest.raises(RuntimeError, match="Need to push a state first"):
        source.root

    with pytest.raises(RuntimeError, match="Need to push a state first"):
        source.state


def test_load_extension_object():
    ext = helpers.load_extension_object("pangu")()
    assert len(ext.renderer_mixins) == 1

    ext = helpers.load_extension_object("marko.ext.pangu")()
    assert len(ext.renderer_mixins) == 1

    with pytest.raises(ImportError, match="Extension foobar cannot be found"):
        helpers.load_extension_object("foobar")()


def test_load_illegal_extension_object():
    with pytest.raises(
        AttributeError,
        match="Module marko.block does not have 'make_extension' attributte",
    ):
        helpers.load_extension_object("marko.block")()
