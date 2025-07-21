from marko import Markdown
from marko.renderers.md_renderer import MarkdownRenderer
from marko.elements.block import Document
from marko.ops import merge


def test_merge():
    first = """
    # Heading 1
    Th`is is a paragraph with **bold** and *italic* text.

    ## Heading 2
    - List item 1
    - List item 2
    - List item 3

    [L`ink to Google](https://www.google.com)
    """

    second = """
    ### Heading 3
    Here's a code block:
    ```python
    print("Hello, World!")
    """

    markdown = Markdown(renderer=MarkdownRenderer)
    assert (markdown.convert(first) + markdown.convert(second)) == (
        markdown.render(merge([markdown.parse(first), markdown.parse(second)]))
    )
