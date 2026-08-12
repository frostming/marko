# Marko Syntax Highlighting Demo

This document demonstrates how Marko's source mapping info can be used to
build a **syntax highlighter**. Every token below is colored by its element
type, using the `source_span` and `syntax_spans` attributes.

## Headings & emphasis

### Level three *with emphasis*

#### Level four with `inline code`

Setext heading
==============

Second level
------------

Text with *emphasis*, **strong emphasis**, ***both***, and ~~strikethrough~~
(GFM). Escaped characters like \*stars\* and \# hashes stay literal.

## Links, images & autolinks

Here is [a link](https://example.com), one [with a title](https://example.com "The title"),
and a [reference link][ref]. An image: ![Marko logo](https://example.com/logo.png "Logo").
Autolinks like <https://example.org> and email <me@example.com> work too.

[ref]: https://example.com/ref "Reference"

## Code

Inline code: use `marko.parse(text)` to get the AST, then check
`element.source_span`.

```python
import marko

doc = marko.parse("# Hello")
heading = doc.children[0]
print(heading.source_span)  # (0, 10)
```

    An indented code block looks like this one,
    and keeps its own color.

## Block quotes

> A block quote with *styled* content.
> It spans multiple lines.
>
> > And can be nested.

## Lists

- unordered item with `code`
- another item
  - nested item one
  - nested item two
- [x] a completed task
- [ ] a pending task

1. first ordered item
2. second ordered item
   1. nested ordered

## Tables (GFM)

| Name   | Price | Quantity |
| ------ | ----- | -------- |
| Apple  | $1    | 10       |
| Banana | $0.5  | 3        |

## Other blocks

---

Some <span style="color: red">raw HTML</span> inline, and a block below:

<div class="note">
  This is an HTML block.
</div>

> [!NOTE]
> GFM alert boxes are supported too.

A paragraph with a hard line break:  
and a soft line break
right here.
