# Marko

> A markdown parser with high extensibility.

[![PyPI](https://img.shields.io/pypi/v/marko.svg?logo=python&logoColor=white)](https://pypi.org/project/marko/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/marko.svg?logo=python&logoColor=white)](https://pypi.org/project/marko/)
[![Documentation Status](https://img.shields.io/readthedocs/marko-py.svg?logo=readthedocs)](https://marko-py.readthedocs.io/en/latest/?badge=latest)
[![CommonMark Spec](https://img.shields.io/badge/CommonMark-0.29-blue.svg)][spec]

[![Build Status](https://img.shields.io/travis/frostming/marko/master.svg?label=Travis&logo=travis)](https://travis-ci.org/frostming/marko)
[![AppVeyor Status](https://img.shields.io/appveyor/ci/frostming/marko/master.svg?logo=appveyor)](https://ci.appveyor.com/project/frostming/marko/branch/master)
[![codecov](https://codecov.io/gh/frostming/marko/branch/master/graph/badge.svg)](https://codecov.io/gh/frostming/marko)

Marko is a markdown parser written in pure Python that complies [CommonMark's spec v0.29][spec].
It is designed to be highly extensible, see [Extend Marko](#extend-marko) for details.

Marko requires Python2.7, Python 3.5 or higher.

## Why Marko

Among all implementations of Python's markdown parser, it is a common issue that user can't easily extend it to add his own features. Furthermore, [Python-Markdown][pymd] and [mistune][mistune] don't comply CommonMark's spec. It is a good reason for me to develop a new markdown parser and use it.

Respecting that Marko complies CommonMark's spec at the same time, which is a super complicated spec, Marko's performance will be affected.
A benchmark result shows that Marko is 3 times slower than [Python-Markdown][pymd], but a bit faster than [Commonmark-py][cmpy], much slower than [mistune][mistune]. If performance is a bigger concern to you than spec compliance, you'd better choose another parser.

[spec]: https://spec.commonmark.org/0.29/
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

## Extend Marko

Please refer to [Document](https://marko-py.readthedocs.io/en/latest/extend.html)

## License

Marko is released under [MIT License](LICENSE)

## Change Log

- v0.5.1: Add type hints for all primary functions.
- v0.5.0: Update to comply commonmark spec 0.29; Change the extension system.
- v0.4.3: Fix TOC rendering when heading level exceeds the max depth.
- v0.4.2: Fix CJK regexp for pangu extension.
- v0.4.0: Support Python 2.7.
- v0.3.4: Fix bugs about extensions.
- v0.3.1: Pangu extension.
- v0.3.0: Change the entry function to a class, add TOC and footnotes extensions.
- v0.2.0: Github flavored markdown and docs.
- v0.1.0: Commonmark spec tests.
