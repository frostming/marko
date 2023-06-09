.. Marko documentation master file, created by
   sphinx-quickstart on Thu Aug 16 19:04:07 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Marko: A markdown parser with high extensibility.
=================================================

.. image:: https://github.com/frostming/marko/workflows/Tests/badge.svg
    :target: https://github.com/frostming/marko/workflows/Tests
.. image:: https://img.shields.io/pypi/v/marko.svg
    :target: https://pypi.org/project/marko/
.. image:: https://img.shields.io/pypi/pyversions/marko.svg
   :target: https://pypi.org/project/marko/
.. image:: https://img.shields.io/badge/CommonMark-0.30-blue.svg
   :target: https://spec.commonmark.org/0.30/

Marko is a pure Python markdown parser that adheres to the specifications of `CommonMark's spec v0.30 <https://spec.commonmark.org/0.30/>`_.
It has been designed with high extensibility in mind, as detailed in the :doc:`Extend Marko <extend>` section.

Marko requires Python 3.7 or higher.

Why Marko?
----------

Of all the Python markdown parsers available, a common issue is the difficulty for users to add their own features.
Additionally, both `Python-Markdown`_ and `mistune`_ do not comply with CommonMark specifications.
This has prompted me to develop a new markdown parser.

Marko's compliance with the complex CommonMark specification can impact its performance.
However, using a parser that does not adhere to this spec may result in unexpected rendering outcomes.
According to benchmark results, Marko is three times slower than Python-Markdown but slightly faster than Commonmark-py
and significantly slower than mistune. If prioritizing performance over spec compliance is crucial for you,
it would be best to opt for another parser.

.. _Python-Markdown: https://github.com/waylan/Python-Markdown
.. _mistune: https://github.com/lepture/mistune
.. _Commonmark-py: https://github.com/rtfd/CommonMark-py

Install and Use Marko
---------------------

The installation is very simple::

    $ pip install marko

And to use it::

    import marko

    print(marko.convert(text))

Marko also provides a simple CLI, for example, to render a document and output to a html file::

    $ cat my_article.md | marko > my_article.html

Other CLI usage::

    usage: marko [-h] [-v] [-p PARSER] [-r RENDERER] [-e EXTENSTION] [-o OUTPUT]
             [document]

    positional arguments:
    document              The document to convert, will use stdin if not given.

    optional arguments:
    -h, --help            show this help message and exit
    -v, --version         show program's version number and exit
    -p PARSER, --parser PARSER
                            Specify another parser class
    -r RENDERER, --renderer RENDERER
                            Specify another renderer class
    -e EXTENSTION, --extension EXTENSTION
                            Specify the import name of extension, can be given
                            multiple times
    -o OUTPUT, --output OUTPUT
                            Ouput to a file

Other Contents
--------------

.. toctree::
    :maxdepth: 2

    extend
    extensions
    api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
