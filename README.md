# 𝓜𝓪𝓻𝓴𝓸

> A markdown parser with high extensibility.

[![PyPI](https://img.shields.io/pypi/v/marko.svg?logo=python&logoColor=white)](https://pypi.org/project/marko/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/marko.svg?logo=python&logoColor=white)](https://pypi.org/project/marko/)
[![Documentation Status](https://img.shields.io/readthedocs/marko-py.svg?logo=readthedocs)](https://marko-py.readthedocs.io/en/latest/?badge=latest)
[![CommonMark Spec](https://img.shields.io/badge/CommonMark-0.30-blue.svg)][spec]

![Build Status](https://github.com/frostming/marko/workflows/Tests/badge.svg)
[![codecov](https://codecov.io/gh/frostming/marko/branch/master/graph/badge.svg)](https://codecov.io/gh/frostming/marko)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b785f5b3fa7c4d93a02372d31b3f73b1)](https://www.codacy.com/app/frostming/marko?utm_source=github.com&utm_medium=referral&utm_content=frostming/marko&utm_campaign=Badge_Grade)

Marko is a markdown parser written in pure Python that complies with [CommonMark's spec v0.30][spec].
It is designed to be highly extensible, see [Extensions](#extensions) for details.

Marko requires Python 3.6 or higher.

## Why Marko

Among all implementations of Python's markdown parser, it is a common issue that user can't easily extend it to add his own features. Furthermore, [Python-Markdown][pymd] and [mistune][mistune] don't comply with CommonMark's spec. It is a good reason for me to develop a new markdown parser.

Respecting that Marko complies with CommonMark's spec at the same time, which is a super complicated spec, Marko's performance will be affected. However, using a parser
which doesn't comply with the CommonMark spec may give you unexpected rendered results from time to time.
A benchmark result shows that Marko is 3 times slower than [Python-Markdown][pymd], but a bit faster than [Commonmark-py][cmpy], much slower than [mistune][mistune]. If performance is a bigger concern to you than spec compliance, you'd better choose another parser.

[spec]: https://spec.commonmark.org/0.30/
[pymd]: https://github.com/waylan/Python-Markdown
[mistune]: https://github.com/lepture/mistune
[cmpy]: https://github.com/rtfd/CommonMark-py

## Use Marko

The installation is very simple:

    $ pip install marko

And to use it:

```python
import marko

print(marko.convert(text))
```

Marko also provides a simple CLI, for example, to render a document and output to a html file:

    $ cat my_article.md | marko > my_article.html

## Extensions

It is super easy to use an extension:

```python
from marko import Markdown
from marko.ext.footnote import Footnote
# Add footnote extension
markdown = Markdown(extensions=[Footnote])
# Or you can just:
markdown = Markdown(extensions=['footnote'])
# Alternatively you can register an extension later
markdown.use(Footnote)
```

An example of using an extension with the command-line version of Marko:

```
$ cat this_has_footnote.txt | marko -e footnote > hi_world.html
```

Marko is shipped with 4 extensions: `'footnote', 'toc' 'pangu', 'codehilite'`.
They are not included in CommonMark's spec but are common in other markdown parsers.

Marko also provides a Github flavored markdown parser which can be found at `marko.ext.gfm.gfm`.

Please refer to [Extend Marko](https://marko-py.readthedocs.io/en/latest/extend.html) about how to
write your own extension.

## License

Marko is released under [MIT License](LICENSE)

## [Change Log](CHANGELOG.md)
