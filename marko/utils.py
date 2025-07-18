import re


def camel_to_snake_case(name: str) -> str:
    """Takes a camelCased string and converts to snake_case."""
    pattern = r"[A-Z][a-z]+|[A-Z]+(?![a-z])"
    return "_".join(map(str.lower, re.findall(pattern, name)))
