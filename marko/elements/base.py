from __future__ import annotations

from typing import ClassVar, Any, Self
from langchain_core.load.serializable import Serializable

from marko.utils import camel_to_snake_case


class BaseElement(Serializable):
    """This class holds attributes common to both the BlockElement and
    InlineElement classes.
    This class should not be subclassed by any other classes beside these.
    """

    override: ClassVar[bool]
    children: Any

    @classmethod
    def initialize(cls, *args, **kwargs) -> Self:
        kwargs = cls.initialize_kwargs(*args, **kwargs)

        private_kwargs = dict()
        for field_name in list(kwargs.keys()):
            if field_name.startswith("_"):
                private_kwargs[field_name] = kwargs.pop(field_name)

        result = cls(**kwargs)

        for name, value in private_kwargs.items():
            setattr(result, name, value)

        return result

    @classmethod
    def initialize_kwargs(cls, *args, **kwargs) -> dict[str, Any]:
        return dict()

    @classmethod
    def get_type(cls, snake_case: bool = False) -> str:
        """
        Return the Markdown element type that the object represents.

        :param snake_case: Return the element type name in snake case if True
        """

        # Prevent override of BlockElement and InlineElement
        if (
            cls.override
            and cls.__base__
            and cls.__base__ not in BaseElement.__subclasses__()
        ):
            name = cls.__base__.__name__
        else:
            name = cls.__name__
        return camel_to_snake_case(name) if snake_case else name

    @classmethod
    def is_lc_serializable(cls) -> bool:
        return True

    def __repr__(self) -> str:
        try:
            from objprint import objstr
        except ImportError:
            from pprint import pformat

            if hasattr(self, "children") and (not (self.children is None)):
                children = f" children={pformat(self.children)}"
            else:
                children = ""

            return f"<{self.__class__.__name__}{children}>"
        else:
            return objstr(self, honor_existing=False, include=["children"])
