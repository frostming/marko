#! -*- coding: utf-8 -*-
"""
Inline(span) level elements
"""


_element_types = {}

__all__ = ('Literal',)


def add_element(element_type, override=False):
    """Add an inline element.

    :param element_type: the element type class.
    :param override: whether to replace the element type that bases.
    """
    if not override:
        _element_types[element_type.__name__] = element_type
    else:
        for cls in element_type.__bases__:
            if cls in _element_types.values():
                _element_types[cls.__name__] = element_type
                break
        else:
            _element_types[element_type.__name__] = element_type


def get_elements():
    return sorted(_element_types.items(), key=lambda e: e[1].priority, reverse=True)


_tags = [
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
_tag_name = r'[A-Za-z][A-Za-z0-9\-]*'
_attribute = r' +[A-Za-z:_][A-Za-z0-9\-_\.:]*(?: *= *(?:[^\s"\'`=<>]+|\'[^\']*\'|"[^"]*"))?'
_attribute_no_lf = r' +[A-Za-z:_][A-Za-z0-9\-_\.:]*(?: *= *(?:[^\s"\'`=<>]+|\'[^\n\']*\'|"[^\n"]*"))?'


class InlineElement(object):
    """Any inline element should inherit this class"""

    #: Use to denote the precedence in parsing
    priority = 5
    #: element regex patterns definition
    patterns = ()

    def __init__(self, match):
        """Parses the matched object into an element"""
        pass


class Literal(InlineElement):

    priority = 3
    patterns = (r'\\[!"#\$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]',)

    def __init__(self, match):
        self.children = _escape(match.group()[1:])


class HardBreak(InlineElement):

    priority = 2
    patterns = (r' {2,}\n',)


class Link(InlineElement):

    name = 'link'
    patterns = (
        r'\[([^\]]+)\]\(([^ ]+) "([^"]+)"\)',
        r'\[([^\]]+)\]\(([^\)]+)\)')

    @classmethod
    def parse(cls, match):
        groups = match.groups()
        content = {
            'text': groups[0],
            'link': groups[1]}

        try:
            content['title'] = groups[2]
        except IndexError:
            pass

        return content

    @classmethod
    def render(content, ctx):
        link = urlquote(clean_backslash(content['link']))
        if content.get('title'):
            title = _escape(clean_backslash(content['title']))
            return (
                '<a href="%s" title="%s">%s</a>'
                % (link, title, content['text'])
            )
        else:
            return (
                '<a href="%s">%s</a>'
                % (link, content['text'])
            )


class InlineHTML(InlineElement):

    priority = 7
    patterns = (
        r'<%s(?:%s)* */?>' % (_tag_name, _attribute),   # open tag
        r'</%s *>' % (_tag_name,),                      # closing tag
        r'<!--(?!>|->|[\s\S]*?--[\s\S]*?-->)[\s\S]*?-->',          # HTML comment
        r'<\?[\s\S]*?\?>',                              # processing instruction
        r'<![A-Z]+ +[\s\S]*?>',                         # declaration
        r'<!\[CDATA\[[\s\S]*?\]\]>'                     # CDATA section
    )

    def __init__(self, match):
        self.children = match.group(0)


class LinkRef(InlineElement):

    name = 'link_ref'

    @classmethod
    def parse(cls, match):
        groups = match.groups()
        return {
            'text': groups[0][1:-1],
            'ref': normalize_label((groups[1] or groups[0])[1:-1]),
            'full': match.group()
        }

    @classmethod
    def render(content, ctx):
        try:
            link, title = ctx['link_ref'][content['ref']]
        except KeyError:
            return '%(full)s' % content
        else:
            return Link.render(
                {'link': link,
                 'title': title,
                 'text': content['text']},
                ctx)


class DoubleEmphasis(InlineElement):

    name = 'double_emphasis'
    patterns = (
        r'\*\*[^ ](?:[^ ]+ \*\* )*[^\*]*\*\*',
        r'__[^ ](?:[^ ]+ __ )*[^_]*__')

    @classmethod
    def parse(cls, match):
        return {'text': match.group(0)[2:-2]}

    @classmethod
    def render(content, ctx):
        return '<strong>%(text)s</strong>' % content


class Emphasis(InlineElement):

    name = 'emphasis'
    patterns = (
        r'(?<!\\)(?:\*(?=\w)|(?<!\w)\*(?=[^*\s]))[\s\S]+'
        r'(?<!\\)(?:(?<=\w)\*|(?<=[^*\s])\*(?!\w))',
        r'(?<!\\)(?:(?<!\w)_(?=\w)|(?<!\w)_(?=[^_\s]))[\s\S]+'
        r'(?<!\\)(?:(?<=\w)_(?!\w)|(?<=[^_\s])_(?!\w))'
    )

    @classmethod
    def parse(cls, match):
        return {'text': match.group(0)[1:-1]}

    @classmethod
    def render(content, ctx):
        return '<em>%(text)s</em>' % content


class CodeSpan(InlineElement):

    name = 'code_span'
    patterns = (
        r'(?<!`)(`+)(?!`)([\s\S]+?)(?<!`)\1(?!`)',)

    @classmethod
    def parse(cls, match):
        return {'text': re.sub(r'\s+', ' ', match.group(2).strip())}

    @classmethod
    def render(content, ctx):
        return '<code>%(text)s</code>' % content


class Image(InlineElement):

    name = 'image'
    patterns = (
        r'!\[([^\]]+)\]\(([^ ]+) "([^"]+)"\)',
        r'!\[([^\]]+)\]\(([^\)]+)\)')

    @classmethod
    def parse(cls, match):
        groups = match.groups()
        content = {
            'text': groups[0],
            'link': groups[1]}

        try:
            content['title'] = groups[2]
        except IndexError:
            pass

        return content

    @classmethod
    def render(content, ctx):
        if 'title' in content:
            return (
                '<img src="%(link)s" '
                'title="%(title)s">%(text)s</img>' % content)
        else:
            return (
                '<img src="%(link)s">%(text)s</img>' % content)


class ImageRef(InlineElement):

    name = 'image_ref'
    patterns = (r'!\[([^\]]+)\] ?\[([^\]]+)\]',)

    @classmethod
    def parse(cls, match):
        return {
            'text': match.group(1),
            'ref': match.group(2)}

    @classmethod
    def render(content, ctx):
        try:
            link, title = ctx[content['ref']]
        except KeyError:
            return '%(text)s' % content
        else:
            return Image.render(
                {'link': link,
                 'title': title,
                 'text': content['text']},
                ctx)


class Url(InlineElement):

    name = 'url'
    patterns = (r'''https?:\/\/[^\s<]+[^<.,:;"')\]\s]''',)

    @classmethod
    def parse(cls, match):
        return {'link': match.group(0)}

    @classmethod
    def render(content, ctx):
        return Link.render(
            {'link': content['link'],
             'text': content['link']},
            ctx
        )


class AutoLink(InlineElement):

    name = 'auto_link'
    patterns = (r'<[^>]+>',)
    children = {}

    @classmethod
    def parse(cls, match):
        return {'link': match.group(0)[1:-1]}

    @classmethod
    def render(content, ctx):
        link = content['link']
        text = 'mailto:' + link if '@' in link else link
        return Link.render(
            {'link': link,
             'text': text},
            ctx)


def _escape(text):
    text = text.replace('&amp;', '&') \
               .replace('&', '&amp;')
    return text.replace('<', '&lt;') \
               .replace('>', '&gt;') \
               .replace('"', '&quot;')


class RawText(InlineElement):

    priority = 1

    def __init__(self, match):
        self.children = _escape(match.group())
