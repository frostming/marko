"""Gap tests for marko.cli argument parsing and class importing."""

import pytest

from marko.cli import import_class
from marko.cli import parse as cli_parse
from marko.html_renderer import HTMLRenderer
from marko.parser import Parser


def test_import_class_resolves_dotted_path():
    assert import_class("marko.html_renderer.HTMLRenderer") is HTMLRenderer


def test_import_class_missing_class_exits_with_message():
    with pytest.raises(SystemExit) as excinfo:
        import_class("marko.html_renderer.Nope")
    assert excinfo.value.code == "Cannot find class Nope in module marko.html_renderer"


def test_cli_parse_defaults():
    args = cli_parse([])
    assert args.parser is Parser
    assert args.renderer is HTMLRenderer
    assert args.extension == []
    assert args.output is None
    assert args.document is None


def test_cli_parse_extension_flag():
    args = cli_parse(["--extension", "toc"])
    assert args.extension == ["toc"]
