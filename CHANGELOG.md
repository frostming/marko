## Unreleased

- Forbid delegation to element-specific render methods for AST renderers.

## v1.1.0(2021-07-23)

- Update the implementation to conform with Commonmark 0.30 spec.

## v1.0.3(2021-06-07)

- Consider unicode punctuations when judging whether a delimiter is an opener or a closer.
- Prefix parsing is eager now.

## v1.0.2(2021-04-06)

- Fix a parsing crash if no newline following the prefix of a block element.
- Unescape html character refs in ASTRenderer result.
- Fix an index error when parsing an incomplete link.

## v1.0.1(2021-01-06)

- Remove the duplicate newlines in the output of paragraphs of markdown renderer.

## v1.0.0(2020-12-29)

- Drop support of Python 2.7
- Remove the deprecated extension object
- Blacken the code base

## v0.10.0(2020-11-23)

- Drop support of Python 3.5
- Fix a bug about rendering image links of `MarkdownRender`

## v0.9.1(2020-09-27)

- Fix an XSS issue that exists in code language field.

## v0.9.0(2020-09-27)

- Fix a bug that backslashes get dropped inside a table cell.
- Fix a bug that the priority of inline elements is not honored.
- Add a new renderer: `marko.md_renderer.MarkdownRenderer` which rerenders the input back to markdown text.

## v0.8.2(2020-06-22)

- Add support for specifying extensions in marko CLI.
- Display a help message when prompting for input in marko CLI.

## v0.8.1(2020-04-03)

- Fix a bug of list item parsing when mixed whitespace type is used.

## v0.8.0(2020-03-07)

- Support arguments for extensions

## v0.7.1(2019-12-20)

- Wrap code block with 'highlight' container in codehilite mode.

## v0.7.0(2019-12-11)

- Deprecate the extension name with `Extension` suffix, e.g. `FootnoteExtension` -> `Footnote`.
  And the old names will be removed by `v1.0.0`.
- Store extra info after the language text in fenced code:
  ````
  ```python myscript.py    <-- myscript.py is stored in element
  print('hello world')
  ```
  ````
- Built-in code highlight extension using pygments.

## v0.6.0(2019-7-26)

- Reverse the extension order.
- Add a new extension attribute `elements`.
- Improve the CLI, add more options.

## v0.5.1(2019-7-20)

- Add type hints for all primary functions.

## v0.5.0(2019-7-19)

- Update to comply commonmark spec 0.29.
- Change the extension system.

## v0.4.3(2018-9-11)

- Fix TOC rendering when heading level exceeds the max depth.

## v0.4.2(2018-8-16)

- Fix CJK regexp for pangu extension.

## v0.4.0(2018-8-24)

- Support Python 2.7.

## v0.3.4(2018-8-20)

- Fix bugs about extensions.

## v0.3.1(2018-8-20)

- Pangu extension.

## v0.3.0(2018-8-20)

- Change the entry function to a class, add TOC and footnotes extensions.

## v0.2.0(2018-8-17)

- Github flavored markdown and docs.

## v0.1.0(2018-8-16)

- Commonmark spec tests.
