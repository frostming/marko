#! -*- coding: utf-8 -*-
"""
Inline(span) level elements
"""


_element_types = {}


def add_element(element_type, override=False):
    """Add an inline element.

    :param element_type: the element type class.
    :param override: whether to replace the element type that bases.
    """
    if not override:
        _element_types[element_type.__name__] = element_type
    else:
        for cls in element_type.__mro__:
            if cls in _element_types.values():
                _element_types[cls.__name__] = element_type
                break
        else:
            _element_types[element_type.__name__] = element_type


def get_elements():
    return sorted(_element_types.values(), lambda e: e.priority)
