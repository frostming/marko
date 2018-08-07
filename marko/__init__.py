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
from .ast_renderer import ASTRenderer
from .block import Document
from .parser import Source


def markdown(text, renderer=ASTRenderer):
    """Parse and render the given text to HTML output with default settings."""
    with renderer() as renderer:
        return renderer.render(Document(Source(text)))
