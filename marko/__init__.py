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
from .base_renderer import BaseRenderer
from .block import Document


def markdown(text, renderer=HTMLRenderer):
    """Parse and render the given text to HTML output with default settings."""
    if issubclass(renderer, BaseRenderer):
        renderer = renderer()
    assert isinstance(
        renderer, BaseRenderer
    ), "The renderer must be a subclass or instance of BaseRenderer`."
    with renderer as renderer:
        return renderer.render(Document(text))
