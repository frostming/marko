"""
Python 2to3 compatibility
"""
# flake8: noqa
import sys

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = (str, unicode)   # noqa
    import backports.html as html
    from urllib import quote
else:
    string_types = str
    import html
    from urllib.parse import quote
