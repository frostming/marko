.. Marko documentation master file, created by
   sphinx-quickstart on Thu Aug 16 19:04:07 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Marko: A markdown parser with high extensibility.
=================================================

.. image:: https://travis-ci.org/frostming/marko.svg?branch=master
    :target: https://travis-ci.org/frostming/marko
.. image:: https://img.shields.io/pypi/v/marko.svg
    :target: https://pypi.org/project/marko/
.. image:: https://img.shields.io/pypi/pyversions/marko.svg
   :target: https://pypi.org/project/marko/
.. image:: https://img.shields.io/badge/CommonMark-0.29-blue.svg
   :target: https://spec.commonmark.org/0.29/

Marko is a markdown parser written in pure Python that complies `CommonMark's spec v0.29 <https://spec.commonmark.org/0.29/>`_.
It is designed to be highly extensible, see :doc:`Extend Marko <extend>` for details.

Marko requires Python 2.7, Python 3.5 or higher.

Why Marko?
----------

Among all implementations of Python's markdown parser, it is a common issue that user can't easily extend it to add his own features.
Furthermore, `Python-Markdown`_ and `mistune`_ don't comply CommonMark's spec.
It is a good reason for me to develop a new markdown parser and use it.

Respecting that Marko complies CommonMark's spec at the same time, which is a super complicated spec, Marko's performance will be affected.
A benchmark result shows that Marko is 3 times slower than `Python-Markdown`_, but a bit faster than `Commonmark-py`_,
much slower than `mistune`_. If performance is a bigger concern to you than spec compliance, you's better choose another parser.

.. _Python-Markdown: https://github.com/waylan/Python-Markdown
.. _mistune: https://github.com/lepture/mistune
.. _Commonmark-py: https://github.com/rtfd/CommonMark-py

Install and Use Marko
---------------------

The installation is very simple::

    $ pip install marko

And to use it::

    from marko import Markdown
    markdown = Markdown()
    print(markdown(text))

Marko also provides a simple CLI, for example, to render a document and output to a html file::

    $ cat my_article.md | marko > my_article.html

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
