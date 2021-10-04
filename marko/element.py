from .helpers import camel_to_snake_case, is_type_check

if is_type_check():
    from typing import Any


class Element:
    """This class holds attributes common to both the BlockElement and
    InlineElement classes.
    This class should not be subclassed by any other classes beside these.
    """
    @classmethod
    def get_type(cls, snake_case=False):  # type: (Any) -> str
        """
        Return the Markdown element type that the object represents.

        :param snake_case: Return the element type name in snake case if True
        """

        # Prevent override of BlockElement and InlineElement
        if cls.override and cls.__base__ not in Element.__subclasses__():
            name = cls.__base__.__name__
        else:
            name = cls.__name__
        return camel_to_snake_case(name) if snake_case else name
