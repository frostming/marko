"""
Tests for the Gemtext renderer.
"""
from marko import Markdown
from marko.ext.gemtext_renderer import GemtextRenderer


def test_gemtext_renderer() -> None:
    """
    Test ``GemtextRenderer``.
    """
    double_space = "  "

    gemini = Markdown(renderer=GemtextRenderer)

    assert (
        gemini.convert(
            f"""
# Header 1

## Header 2

### Header 3

#### Header 4

- Mercury
- Gemini
  - Apollo

> This is{double_space}
> A multiline{double_space}
> blockquote{double_space}

*This* is a **paragraph**. With `code`.

This is an [inline link](https://example.com/). This is [another](https://example.org/).

```
This is some code.
```

End.
""",
        )
        == f"""
# Header 1

## Header 2

### Header 3

### Header 4

* Mercury
* Gemini
* Apollo

> This is
> A multiline
> blockquote{double_space}

This is a paragraph. With code.

This is an inline link. This is another.

=> https://example.com/ inline link
=> https://example.org/ another

```
This is some code.
```

End.
"""
    )


def test_gemini_renderer_link_ref_def() -> None:
    """
    Test rendering a link definition reference.
    """
    gemini = Markdown(renderer=GemtextRenderer)

    assert (
        gemini.convert(
            """
Hi, here's my [thing that I just casually mention][tt] sometimes.

[tt]: gemini://my.boring/url "I like this link"
            """,
        )
        == """
Hi, here's my thing that I just casually mention sometimes.

=> gemini://my.boring/url I like this link


"""
    )


def test_gemini_renderer_links() -> None:
    """
    Test rendering links.
    """
    gemini = Markdown(renderer=GemtextRenderer)
    assert (
        gemini.convert(
            """
This is a paragraph with [a link](https://example.com/). It is a good paragraph.

This one [also has a link](https://example.net/). It also has some *emphasis* and **bold**.

And this one is a special paragraph because it has not just [one](https://example.com/one),
but [two](https://example.com/two) links. That is quite a lot.

This other paragraph also has [a link][ref], using a reference. It's very fancy.

[ref]: https://example.org/foo "This is foo"

This one has an auto link <https://example.com/autolink>.

That is it.
            """,
        )
        == """
This is a paragraph with a link. It is a good paragraph.

=> https://example.com/ a link

This one also has a link. It also has some emphasis and bold.

=> https://example.net/ also has a link

And this one is a special paragraph because it has not just one,
but two links. That is quite a lot.

=> https://example.com/one one
=> https://example.com/two two

This other paragraph also has a link, using a reference. It's very fancy.

=> https://example.org/foo This is foo


This one has an auto link https://example.com/autolink.

=> https://example.com/autolink https://example.com/autolink

That is it.

"""
    )


def test_gemini_renderer_padding_after_link_ref_def() -> None:
    """
    Test the padding after a link reference definition.

    Ideally we shouldn't be left with an empty line.
    """
    gemini = Markdown(renderer=GemtextRenderer)
    assert (
        gemini.convert(
            """
This other paragraph also has [a link][ref], using a reference. It's very fancy.

[ref]: https://example.org/foo "This is foo"

That is it.
""",
        )
        == """
This other paragraph also has a link, using a reference. It's very fancy.

=> https://example.org/foo This is foo


That is it.
"""
    )


def test_gemini_renderer_image() -> None:
    """
    Test rendering images.
    """
    gemini = Markdown(renderer=GemtextRenderer)
    assert (
        gemini.convert(
            """
This is a paragraph.

![Alt text](https://assets.digitalocean.com/articles/alligator/boo.svg "a title")

![Alt text](https://assets.digitalocean.com/articles/alligator/boo.svg)

That is it.
""",
        )
        == """
This is a paragraph.

=> https://assets.digitalocean.com/articles/alligator/boo.svg a title

=> https://assets.digitalocean.com/articles/alligator/boo.svg Alt text

That is it.
"""
    )
