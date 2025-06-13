## v2.1.4(2025-06-13)

### Fixed

- Correct the parsing of LinkRefDef if it is the last line but doesn't end with a line break.

## v2.1.3(2025-04-05)

### Fixed

- Fix a recursion error when dispatching render methods in extensions.
- Initialize `children` attribute when creating a `Document` instance.

## v2.1.2(2024-06-21)

### Changed

- Update the GFM spec to the latest master branch.
- Update the CommonMark spec to 0.31.2.

## v2.1.1(2024-06-19)

### Fixed

- Reference link will not render if the reference definition doesn't end with newline.

## v2.1.0(2024-06-13)

### Changed

- Drop support of Python 3.7.

## v2.0.3(2024-02-22)

- Add pretty representation for the AST for debugging purpose. An extra group `repr` is added for more readable output.
- Make a dummy `Document` element if the element to render is not a `Document` instance.

## v2.0.2(2023-11-16)

### Fixed

- Rewrite the parsing logic of GFM tables.
- Fixed the dispatching among different renderers for render methods in extensions. Now the GFM renderer supports `MarkdownRenderer`.

## v2.0.1(2023-10-23)

### Fixed

- Preserve link references when rendering document as Markdown.

### Documentation

- Fix the sidebar warning in shibuya theme.

## v2.0.0(2023-06-12)

### Changed

- Avoid saving to global variables during parsing. There can be multiple parsers running in parallel.
- Now the `children` attribute for block elements should be a list of child elements.
- Move the HTML content of `HTMLBlock` from `children` to `body` attribute.
- Fixed some built-in extensions that modify class attributes.
- Add a helper class to create extensions, instead of using arbitrary objects to hold partial properties.

### Fixed

- Call `setup_extensions()` when running `render()` method alone.

## v1.3.1(2023-06-09)

### Fixed

- Fix the unpack error when parsing a fenced code block with `codehilite` extension enabled.

## v1.3.0(2023-01-28)

- Fix a bug that `Parser.parse_inline()` cannot be called without preceding call of `Parser.parse()`. [#131](https://github.com/frostming/marko/issue/131)
- Fix a rendering bug when line breaks exist in a link text. [#126](https://github.com/frostming/marko/issue/126)
- Drop support of Python 3.6.
- Update the GFM spec to the latest master branch.
- Fix a precedence issue of parsing strikethroughs in GFM.

## v1.2.2(2022-09-22)

- Fix a bug of markdown renderer, the ordered list index isn't increasing. [#112](https://github.com/frostming/marko/pull/112)
- Fix a crash issue when parsing a list item with NBSP in preceding spaces. [#123](https://github.com/frostming/marko/pull/123)
- Fix a hanging issue when parsing a text with nested brackets. [#124](https://github.com/frostming/marko/pull/124)

## v1.2.1(2022-05-12)

- Fix a bug that tabs between the list bullet and item are not expanded properly.
- Upgrade from type comments to Py 3.5+ style annotations.

## v1.2.0(2022-01-04)

- Forbid delegation to element-specific render methods for AST renderers.
- Add LaTeX renderer to the `marko.ext` namespace.

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
