# -*- coding: utf-8 -*-

# Copyright (c) 2018 by Frost Ming.
# Modified under MIT license

# Copyright (c) 2017 by Esteban Castro Borsani.
# Released under MIT license

import re
import copy

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

BLOCK_ELEMENTS = 'BLOCK_ELEMENTS'
INLINE_ELEMENTS = 'INLINE_ELEMENTS'
LIST_ELEMENTS = 'LIST_ELEMENTS'
RAW_TEXT = 'RAW_TEXT'

_block_tag = ['address', 'article', 'aside', 'base', 'basefont', 'blockquote',
              'body', 'caption', 'center', 'col', 'colgroup', 'dd', 'details',
              'dialog', 'dir', 'div', 'dl', 'dt', 'fieldset', 'figcaption',
              'figure', 'footer', 'form', 'frame', 'frameset', 'h1', 'h2',
              'h3', 'h4', 'h5', 'h6', 'head', 'header', 'hr', 'html', 'iframe',
              'legend', 'li', 'link', 'main', 'menu', 'menuitem', 'meta',
              'nav', 'noframes', 'ol', 'optgroup', 'option', 'p', 'param',
              'section', 'source', 'summary', 'table', 'tbody', 'td', 'tfoot',
              'th', 'thead', 'title', 'tr', 'track', 'ul']
_block_tag = r'(?:%s)' % ('|'.join(_block_tag),)
_tag_name = r'[A-Za-z][A-Za-z0-9\-]*'
_attribute = r' +[A-Za-z:_][A-Za-z0-9\-_\.:]*(?: *= *(?:[^\s"\'`=<>]+|\'[^\']*\'|"[^"]*"))?'
_attribute_no_lf = r' +[A-Za-z:_][A-Za-z0-9\-_\.:]*(?: *= *(?:[^\s"\'`=<>]+|\'[^\n\']*\'|"[^\n"]*"))?'
_link_label = r'\[(?! *\])(?:\\\\|\\\[|\\\]|[^\[\]])+?\]'
_b_paren = r'\((?:\w|\\\\|\\\(|\\\)|[^()])*?\)'
_b_paren_2 = r'\((?:\w|\\\\|\\\(|\\\)|%s)*?\)' % _b_paren
_b_paren_3 = r'\((?:\w|\\\\|\\\(|\\\)|%s)*?\)' % _b_paren_2
_link_dest = r'<(?:\\\\|\\<|\\>|[^\s<>])*?>|(?:\S|\\\\|\\\(|\\\)|%s)+' % _b_paren_3
_link_title = r'"(?:\\\\|\\"|(?!\n\n)[^"])*?"|\'(?:\\\\|\\\'|(?!\n\n)[^\'])*?\'|\((?:\\\\|\\\)|(?!\n\n)[^()])*?\)'
_lazy_para = r'(?: {,3}(?:> ?|[*\-+] |\d+\. ))* {,3}(?!#{1,6} |%s|%s|%s).+?$\n?[\s\S]*?(?={,3}(?:#{1,6} |%s|%s|%s)'


def dedent(text, prefix):
    return re.sub('^{}'.format(prefix), '', text, flags=re.M)


def clean_block(text):
    """remove the optional tailing blank lines"""
    return re.sub(r'\n+\Z', '\n', text)


def normalize_label(label):
    return re.sub(r'\s+', ' ', label.strip().lower())


def clean_backslash(text):
    return re.sub(r'\\[!"#\$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]', lambda m: m.group()[1:], text)


def urlquote(text):
    return re.sub(r'[^a-zA-Z0-9_!#\$%&\?+\-*/\.:;~()]', lambda m: quote(m.group()), text)


class Element:

    #: Element name, elements with the same name can't coexist.
    name = ''
    #: Regex patterns for the element.
    patterns = ()
    #: Children element type map.
    children = {}

    @staticmethod
    def parse(match, ctx):
        """Parse the match object passed in as structured result.

        :param match: the regex match object returned by re.Scanner.
        :param ctx: the context dictionary.
        :returns: a structured result representing the AST.
        :rtype: dict
        """
        raise NotImplementedError

    @staticmethod
    def render(content, ctx):
        """Render the structured result as HTML text.

        :param content: the structured result returned by ``parse``
        :param ctx: the context dictionary.
        :returns: the HTML text of the element.
        :rtype: str
        """
        raise NotImplementedError

    @staticmethod
    def post_parse(node, parent_ctx, ctx):
        """Extra operates the parsed result and return the new parsed result.

        :param node: the ``(name, content)`` tuple representing the current element.
        :param parent_ctx: some context related to parent element.
        :param ctx: the global context dictionary.
        :returns: ``(new node, current_ctx)``
        """
        return node, {}

    @staticmethod
    def continue_paragraph(match, ctx, ast):
        """Called when the last element is a paragraph.

        :param match: the regex match object returned by re.Scanner.
        :param ctx: the context dictionary.
        :param ast: the current AST.
        :returns: ``True`` indicates the paragraph is continued and prevents further parsing.
            ``False`` indicates the paragraph is not continued and closed.
        """
        return False


class BlankLine(Element):
    name = 'blank_line'
    patterns = (r'\n+',)
    children = {}

    @staticmethod
    def parse(match, ctx):
        return {}

    @staticmethod
    def render(content, ctx):
        return ''


class BlockHTML(Element):

    name = 'block_html'
    patterns = (
        r'^ {,3}<(?:script|pre|style)(?: *|>|$)[\s\S]*?(?:</(?:script|pre|style)>.*?$\n?|\Z)',   # type 1
        r'^ {,3}<!--[\s\S]*?(?:-->.*?$\n?|\Z)',     # type 2
        r'^ {,3}<\?[\s\S]*?(?:\?>.*?$\n?|\Z)',      # type 3
        r'^ {,3}<![A-Z][\s\S]*?(?:>.*?$\n?|\Z)',    # type 4
        r'^ {,3}<!\[CDATA\[[\s\S]*?(?:\]\]>.*?$\n?|\Z)',   # type 5
        r'^ {,3}</?%s(?: +|/?>|$)[\s\S]*?(?:\n{2,}|\Z)' % _block_tag,     # type 6
        (r'^ {,3}(<(?!script|pre|style)%(tag)s(?:%(attr)s)* */?>'
         r'|</(?!script|pre|style)%(tag)s *>) *$[\s\S]*?(?=\n{2,}|\Z)')
        % {'tag': _tag_name, 'attr': _attribute_no_lf}   # type 7
    )
    _pattern = r'(?:{})'.format('|'.join(patterns))
    children = {}

    @staticmethod
    def continue_paragraph(match, ctx, ast):
        if len(match.groups()) > 0:     # type 7
            ctx['last_paragraph']['text'] += match.group()
            return True
        else:
            return False

    @staticmethod
    def parse(match, ctx):
        return {'text': clean_block(match.group(0))}

    @staticmethod
    def render(content, ctx):
        return content['text'].rstrip('\n') + '\n'


class Code(Element):

    name = 'code'
    patterns = (r'^ {4}[^\n]+$\n?(?:^ {4}[^\n]+$\n?|\n+(?= {4}))*',)
    children = {'text': RAW_TEXT}

    @staticmethod
    def continue_paragraph(match, ctx, ast):
        ctx['last_paragraph']['text'] += match.group()
        return True

    @staticmethod
    def parse(match, ctx):
        return {'text': dedent(match.group(), ' {4}')}

    @staticmethod
    def render(content, ctx):
        return '<pre><code>%(text)s</code></pre>\n' % content


class Fenced(Element):
    name = 'fenced'
    patterns = (
        r'^( {,3})(`{3,})([^`]*?)$\n?([\s\S]*?)(?:^ {,3}\2`* *$\n?|\Z)',
        r'^( {,3})(~{3,})([^~]*?)$\n?([\s\S]*?)(?:^ {,3}\2~* *$\n?|\Z)'
    )
    _pattern = r'^ {,3}(?:`{3,}[^`]*?$|~{3,}[^~]*?$)'
    children = {'text': RAW_TEXT}

    @staticmethod
    def parse(match, ctx):
        indent = len(match.group(1))
        content = {'text': dedent(match.group(4), r' {,%d}' % indent)}
        info_string = match.group(3).strip()
        if info_string:
            content['lang'] = info_string.split()[0]
        return content

    @staticmethod
    def render(content, ctx):
        if content.get('lang'):
            return '<pre><code class="language-%(lang)s">%(text)s</code></pre>\n' % content
        else:
            return '<pre><code>%(text)s</code></pre>\n' % content


class Setext(Element):
    name = 'setext'
    patterns = (
        r'((?:[^\n]+\n)+?) {0,3}(=+) *$\n?',
        r'((?:[^\n]+\n)+?) {0,3}(\-+) *$\n?'
    )
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def continue_paragraph(match, ctx, ast):
        if match.group(2)[0] == '=' or len(match.group(2)) < 3:
            ctx['last_paragraph']['text'] += match.group()
        else:
            ctx['last_paragraph']['text'] += match.group(1)
            ast.append((HRule.name, {}))
        return True

    @staticmethod
    def parse(match, ctx):
        title = match.group(1)
        if match.group(2)[0] == '=':
            level = 1
        else:
            level = 2
        return {'text': title, 'level': level}

    @staticmethod
    def render(content, ctx):
        return '<h%(level)s>%(text)s</h%(level)s>\n' % content


class Header(Element):

    name = 'header'
    patterns = (r'^ {0,3}(#{1,6})( [^\n]*?| *)(?:(?<= )(?<!\\)#+)? *$\n?',)
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        groups = match.groups()
        title = (
            groups[1]
            .lstrip(' ')
            .rstrip())
        level = len(groups[0])

        return {
            'text': title,
            'level': level,
        }

    @staticmethod
    def render(content, ctx):
        return '<h%(level)s>%(text)s</h%(level)s>\n' % content


class Quote(Element):

    name = 'quote'
    patterns = (r'(?:^ {,3}>[^\n]+$\n?)+',)
    children = {'text': BLOCK_ELEMENTS}
    _quote_sub_pattern = re.compile(r'^ {,3}> ?', flags=re.M)

    @staticmethod
    def parse(match, ctx):
        return {
            'text': Quote
            ._quote_sub_pattern
            .sub('', match.group()),
        }

    @staticmethod
    def render(content, ctx):
        return '<blockquote>\n%(text)s</blockquote>\n' % content


class HRule(Element):

    name = 'h_rule'
    patterns = (r'^ {0,3}(?:(?:\* *){3,}|(?:- *){3,}|(?:_ *){3,}) *$\n?',)
    children = {}

    @staticmethod
    def parse(match, ctx):
        return {}

    @staticmethod
    def render(content, ctx):
        return '<hr />\n'


class ListItem(Element):

    name = 'list_item'
    patterns = (
        (r'^( {,3})([*\-+])(?:( {1,3}?)(?= {4}|\S)[^\n]*| *)$\n?'
         r'(?:\n*\1 (?(3)\3| )[^\n]*$\n?)*'),
        (r'^( {,3})(\d(\d)?\.)(?:( {1,3}?)(?= {4}|\S)[^\n]*| *)$\n?'
         r'(?:\n*\1 (?(3) ) (?(4)\4| )[^\n]*$\n?)*')
    )
    children = {'text': BLOCK_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        splitter_group = 4 if match.group(2)[0].isdigit() else 3
        try:
            indent = len(''.join(match.group(1, 2, splitter_group)))
        except TypeError:
            indent = len(''.join(match.group(1, 2))) + 1
        parts = match.group(0).split('\n', 1)
        if len(parts) == 1:
            first, rest = parts[0], ''
        else:
            first, rest = parts
        text = '\n'.join([first[indent:], dedent(rest, ' {%d}' % indent)])
        return {'text': text}

    @staticmethod
    def render(content, ctx):
        return '<li>%s</li>\n' % content['text'].rstrip('\n')

    @staticmethod
    def post_parse(node, parent_ctx, ctx):
        return node, {'tight': parent_ctx['tight']}


class List(Element):

    name = 'list'
    patterns = (
        (r'^( {,3})([*\-+])(?:( {1,3}?)(?= {4}|\S)[^\n]*| *)$\n?'
         r'(?:\n*\1 (?(3)\3| )[^\n]*$\n?)*'
         r'(?:^( {,3})(?!(?:(?:\* *){3,}|(?:- *){3,}) *$)'      # exclude hrule
         r'\2(?:( {1,3}?)(?= {4}|\S)[^\n]*| *)$\n?'
         r'(?:\n*\4 (?(5)\5| )[^\n]*$\n?)*)*'),
        (r'(?:^( {,3})(\d(\d)?\.)(?:( {1,3}?)(?= {4}|\S)[^\n]*| *)$\n?'
         r'(?:\n*\1 (?(3) ) (?(4)\4| )[^\n]*$\n?)*)+')
    )
    children = {'text': LIST_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        content = {'text': match.group(0)}
        bullet = match.group(2)
        if '.' in bullet:
            content['type'] = 'ordered'
            content['start'] = int(bullet[:-1])
        else:
            content['type'] = 'unordered'
        return content

    @staticmethod
    def render(content, ctx):
        if content['type'] == 'ordered':
            if content['start'] != 1:
                return '<ol start="%(start)s">\n%(text)s\n</ol>' % content
            return '<ol>\n%(text)s</ol>\n' % content
        return '<ul>\n%(text)s</ul>\n' % content

    @staticmethod
    def _has_loose_item(parsed):
        """Check if the list has loose item"""
        token, children = parsed
        for tok, item_children in children['text']:
            for child_tok, child in item_children['text']:
                if child_tok == BlankLine.name:
                    return True
        return False

    @staticmethod
    def post_parse(node, parent_ctx, ctx):
        return node, {'tight': not List._has_loose_item(node)}


class LinkRefLabel(Element):

    name = 'link_ref_label'
    patterns = (
        r'^ {,3}(%s): *\n? *(%s)( *\n? *(?<=\s)(?:%s))? *$\n?'
        % (_link_label, _link_dest, _link_title),
    )
    children = {}

    @staticmethod
    def continue_paragraph(match, ctx, ast):
        ctx['last_paragraph']['text'] += match.group()
        return True

    @staticmethod
    def parse(match, ctx):
        label = normalize_label(match.group(1)[1:-1])
        description = match.group(2)
        if description[0] == '<':
            description = description[1:-1]
        title = match.group(3).strip()[1:-1] if match.group(3) else ''
        refs = ctx.setdefault('link_ref', {})
        if label not in refs:
            refs[label] = (description, title)
        return {}

    @staticmethod
    def render(content, ctx):
        return ''


class Paragraph(Element):

    name = 'paragraph'
    patterns = (r'^ {,3}[^\n]+$\n?',)
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def continue_paragraph(match, ctx, ast):
        ctx['last_paragraph']['text'] += match.group()
        return True

    @staticmethod
    def parse(match, ctx):
        content = {'text': match.group(0), 'parse_children_later': True}
        ctx['last_paragraph'] = content
        return content

    @staticmethod
    def post_parse(node, parent_ctx, ctx):
        tok, content = node
        content['tight'] = parent_ctx.get('tight', False)
        return (tok, content), {}

    @staticmethod
    def render(content, ctx):
        text = content['text']
        if content['tight']:
            return text
        return '<p>%s</p>\n' % text


class Literal(Element):

    name = 'literal'
    patterns = (r'\\[!"#\$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]',)
    children = {'text': RAW_TEXT}

    @staticmethod
    def parse(match, ctx):
        return {'text': match.group()[1:]}

    @staticmethod
    def render(content, ctx):
        return content['text']


class HardBreak(Element):

    name = 'hard_break'
    patterns = (r' {2,}\n',)
    children = {}

    @staticmethod
    def parse(match, ctx):
        return {}

    @staticmethod
    def render(content, ctx):
        return '<br />'


class Link(Element):

    name = 'link'
    patterns = (
        r'\[([^\]]+)\]\(([^ ]+) "([^"]+)"\)',
        r'\[([^\]]+)\]\(([^\)]+)\)')
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        groups = match.groups()
        content = {
            'text': groups[0],
            'link': groups[1]}

        try:
            content['title'] = groups[2]
        except IndexError:
            pass

        return content

    @staticmethod
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


class InlineHTML(Element):

    name = 'inline_html'
    patterns = (
        r'<%s(?:%s)* */?>' % (_tag_name, _attribute),   # open tag
        r'</%s *>' % (_tag_name,),                      # closing tag
        r'<!--(?!>|->|[\s\S]*?--[\s\S]*?-->)[\s\S]*?-->',          # HTML comment
        r'<\?[\s\S]*?\?>',                              # processing instruction
        r'<![A-Z]+ +[\s\S]*?>',                         # declaration
        r'<!\[CDATA\[[\s\S]*?\]\]>'                     # CDATA section
    )
    children = {}

    @staticmethod
    def parse(match, ctx):
        return {'html': match.group(0)}

    @staticmethod
    def render(content, ctx):
        return content['html']


class LinkRef(Element):

    name = 'link_ref'
    patterns = (r'(%s)(%s)?' % (_link_label, _link_label),)
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        groups = match.groups()
        return {
            'text': groups[0][1:-1],
            'ref': normalize_label((groups[1] or groups[0])[1:-1]),
            'full': match.group()
        }

    @staticmethod
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


class DoubleEmphasis(Element):

    name = 'double_emphasis'
    patterns = (
        r'\*\*[^ ](?:[^ ]+ \*\* )*[^\*]*\*\*',
        r'__[^ ](?:[^ ]+ __ )*[^_]*__')
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        return {'text': match.group(0)[2:-2]}

    @staticmethod
    def render(content, ctx):
        return '<strong>%(text)s</strong>' % content


class Emphasis(Element):

    name = 'emphasis'
    patterns = (
        r'(?<!\\)(?:\*(?=\w)|(?<!\w)\*(?=[^*\s]))[\s\S]+'
        r'(?<!\\)(?:(?<=\w)\*|(?<=[^*\s])\*(?!\w))',
        r'(?<!\\)(?:(?<!\w)_(?=\w)|(?<!\w)_(?=[^_\s]))[\s\S]+'
        r'(?<!\\)(?:(?<=\w)_(?!\w)|(?<=[^_\s])_(?!\w))'
    )
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        return {'text': match.group(0)[1:-1]}

    @staticmethod
    def render(content, ctx):
        return '<em>%(text)s</em>' % content


class CodeSpan(Element):

    name = 'code_span'
    patterns = (
        r'(?<!`)(`+)(?!`)([\s\S]+?)(?<!`)\1(?!`)',)
    children = {'text': RAW_TEXT}

    @staticmethod
    def parse(match, ctx):
        return {'text': re.sub(r'\s+', ' ', match.group(2).strip())}

    @staticmethod
    def render(content, ctx):
        return '<code>%(text)s</code>' % content


class Image(Element):

    name = 'image'
    patterns = (
        r'!\[([^\]]+)\]\(([^ ]+) "([^"]+)"\)',
        r'!\[([^\]]+)\]\(([^\)]+)\)')
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        groups = match.groups()
        content = {
            'text': groups[0],
            'link': groups[1]}

        try:
            content['title'] = groups[2]
        except IndexError:
            pass

        return content

    @staticmethod
    def render(content, ctx):
        if 'title' in content:
            return (
                '<img src="%(link)s" '
                'title="%(title)s">%(text)s</img>' % content)
        else:
            return (
                '<img src="%(link)s">%(text)s</img>' % content)


class ImageRef(Element):

    name = 'image_ref'
    patterns = (r'!\[([^\]]+)\] ?\[([^\]]+)\]',)
    children = {'text': INLINE_ELEMENTS}

    @staticmethod
    def parse(match, ctx):
        return {
            'text': match.group(1),
            'ref': match.group(2)}

    @staticmethod
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


class Url(Element):

    name = 'url'
    patterns = (r'''https?:\/\/[^\s<]+[^<.,:;"')\]\s]''',)

    @staticmethod
    def parse(match, ctx):
        return {'link': match.group(0)}

    @staticmethod
    def render(content, ctx):
        return Link.render(
            {'link': content['link'],
             'text': content['link']},
            ctx
        )


class AutoLink(Element):

    name = 'auto_link'
    patterns = (r'<[^>]+>',)
    children = {}

    @staticmethod
    def parse(match, ctx):
        return {'link': match.group(0)[1:-1]}

    @staticmethod
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


class RawText(Element):

    name = 'raw_text'
    children = {}

    @staticmethod
    def parse(hole, ctx):
        return {'text': hole}

    @staticmethod
    def render(content, ctx):
        return _escape(content['text'])


DEFAULT_ELEMENTS = {
    element.name: element
    for element in (
        BlockHTML,
        BlankLine,
        Fenced,
        Header,
        Setext,
        Quote,
        HRule,
        List,
        ListItem,
        Code,
        LinkRefLabel,
        Paragraph,
        Literal,
        Link,
        Url,
        InlineHTML,
        LinkRef,
        DoubleEmphasis,
        Emphasis,
        CodeSpan,
        Image,
        ImageRef,
        HardBreak,
        AutoLink)}
DEFAULT_ELEMENTS[None] = RawText


def default_elements():
    return DEFAULT_ELEMENTS.copy()


DEFAULT_CHILDREN = {
    BLOCK_ELEMENTS: [
        Code,
        HRule,
        Fenced,
        Header,
        BlankLine,
        Quote,
        List,
        LinkRefLabel,
        BlockHTML,
        Setext,
        Paragraph],
    INLINE_ELEMENTS: [
        Literal,
        InlineHTML,
        Link,
        Url,
        LinkRef,
        DoubleEmphasis,
        Emphasis,
        CodeSpan,
        Image,
        ImageRef,
        HardBreak,
        AutoLink],
    LIST_ELEMENTS: [ListItem, Paragraph],
    RAW_TEXT: [RawText]}


def default_children():
    return copy.deepcopy(DEFAULT_CHILDREN)
