"""
Some regex patterns
"""
import re

tags = [
    'address', 'article', 'aside', 'base', 'basefont', 'blockquote',
    'body', 'caption', 'center', 'col', 'colgroup', 'dd', 'details',
    'dialog', 'dir', 'div', 'dl', 'dt', 'fieldset', 'figcaption',
    'figure', 'footer', 'form', 'frame', 'frameset', 'h1', 'h2',
    'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hr', 'html', 'iframe',
    'legend', 'li', 'link', 'main', 'menu', 'menuitem', 'meta',
    'nav', 'noframes', 'ol', 'optgroup', 'option', 'p', 'param',
    'section', 'source', 'summary', 'table', 'tbody', 'td', 'tfoot',
    'th', 'thead', 'title', 'tr', 'track', 'ul'
]
tag_name = r'[A-Za-z][A-Za-z0-9\-]*'
attribute = (
    r' +[A-Za-z:_][A-Za-z0-9\-_\.:]*'
    r'(?: *= *(?:[^\s"\'`=<>]+|\'[^\']*\'|"[^"]*"))?'
)
attribute_no_lf = (
    r' +[A-Za-z:_][A-Za-z0-9\-_\.:]*'
    r'(?: *= *(?:[^\s"\'`=<>]+|\'[^\n\']*\'|"[^\n"]*"))?'
)
link_label = r'(?P<label>\[(?:\\\\|\\[\[\]]|[^\[\]])+\])'
link_dest = r'(?P<dest><(?:\\\\|\\[<>]|[^\s<>])*>|\S+)'
link_title = (r'(?P<title>"(?:\\\\|\\"|[^"])*"|\'(?:\\\\|\\\'|[^\'])*\''
              r'|\((?:\\\\|\\\)|[^\(\)])*\))')

link_dest_1 = re.compile(r'<(?:\\\\|\\[<>]|[^\s<>])*>')
whitespace = re.compile(r'\s+')
optional_label = re.compile(r'\[(?:\\\\|\\[\[\]]|[^\[\]])*\]')
