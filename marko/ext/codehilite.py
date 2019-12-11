"""
Code highlight extension
~~~~~~~~~~~~~~~~~~~~~~~~

Enable code highlight using ``pygments``. This requires to install `codehilite` extras::

    pip install marko[codehilite]

Usage::

    from marko import Markdown

    markdown = Markdown(extensions=['codehilite'])
    markdown.convert(```python my_script.py\nprint('hello world')\n```)
"""
