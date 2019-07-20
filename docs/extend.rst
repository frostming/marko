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
given by ``parse_group`` of the match to produce inline elements, the default group is 1. See :ref:`elements` for available attributes
and methods to change the parsing behavior.

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

Define your parser mixin class
------------------------------

Marko uses mixins to add functionalities to the existing parser.
Now let's add the element to parser processing::

    class WikiParserMixin(object):

        def __init__(self, *extras):
            super(MyParser, self).__init__(*extras)
            self.add_element(GithubWiki)

This will register ``GithubWiki`` element to the parser besides default elements.

.. note::

    For Python 2 compatibility, mixin classes should explicitly inhert from ``object``, so that ``super``
    function can work correctly.

About overriding default elements
+++++++++++++++++++++++++++++++++

Sometimes you modify the functionality of existing elements, like changing the parsing process or providing more attributes, and want to replace the old one.
In this case, you should use the second approach to register the element and call ``add_element`` with a second argument ``override=True``::

    class MyParserMixin(object):

        def __init__(self, *extras):
            super(MyParser, self).__init__(*extras)
            self.add_element(MyLink, True)

Please note that super class's ``__init__`` should be called before the registration to ensure all default elements are ready.

Create a new renderer
---------------------

Renderer mixins controll how to represent the elements by the element name, in snake-cased form. In our case::

    class WikiRendererMixin(object):

        def render_github_wiki(self, element):
            return '<a href="{}">{}</a>'.format(
                self.escape_url(element.target), self.render_children(element)
            )

The renderer mixins will be combined together with marko's default base renderer: ``HTMLRenderer``,
which you need in most cases, to create a :class:`marko.renderer.Renderer` instance.

Besides HTML renderer, Marko also provides AST renderers to inspect the parsed AST.
They are useful to develop your own parsing algorithm:

* ``marko.ast_renderer.ASTRenderer``: renders elements as JSON objects.
* ``marko.ast_renderer.XMLRenderer``: renders elements as XML format AST.

Create an extension object
--------------------------

We need an additional extension object to sum these mixins up. It should have ``parser_mixins`` or ``renderer_mixins``
or both attributes to contain corresponding mixin classes in a list. It is typically a simple class,
and other Python objects may also work::

    class GithubWikiExtension:
        parser_mixins = [WikiParserMixin]
        renderer_mixins = [WikiRendererMixin]

The extension exposes a single object so that it can be distributed as a standalone package. Read the following section about
how to use it.

Register the extension
----------------------

Now you have your own extension ready, let's register it to the markdown parser::

    from marko import Markdown

    markdown = Markdown(extensions=[GithubWikiExtension])
    # Alternatively, you can register extensions later.
    markdown = Markdown()
    markdown.use(GithubWikiExtension)
    print(markdown(text))

.. note::

    The ``extensions`` argument, or ``use()`` accepts multiple extension objects.
    You can alsow call it multiple times. The registration order matters in the way that
    the first registered has the highest priority in the MRO.

    You can also choose a different base parser or renderer by::

        markdown = Markdown(renderer=marko.ast_renderer.ASTRenderer)
