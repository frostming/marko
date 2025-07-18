"""
Helper functions and data structures
"""

from __future__ import annotations

from functools import partial
from importlib import import_module
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Type, TYPE_CHECKING, overload

from marko.renderers import BaseRenderer

if TYPE_CHECKING:
    from marko.elements.base import BaseElement
    from typing import Any, Callable, TypeVar

    RendererFunc = Callable[[Any, BaseElement], Any]
    TRenderer = TypeVar("TRenderer", bound=RendererFunc)
    D = TypeVar("D", bound="_RendererDispatcher")


class MarkoExtension(BaseModel):
    parser_mixins: List[Type] = Field(default_factory=list)
    renderer_mixins: List[Type] = Field(default_factory=list)

    elements: List[Type] = Field(default_factory=list)
    # must be Type[Element], but tests use as Any

    model_config = ConfigDict(frozen=True, extra="forbid")


def load_extension(name: str, **kwargs: Any) -> MarkoExtension:
    """Load extension object from a string.
    First try `marko.ext.<name>` if possible
    """
    module = None
    if "." not in name:
        try:
            module = import_module(f"marko.ext.{name}")
        except ImportError:
            pass
    if module is None:
        try:
            module = import_module(name)
        except ImportError as e:
            raise ImportError(f"Extension {name} cannot be imported") from e

    try:
        return module.make_extension(**kwargs)
    except AttributeError:
        raise AttributeError(
            f"Module {name} does not have 'make_extension' attributte."
        ) from None


class _RendererDispatcher:
    name: str

    def __init__(
        self,
        types: type[BaseRenderer] | tuple[type[BaseRenderer], ...],
        func: RendererFunc,
    ) -> None:
        from marko.renderers.ast_renderer import ASTRenderer, XMLRenderer

        self._mapping = {types: func}
        self._mapping.setdefault((ASTRenderer, XMLRenderer), self.render_ast)

    def dispatch(
        self: D, types: type[BaseRenderer] | tuple[type[BaseRenderer], ...]
    ) -> Callable[[RendererFunc], D]:
        def decorator(func: RendererFunc) -> D:
            self._mapping[types] = func
            return self

        return decorator

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    @staticmethod
    def render_ast(self, element: BaseElement) -> Any:
        return self.render_children(element)

    def super_render(self, r: Any, element: BaseElement) -> Any:
        """Call on the next class in the MRO which has the same method."""
        klasses = (c for c in type(r).mro() if self.name in c.__dict__)
        try:
            next(klasses)  # skip the current class
            parent = next(klasses)
        except StopIteration:
            raise NotImplementedError(f"Unsupported renderer {type(r)}") from None
        else:
            return getattr(parent, self.name)(r, element)

    @overload
    def __get__(self: D, obj: None, owner: type) -> D: ...

    @overload
    def __get__(self: D, obj: BaseRenderer, owner: type) -> RendererFunc: ...

    def __get__(self: D, obj: BaseRenderer | None, owner: type) -> RendererFunc | D:
        if obj is None:
            return self
        for types, func in self._mapping.items():
            if isinstance(obj, types):
                return partial(func, obj)
        return partial(self.super_render, obj)


def render_dispatch(
    types: type[BaseRenderer] | tuple[type[BaseRenderer], ...],
) -> Callable[[RendererFunc], _RendererDispatcher]:
    def decorator(func: RendererFunc) -> _RendererDispatcher:
        return _RendererDispatcher(types, func)

    return decorator
