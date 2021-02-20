Extend Marko
============

Here is an example of supporting parsing GitHub wiki links: ``[[Page 2|Page 2]]``.

Create a new element
--------------------

GitHub wiki link is an inline level element. For the difference between block elements and inline elements,
please refer to the `corresponding section <https://spec.commonmark.org/0.28/#container-blocks-and-leaf-blocks>`_ of Commonmark's spec.

Now subclass ``marko.inline.InlineElement`` to create a new element type::

    from marko import inline

    class GitHubWiki(inline.InlineElement):

        pattern = r'\[\[ *(.+?) *| *(.+?) *\]\]'
        parse_children = True

Inline elements use the ``pattern`` attribute to look for the matches in the text. To get more control of the scan process,
consider overriding ``find()`` method to return an iterable of matches. If ``parse_children`` is ``True``, parser will parse the group
given by ``parse_group`` of the match to produce inline elements, the default group is 1. See :ref:`elements` for available attributes
and methods to change the parsing behavior.

Now, write the ``__init__()`` method to control how the parsed result should map to element attributes.
You don't need to provide the parsed content since it is handled by parser automatically::

    class GitHubWiki(inline.InlineElement):

        pattern = r'\[\[ *(.+?) *| *(.+?) *\]\]'
        parse_children = True

        def __init__(self, match):
            self.target = match.group(2)

About the parsing priority
++++++++++++++++++++++++++

The parser respects element's ``priority`` attribute to control the parsing precedence. It is 5 by default, which is the same as emphasis, links and images. A higher number means the element will be tried sooner.
For elements of the same priority, what comes the first will be parsed::

    *This is an [[emphasis*|target]]
    # Parsed as: <em>This is an [[emphasis</em>|target]]

If we set a higher priority (e.g. 6), it will be tried sooner::

    *This is an <a href="target">emphasis*</a>

About overriding default elements
+++++++++++++++++++++++++++++++++

Sometimes you may want to modify the functionality of existing elements, like changing the parsing process or providing more attributes, and want to replace the old one.
In this case, you should add ``override = True`` to the element attribute.

Add a new render function
-------------------------

Marko uses mixins to add functionalities to renderer or parser. Parser controls the parsing logic which you don't need
to change at the most of time, while renderer mixins controll how to represent the elements by the element name, in snake-cased form.
In our case::

    class WikiRendererMixin(object):

        def render_github_wiki(self, element):
            return '<a href="{}">{}</a>'.format(
                self.escape_url(element.target), self.render_children(element)
            )

The renderer mixins will be combined together with marko's default base renderer: ``HTMLRenderer``,
which you need in most cases, to create a :class:`marko.renderer.Renderer` instance.

Besides of the HTML renderer, Marko also provides some AST renderers to inspect the parsed AST.
They are useful to see how parsing works when you are developing your own parsing algorithm:

* ``marko.ast_renderer.ASTRenderer``: renders elements as JSON objects.
* ``marko.ast_renderer.XMLRenderer``: renders elements as XML format AST.

Create an extension object
--------------------------

We need an additional extension object to sum these mixins up. It is typically a simple class,
though other Python objects may also work::

The extension object protocol is something like::

    type Extension
        one-of: elements, renderer_mixins, parser_mixins

And our ``GitHubWiki`` extension should be::

    class GitHubWiki:
        elements = [GitHubWiki]
        renderer_mixins = [WikiRendererMixin]

An optional ``parser_mixins`` can be also given if you want to customize the parser.
The extension exposes a single object so that it can be distributed as a standalone package. We will come to how to use it in the later sections.

Sometimes the extension can leave some arguments for users to customize. In this case, you can create an "extension factory" ::

    class GitHubWiki:
        def __init__(self, arg):
            WikiRendererMixin.arg = arg
            self.elements = [GitHubWiki]
            self.renderer_mixins = [WikiRendererMixin]

Register the extension
----------------------

Now you have your own extension ready, let's register it to the markdown parser::

    from marko import Markdown

    markdown = Markdown(extensions=[GitHubWiki])
    # Alternatively, you can register extensions later.
    markdown = Markdown()
    markdown.use(GitHubWiki)
    print(markdown(text))

.. note::

    The ``extensions`` argument, or ``use()`` accepts multiple extension objects.
    You can also call it multiple times. The registration order matters in the way that
    the last registered has the highest priority in the MRO.

    You can also choose a different base parser or renderer by::

        markdown = Markdown(renderer=marko.ast_renderer.ASTRenderer)

Let's have a look at how Marko creates the renderer with the extensions and base renderer class. The same applies for the parser.

Assume you choose ``HTMLRenderer`` as the base renderer class and have three extensions ``A, B, C`` registered in order::

    class A:
        renderer_mixins = [ARendererMixin]

    class B:
        renderer_mixins = [BRendererMixin]

    class C:
        renderer_mixins = [CRendererMixin]

    markdown = Markdown(extensions=[A, B, C])

Then the renderer is created like following::

    class MyRenderer(CRendererMixin, BRendererMixin, ARendererMixin, HTMLRenderer):
        pass

Note the order of the multi inheriting.

Publish the extension as package
--------------------------------
You can also refer to the extension without actually importing the extension object.

To do so, put a ``make_extension()`` function in the entry file which takes any arguments and returns an extension object::

    def make_extension(arg):
        return GitHubWiki(arg)

Then you can refer to the extension via import string(assume the package name is ``marko_github_wiki``)::

    markdown = Markdown(extensions=["marko_github_wiki"])
