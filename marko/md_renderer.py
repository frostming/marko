"""
Markdown renderer
"""
from contextlib import contextmanager

from .renderer import Renderer


class MarkdownRenderer(Renderer):
    """Render the AST back to markdown document.

    It is useful for, e.g. merging sections and formatting documents.
    For convenience, markdown renderer provides all render functions for basic elements
    and those from common extensions.
    """

    def __enter__(self):  # type: () -> Renderer
        self._prefix = ""
        self._second_prefix = ""
        return super().__enter__()

    @contextmanager
    def container(self, prefix, second_prefix=""):
        old_prefix = self._prefix
        old_second_prefix = self._second_prefix
        self._prefix += prefix
        self._second_prefix += second_prefix
        yield
        self._prefix = old_prefix
        self._second_prefix = old_second_prefix

    def render_paragraph(self, element):
        children = self.render_children(element)
        line = self._prefix + children + "\n"
        self._prefix = self._second_prefix
        return line

    def render_list(self, element):
        result = []
        if element.ordered:
            num = element.start
            for child in element.children:
                with self.container(f"{num}. ", " " * (len(str(num)) + 2)):
                    result.append(self.render(child))
        else:
            for child in element.children:
                with self.container(f"{element.bullet} ", "  "):
                    result.append(self.render(child))
        self._prefix = self._second_prefix
        return "".join(result)

    def render_list_item(self, element):
        return self.render_children(element)

    def render_quote(self, element):
        with self.container("> ", "> "):
            result = self.render_children(element)
        self._prefix = self._second_prefix
        return result + "\n"

    def render_fenced_code(self, element):
        extra = f" {element.extra}" if element.extra else ""
        lines = [self._prefix + f"```{element.lang}{extra}"]
        lines.extend(
            self._second_prefix + line
            for line in self.render_children(element).splitlines()
        )
        lines.append(self._second_prefix + "```")
        self._prefix = self._second_prefix
        return "\n".join(lines) + "\n"

    def render_code_block(self, element):
        indent = " " * 4
        lines = self.render_children(element).splitlines()
        lines = [self._prefix + indent + lines[0]] + [
            self._second_prefix + indent + line for line in lines[1:]
        ]
        self._prefix = self._second_prefix
        return "\n".join(lines) + "\n"

    def render_html_block(self, element):
        result = self._prefix + element.children + "\n"
        self._prefix = self._second_prefix
        return result

    def render_thematic_break(self, element):
        result = self._prefix + "* * *\n"
        self._prefix = self._second_prefix
        return result

    def render_heading(self, element):
        result = (
            self._prefix
            + "#" * element.level
            + " "
            + self.render_children(element)
            + "\n"
        )
        self._prefix = self._second_prefix
        return result

    def render_setext_heading(self, element):
        return self.render_heading(element)

    def render_blank_line(self, element):
        result = self._prefix + "\n"
        self._prefix = self._second_prefix
        return result

    def render_link_ref_def(self, element):
        return ""

    def render_emphasis(self, element):
        return f"*{self.render_children(element)}*"

    def render_strong_emphasis(self, element):
        return f"**{self.render_children(element)}**"

    def render_inline_html(self, element):
        return element.children

    def render_link(self, element):
        title = (
            ' "{}"'.format(element.title.replace('"', '\\"')) if element.title else ""
        )
        return f"[{self.render_children(element)}]({element.dest}{title})"

    def render_auto_link(self, element):
        return f"<{element.dest}>"

    def render_image(self, element):
        template = "![{}]({}{})"
        title = (
            ' "{}"'.format(element.title.replace('"', '\\"')) if element.title else ""
        )
        return template.format(self.render_children(element), element.dest, title)

    def render_literal(self, element):
        return "\\" + element.children

    def render_raw_text(self, element):
        return element.children

    def render_line_break(self, element):
        return "\n" if element.soft else "\\\n"

    def render_code_span(self, element):
        text = element.children
        if text and text[0] == "`" or text[-1] == "`":
            return f"`` {text} ``"
        return f"`{element.children}`"
