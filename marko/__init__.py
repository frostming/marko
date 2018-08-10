#! -*- coding: utf-8 -*-
"""
  _    _     _     ___   _  _    ___
 | \  / |   /_\   | _ \ | |/ /  / _ \
 | |\/| |  / _ \  |   / | ' <  | (_) |
 |_|  |_| /_/ \_\ |_|_\ |_|\_\  \___/

 A markdown parser with high extensibility.

 Licensed under MIT.
 Created by Frost Ming<mianghong@gmail.com>
"""
from .html_renderer import HTMLRenderer
from .renderer import Renderer
from .parser import Parser


def markdown(text, parser=Parser, renderer=HTMLRenderer):
    """Parse and render the given text to HTML output with default settings.

    :param parser: a Parser class or instance to parse text into AST.
    :param renderer: a Renderer class or instance to render AST as output.
    """
    if issubclass(renderer, Renderer):
        renderer = renderer()
    assert isinstance(
        renderer, Renderer
    ), "The renderer must be a subclass or instance of `Renderer`."
    if issubclass(parser, Parser):
        parser = Parser()
    assert isinstance(
        parser, Parser,
    ), "The parser must be a subclass or instance of `Parser`."
    with renderer as r:
        return r.render(parser.parse(text))
