import dataclasses
from typing import Any, Callable, Container, Iterable, TypeVar, overload

from .element import Element
from .renderer import Renderer

RendererFunc = Callable[[Any, Element], Any]
TRenderer = TypeVar("TRenderer", bound=RendererFunc)
D = TypeVar("D", bound="_RendererDispatcher")

def camel_to_snake_case(name: str) -> str: ...
def is_paired(text: Iterable[str], open: str = "(", close: str = ")") -> bool: ...
def normalize_label(label: str) -> str: ...
def find_next(
    text: str,
    target: Container[str],
    start: int = 0,
    end: int | None = None,
    disallowed: Container[str] = (),
) -> int: ...
def partition_by_spaces(text: str, spaces: str = " \t") -> tuple[str, str, str]: ...

@dataclasses.dataclass(frozen=True)
class MarkoExtension:
    parser_mixins: list[type] = dataclasses.field(default_factory=list)
    renderer_mixins: list[type] = dataclasses.field(default_factory=list)
    elements: list[type[Element]] = dataclasses.field(default_factory=list)

def load_extension(name: str, **kwargs: Any) -> MarkoExtension: ...

class _RendererDispatcher:
    name: str
    def __init__(
        self, types: type[Renderer] | tuple[type[Renderer], ...], func: RendererFunc
    ) -> None: ...
    def dispatch(
        self: D, types: type[Renderer] | tuple[type[Renderer], ...]
    ) -> Callable[[RendererFunc], D]: ...
    def __set_name__(self, owner: type, name: str) -> None: ...
    @staticmethod
    def render_ast(self: Any, element: Element) -> Any: ...
    def super_render(self, r: Any, element: Element) -> Any: ...
    @overload
    def __get__(self: D, obj: None, owner: type) -> D: ...
    @overload
    def __get__(self: D, obj: Renderer, owner: type) -> RendererFunc: ...

def render_dispatch(
    types: type[Renderer] | tuple[type[Renderer], ...],
) -> Callable[[RendererFunc], _RendererDispatcher]: ...
