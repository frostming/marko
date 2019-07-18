from marko.ext.gfm import GFMarkdown
from marko import Markdown
from marko.ast_renderer import ASTRenderer

a = '<blockquote>\n  <xmp> is disallowed.  <XMP> is also disallowed.\n</blockquote>\n'

print(GFMarkdown()(a))
