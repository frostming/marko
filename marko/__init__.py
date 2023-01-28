r"""
  _    _     _     ___   _  _    ___
 | \  / |   /_\   | _ \ | |/ /  / _ \
 | |\/| |  / _ \  |   / | ' <  | (_) |
 |_|  |_| /_/ \_\ |_|_\ |_|\_\  \___/

 A markdown parser with high extensibility.

 Licensed under MIT.
 Created by Frost Ming<mianghong@gmail.com>
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .helpers import load_extension_object
from .html_renderer import HTMLRenderer
from .parser import Parser
from .renderer import Renderer

if TYPE_CHECKING:

    from .block import Document
    from .parser import ElementType

__version__ = "1.3.0"


class SetupDone(Exception):
    def __str__(self) -> str:
        return "Unable to register more extensions after setup done."


class Markdown:
    """The main class to convert markdown documents.

    Attributes:
        * parser: an instance of :class:`marko.parser.Parser`
        * renderer: an instance of :class:`marko.renderer.Renderer`

    :param parser: a subclass :class:`marko.parser.Parser`.
    :param renderer: a subclass :class:`marko.renderer.Renderer`.
    :param extensions: a list of extensions to register on the object.
        See document of :meth:`Markdown.use()`.
    """

    def __init__(
        self,
        parser: type[Parser] = Parser,
        renderer: type[Renderer] = HTMLRenderer,
        extensions: Any | None = None,
    ) -> None:
        if not issubclass(parser, Parser):
            raise TypeError("parser must be a subclass of Parser.")
        self._base_parser = parser
        self._parser_mixins: list[Any] = []

        if not issubclass(renderer, Renderer):
            raise TypeError("renderer must be a subclass of Renderer.")
        self._base_renderer = renderer
        self._renderer_mixins: list[Any] = []

        self._extra_elements: list[ElementType] = []
        self._setup_done = False
        if extensions:
            self.use(*extensions)

    def use(self, *extensions: Any) -> None:
        r"""Register extensions to Markdown object.
        An extension should be either an object providing ``elements``, `parser_mixins``
        , ``renderer_mixins`` or all attributes, or a string representing the
        corresponding extension in ``marko.ext`` module.

        :param \*extensions: extension object or string.

        .. note:: Marko uses a mixin based extension system, the order of extensions
            matters: An extension preceding in order will have higher priorty.
        """
        if self._setup_done:
            raise SetupDone()
        for extension in extensions:
            if isinstance(extension, str):
                extension = load_extension_object(extension)()

            self._parser_mixins = (
                getattr(extension, "parser_mixins", []) + self._parser_mixins
            )
            self._renderer_mixins = (
                getattr(extension, "renderer_mixins", []) + self._renderer_mixins
            )
            self._extra_elements.extend(getattr(extension, "elements", []))

    def _setup_extensions(self) -> None:
        """Install all extensions and set things up."""
        if self._setup_done:
            return
        self.parser: Parser = type(
            "MarkdownParser", tuple(self._parser_mixins) + (self._base_parser,), {}
        )()
        for e in self._extra_elements:
            self.parser.add_element(e)
        self.renderer: Renderer = type(
            "MarkdownRenderer",
            tuple(self._renderer_mixins) + (self._base_renderer,),
            {},
        )()
        self._setup_done = True

    def convert(self, text: str) -> str:
        """Parse and render the given text."""
        return self.render(self.parse(text))

    def __call__(self, text: str) -> str:
        return self.convert(text)

    def parse(self, text: str) -> Document:
        """Call ``self.parser.parse(text)``.

        Override this to preprocess text or handle parsed result.
        """
        self._setup_extensions()
        return cast("Document", self.parser.parse(text))

    def render(self, parsed: Document) -> str:
        """Call ``self.renderer.render(text)``.

        Override this to handle parsed result.
        """
        self.renderer.root_node = parsed
        with self.renderer as r:
            return r.render(parsed)


# Inner instance, use the bare convert/parse/render function instead
_markdown = Markdown()


def convert(text: str) -> str:
    """Parse and render the given text.

    :param text: text to convert.
    :returns: The rendered result.
    """
    return _markdown.convert(text)


def parse(text: str) -> Document:
    """Parse the text to a structured data object.

    :param text: text to parse.
    :returns: the parsed object
    """
    return _markdown.parse(text)


def render(parsed: Document) -> str:
    """Render the parsed object to text.

    :param parsed: the parsed object
    :returns: the rendered result.
    """
    return _markdown.render(parsed)
