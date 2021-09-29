class Element:
    @classmethod
    def get_element_type(cls):  # type: () -> str
        """Return the Markdown element type that the object represents."""

        # Prevent override of BlockElement and InlineElement
        if cls.override and cls.__base__ not in Element.__subclasses__():
            return cls.__base__.__name__
        else:
            return cls.__name__
