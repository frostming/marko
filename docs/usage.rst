Usage Guide
===========

This guide covers the basic usage of Marko's main APIs for parsing and rendering Markdown documents.

Quick Start
-----------

The simplest way to use Marko is through the convenience functions::

    import marko

    # Convert markdown to HTML
    html = marko.convert("# Hello World\nThis is **bold** text.")
    print(html)
    # Output: <h1>Hello World</h1>\n<p>This is <strong>bold</strong> text.</p>\n

The Markdown Object
-------------------

For more control and customization, use the :class:`~marko.Markdown` class::

    from marko import Markdown

    # Create a Markdown instance
    md = Markdown()

    # Convert markdown text
    html = md.convert("# Hello World")
    # Or use the shorthand
    html = md("# Hello World")

Customizing Parser and Renderer
-------------------------------

You can specify custom parser and renderer classes when creating a :class:`~marko.Markdown` instance:

Using Different Renderers
~~~~~~~~~~~~~~~~~~~~~~~~~

Marko provides several built-in renderers::

    from marko import Markdown, Parser, HTMLRenderer
    from marko.md_renderer import MarkdownRenderer
    from marko.ast_renderer import ASTRenderer, XMLRenderer

    # Default HTML renderer
    md = Markdown(parser=Parser, renderer=HTMLRenderer)

    # Markdown renderer (normalizes markdown)
    md_to_md = Markdown(renderer=MarkdownRenderer)
    normalized = md_to_md("# Heading\n\n\nExtra newlines")

    # AST renderer (returns dict representation)
    md_ast = Markdown(renderer=ASTRenderer)
    ast_dict = md_ast("# Hello")
    # {'element': 'document', 'children': [{'element': 'heading', 'level': 1, 'children': ['Hello']}]}

    # XML renderer
    md_xml = Markdown(renderer=XMLRenderer)
    xml = md_xml("# Hello")

Using Extensions
----------------

Marko supports a powerful extension system. Extensions can add new elements, modify parsing behavior, and customize rendering. See :doc:`extensions` for details about built-in extensions and :doc:`extend` for creating custom extensions.

Loading Extensions
~~~~~~~~~~~~~~~~~~

There are several ways to use extensions::

    from marko import Markdown

    # Method 1: Pass extensions during initialization
    md = Markdown(extensions=['footnote', 'toc'])

    # Method 2: Use the use() method
    md = Markdown()
    md.use('footnote')
    md.use('toc')

    # Method 3: Pass extension objects
    from marko.ext.footnote import make_extension
    md = Markdown(extensions=[make_extension()])

Built-in Extensions
~~~~~~~~~~~~~~~~~~~

Marko includes several built-in extensions. See :doc:`extensions` for detailed information about each extension and their usage.

Working with the AST
--------------------

The parsed document is an Abstract Syntax Tree (AST) that you can traverse and manipulate::

    from marko import Markdown

    md = Markdown()
    doc = md.parse("# Title\n\nParagraph with **bold** text.")

    # The document has a tree structure
    print(doc)  # Document object
    print(doc.children)  # List of block elements

    # Access specific elements
    heading = doc.children[0]  # Heading element
    print(heading.level)  # 1
    print(heading.children)  # ['Title']

    paragraph = doc.children[1]  # Paragraph element
    print(paragraph.children)  # List of inline elements

For more details about element types, see :ref:`elements`.

Custom Rendering
----------------

Create custom renderers by subclassing :class:`~marko.renderer.Renderer`::

    from marko.renderer import Renderer

    class MyCustomRenderer(Renderer):
        def render_heading(self, element):
            # Custom heading rendering
            return f"<h{element.level} class='my-heading'>{self.render_children(element)}</h{element.level}>"

        def render_paragraph(self, element):
            # Custom paragraph rendering
            return f"<p class='my-paragraph'>{self.render_children(element)}</p>"

    # Use the custom renderer
    md = Markdown(renderer=MyCustomRenderer)
    html = md.convert("# Hello\n\nWorld")

Thread Safety
-------------

.. warning::
   The :class:`~marko.Markdown` class is **not thread-safe**. Create a new instance for each thread.

::

    import threading
    from marko import Markdown

    def worker():
        # Each thread should have its own Markdown instance
        md = Markdown()
        result = md.convert("# Thread-specific content")
        return result

    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

Common Patterns
---------------

Pre-processing Text
~~~~~~~~~~~~~~~~~~~

Override the ``parse`` method to pre-process text::

    class MyMarkdown(Markdown):
        def parse(self, text):
            # Pre-process text before parsing
            text = text.replace('TODO:', '**TODO:**')
            return super().parse(text)

    md = MyMarkdown()
    html = md.convert("TODO: Important task")

Post-processing Results
~~~~~~~~~~~~~~~~~~~~~~~

Override the ``render`` method to post-process results::

    class MyMarkdown(Markdown):
        def render(self, parsed):
            html = super().render(parsed)
            # Post-process HTML
            return html.replace('<p>', '<p class="content">')

    md = MyMarkdown()
    html = md.convert("Hello world")

Converting Multiple Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    from marko import Markdown

    md = Markdown(extensions=['gfm', 'codehilite'])

    documents = ["# Doc 1", "# Doc 2", "# Doc 3"]
    html_docs = [md(doc) for doc in documents]

Reformat Markdown Document
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    from marko import Markdown
    from marko.md_renderer import MarkdownRenderer

    md = Markdown(renderer=MarkdownRenderer)
    text = md("# Heading\n\nThis is __bold__ text.")
    print(text)  # "# Heading\n\nThis is **bold** text.\n"

Converting Files
~~~~~~~~~~~~~~~~

::

    from marko import Markdown

    md = Markdown()

    # Read and convert a markdown file
    with open('document.md', 'r') as f:
        content = f.read()
        html = md.convert(content)

    # Write to HTML file
    with open('document.html', 'w') as f:
        f.write(html)

Extracting Links
~~~~~~~~~~~~~~~~

::

    from marko import Markdown
    from marko.ast_renderer import ASTRenderer

    md = Markdown(renderer=ASTRenderer)
    ast = md("[Link](https://example.com)")

    def extract_links(node):
        links = []
        if isinstance(node, dict):
            if node.get('element') == 'link':
                links.append(node.get('dest'))
            if 'children' in node:
                for child in node['children']:
                    links.extend(extract_links(child))
        elif isinstance(node, list):
            for item in node:
                links.extend(extract_links(item))
        return links

    links = extract_links(ast)
    print(links)  # ['https://example.com']

Best Practices
--------------

1. **Reuse Markdown instances** when possible (but not across threads)
2. **Load extensions once** during initialization
3. **Use appropriate renderers** for your output format
4. **Handle untrusted input carefully** - Marko escapes HTML by default
5. **Test with CommonMark spec** - Marko follows CommonMark 0.31.2

Performance Considerations
--------------------------

* Marko prioritizes spec compliance over speed
* For best performance, reuse :class:`~marko.Markdown` instances when possible
* Consider using simpler parsers if you don't need full CommonMark compliance

Next Steps
----------

* Learn how to create custom extensions in :doc:`extend`
* Explore available extensions in :doc:`extensions`
* Check the :doc:`api` for detailed class and method documentation
