from typing import Any, overload

from marko import inline
from marko.element import Element

from .renderer import Renderer, force_delegate

class ASTRenderer(Renderer):
    delegate: bool

    # Narrowed return type for dict-returning renderer
    def render(self, element: Element) -> dict[str, Any]: ...

    @force_delegate
    def render_raw_text(self, element: inline.RawText) -> dict[str, Any]: ...
    @overload
    def render_children(self, element: list[Element]) -> list[dict[str, Any]]: ...
    @overload
    def render_children(self, element: Element) -> dict[str, Any]: ...
    @overload
    def render_children(self, element: str) -> str: ...

class XMLRenderer(Renderer):
    delegate: bool
    indent: int

    # Narrowed return types for str-returning renderer
    def render(self, element: Element) -> str: ...
    def render_children(self, element: Element) -> str: ...

    def __enter__(self) -> XMLRenderer: ...
    def __exit__(self, *args: Any) -> None: ...
