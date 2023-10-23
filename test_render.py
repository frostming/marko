import marko
from marko.md_renderer import MarkdownRenderer

text = """\
Here's some *text* and a footnote[^a] and a [test *link*][link]
and [another link](abc "ahaha").

1. a list

> a *quote*

[^a]: A

[link]: abc "ahaha"
"""
md = marko.Markdown(renderer=MarkdownRenderer, extensions=["footnote"])
print(md.convert(text), end="")
