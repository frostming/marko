"""
Python 2to3 compatibility
"""
import sys

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = (str, unicode)   # noqa
else:
    string_types = str
