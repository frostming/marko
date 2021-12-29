"""
LaTeX renderer
"""
import logging
from typing import Iterable, List, Set, Union

from marko import Renderer

_logger = logging.getLogger(__name__)


class LatexRenderer(Renderer):
    """Render the parsed Markdown to LaTeX format."""

    packages: Set[str]
    _packages_back: Set[str]

    # Header levels that will be numbered. Default none.
    # It could be a list of header levels (ex. [1, 2]) or header names ['part', 'section']
    # TODO: add unit test
    numbered_headers: List[Union[int, str]]

    def __init__(self,
                 initial_packages: Iterable[str] = (),
                 numbered_headers: Iterable[Union[int, str]] = ()):

        super().__init__()
        self.packages = set(initial_packages)
        self.numbered_headers = list(numbered_headers)

    def __enter__(self):
        self._packages_back = self.packages.copy()
        return super().__enter__()

    def __exit__(self, *args):
        self.packages = self._packages_back
        super().__exit__(*args)

    def render_document(self, element):
        # should come first to collect needed packages
        children = self.render_children(element)
        # create document parts
        items = ["\\documentclass{article}"]
        # add used packages
        items.extend(f"\\usepackage{{{p}}}" for p in self.packages)
        # add inner content
        items.append(self._environment("document", children))
        return "\n".join(items)

    def render_paragraph(self, element):
        children = self.render_children(element)
        if element._tight:
            return children
        else:
            return f"{children}\n"

    def render_blank_line(self, element):
        return "\n"

    def render_line_break(self, element):
        if element.soft:
            return "\n"
        return "\\\\\n"

    def render_list(self, element):
        children = self.render_children(element)
        env = "enumerate" if element.ordered else "itemize"
        # TODO: check how to handle element.start with ordered list
        if element.start:
            _logger.warning("Setting the starting number of the list is not supported!")
        return self._environment(env, children)

    def render_list_item(self, element):
        children = self.render_children(element)
        return f"\\item {children}\n"

    def render_quote(self, element):
        self.packages.add("csquotes")
        children = self.render_children(element)
        return self._environment("displayquote", children)

    def render_fenced_code(self, element):
        self.packages.add("listings")
        language = self._escape_latex(element.lang)
        return self._environment("lstlisting", element.children[0].children, [f"language={language}"])

    def render_code_block(self, element):
        return self._environment("verbatim", element.children[0].children)

    def render_thematic_break(self, element):
        return "\\noindent\\rule{\\textwidth}{1pt}\n"

    def render_heading(self, element):
        children = self.render_children(element)
        headers = ["part", "section", "subsection", "subsubsection", "paragraph", "subparagraph"]
        header = headers[element.level - 1]
        if (element.level not in self.numbered_headers) and (header not in self.numbered_headers):
            header += "*"
        return f"\\{header}{{{children}}}\n"

    def render_setext_heading(self, element):
        return self.render_heading(element)

    def render_emphasis(self, element):
        children = self.render_children(element)
        return f"\\textit{{{children}}}"

    def render_strong_emphasis(self, element):
        children = self.render_children(element)
        return f"\\textbf{{{children}}}"

    def render_code_span(self, element):
        children = self._escape_latex(element.children)
        return f"\\texttt{{{children}}}"

    def render_link(self, element):
        if element.title:
            _logger.warning("Setting a title for links is not supported!")
        body = self.render_children(element)
        return f"\\href{{{element.dest}}}{{{body}}}"

    def render_auto_link(self, element):
        return f"\\url{{{element.dest}}}"

    def render_link_ref_def(self, element):
        return ""

    def render_image(self, element):
        self.packages.add("graphicx")
        # TODO: check how alt (element.children) and element.title could be used!
        return f"\\includegraphics{{{element.dest}}}"

    def render_html_block(self, element):
        _logger.warning("Rendering HTML is not supported!")
        return ""

    def render_inline_html(self, element):
        _logger.warning("Rendering HTML is not supported!")
        return ""

    def render_literal(self, element):
        return self.render_raw_text(element)

    def render_raw_text(self, element):
        return self._escape_latex(element.children)

    @staticmethod
    def _escape_latex(text: str) -> str:
        # Special LaTeX Character:  # $ % ^ & _ { } ~ \
        specials = {
            "#": "\\#",
            "$": "\\$",
            "%": "\\%",
            "&": "\\&",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "^": "\\^{}",
            "~": "\\~{}",
            "\\": "\\textbackslash{}",
        }

        return "".join(specials.get(s, s) for s in text)

    @staticmethod
    def _environment(env_name: str, content: str, options: Iterable[str] = ()) -> str:
        options_str = f"[{','.join(options)}]" if options else ""
        return f"\\begin{{{env_name}}}{options_str}\n{content}\\end{{{env_name}}}\n"
