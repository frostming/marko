"""
Python 2to3 compatibility
"""
import sys
import re

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = (str, unicode)   # noqa
else:
    string_types = str

camelcase_re = re.compile(r'([A-Z]+)(?=[a-z0-9])')


def camel_to_snake_case(name):

    def _join(match):
        word = match.group()

        if len(word) > 1:
            return ('_%s_%s' % (word[:-1], word[-1])).lower()

        return '_' + word.lower()

    return camelcase_re.sub(_join, name).lstrip('_')
