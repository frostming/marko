Marko
=====
> A markdown parser with high extensibility.

[![Build Status](https://travis-ci.org/frostming/marko.svg?branch=master)](https://travis-ci.org/frostming/marko)

Marko is a markdown parser written in pure Python that complies [CommonMark's spec v0.28][spec].
It is designed to be highly extensible, see [Extend Marko](#extend-marko) for details.

Marko requires Python 3.4 or higher, Python 2.7 support is still in plan but I guess it is not needed.

## Why Marko

Among all implementations of Python's markdown parser, it is a common issue that user can't easily extend it to add his own features. Furthermore, [Python-Markdown][pymd] and [mistune][mistune] don't comply CommonMark's spec. It is a good reason for me to develop a new markdown parser and use it.

Respecting that Marko complies CommonMark's spec at the same time, which is a super complicated spec, Marko's performance will be affected.
A benchmark result shows that Marko is 3 times slower than [Python-Markdown][pymd], but a bit faster than [Commonmark-py][cmpy], much slower than [mistune][mistune]. If performance is a bigger concern to you than spec compliance, you's better choose another parser.

[spec]: https://spec.commonmark.org/0.28/
[pymd]: https://github.com/waylan/Python-Markdown
[mistune]: https://github.com/lepture/mistune
[cmpy]: https://github.com/rtfd/CommonMark-py

## Use Marko

The installation is very simple:

    $ pip install marko

And to use it:
```python
import marko
marko.markdown('A long text')
```
Marko also provides a simple CLI, for example, to render a document and output to a html file:

    $ cat my_article.md | marko > my_article.html

## Extend Marko

Note that the signature of `marko.markdown()`:
```python
def markdown(text, parser=Parser, renderer=HTMLRenderer):
    ...
```
You can supply your own parser or renderer to it.

* A parser is what parses the document into separated elements.
* A renderer is what renders given element into desired output, which can be HTML in the most common situation.

## License

Marko is released under [MIT License](LICENSE)
