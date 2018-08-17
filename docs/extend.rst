Extend Marko
============

Here is an example to add GitHub wiki links: ``[[Page 2|Page 2]]`` to the parsing process.

Create a new element
--------------------

Github wiki link is an inline level element. For the difference between block elements and inline elements,
please refer to `corresponding section <https://spec.commonmark.org/0.28/#container-blocks-and-leaf-blocks>`_ of Commonmark's spec.

Now subclass ``marko.inline.InlinElement`` to a new element type::

    from marko import inline

    class GithubWiki(inline.InlinElement):

        pattern = r'\[\[ *(.+?) *| *(.+?) *\]\]'
        parse_children = True

Inline elements use the ``pattern`` attribute to look for the matches in the text. To get more control of the scan process,
consider overriding ``find()`` method to return an iterable of matches. If ``parse_children`` is ``True``, parser will parse the group
given by ``parse_group``, which is 1 by default, of the match, as inline elements.

Now, write the ``__init__()`` method to control how the parsed result should map to element attributes.
You don't need to provide the parsed content since it is handled by parser automatically::

    class GithubWiki(inline.InlinElement):

        pattern = r'\[\[ *(.+?) *| *(.+?) *\]\]'
        parse_children = True

        def __init__(self, match):
            self.target = match.group(2)

About parsing priority
++++++++++++++++++++++

The parser respects element's ``priority`` attribute to control the parsing precedence. It is 5 by default, which is the same as emphasis, links and images.
For elements of the same priority, what comes the first will be parsed::

    *This is an [[emphasis*|target]]
    # Parsed as: <em>This is an [[emphasis</em>|target]]

If we set a higher priority, it will be first parsed instead::

    *This is an <a href="target">emphasis*</a>

Register the element in parser
------------------------------

Now let's add the element to parser processing::

    from marko import Parser

    parser = Parser(GithubWiki)

This will register ``GithubWiki`` element to the parser other than default elements. Alternatively, you can subclass ``Parser`` and register any extra element inside::

    class MyParser(Parser):

        def __init__(self, *extras):
            super(MyParser, self).__init__(*extras)
            self.add_element(GithubWiki)

About overriding default elements
+++++++++++++++++++++++++++++++++

Sometimes you modify the functionality of existing elements, like changing the parsing process or providing more attributes, and want to replace the old one.
In this case, you should use the second approach to register the element and call ``add_element`` with a second argument ``override=True``::

    class MyParser(Parser):

        def __init__(self, *extras):
            super(MyParser, self).__init__(*extras)
            self.add_element(MyLink, True)

Please note that super class's ``__init__`` should be called before the registration to ensure all default elements are ready.

Create a new renderer
---------------------

``marko.Renderer`` controlls how to represent the elements by the element name, in snake-cased form. In our case::

    from marko import HTMLRenderer

    class MyRenderer(HTMLRenderer):

        def render_github_wiki(self, element):
            return '<a href="{}">{}</a>'.format(
                self.escape_url(element.target), self.render_children(element)
            )

Here I subclass ``HTMLRenderer`` to inherit all other HTML render functions.

Besides HTML renderer, Marko also provides AST renderers to inspect the parsed AST. It is useful when developing your own parsing algorithm:

* ``marko.ast_renderer.ASTRenderer``: renders elements as JSON objects.
* ``marko.ast_renderer.XMLRenderer``: renders elements as XML format AST.

We are done
-----------

Let's take all together to parse the text::

    markdown("Some long text", parser=MyParser, renderer=MyRenderer)

Here ``parser`` and ``renderer`` arguments can be either a subclass of ``Parser`` and ``Renderer``, or an instance of it, respectively.
For more details, see :doc:`API References <api>`.
