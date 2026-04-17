from .helpers import camel_to_snake_case as camel_to_snake_case

class Element:
    override: bool
    @classmethod
    def get_type(cls, snake_case: bool = False) -> str: ...
    def __repr__(self) -> str: ...
