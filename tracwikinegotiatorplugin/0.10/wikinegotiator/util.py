# -*- coding: utf-8 -*-
# Utility functions which does not depends on trac and negotiator.

import re

__all__ = ['split_lang', 'make_page_name', 'get_preferred_langs',
           'make_lang_list']

_re_page = re.compile(r'(.*)(?:\.([a-z][a-z](?:-[a-z][a-z])?))$')

_re_arg_lang = re.compile(r'^(?P<lang>[a-z]{1,8}(?:[-_][a-z]{1,8})?)$')

_re_accept_lang = re.compile(r'^(?P<lang>[a-z]{1,8}(?:[-_][a-z]{1,8})?|\*)'
                             +'(?:;\s*q=(?P<q>[0-9.]+))?$')

def split_lang(page, lang=None):
    """Split page body name and suffixed language code from
    requested page name.
    The separator for suffix is '.' and multiple separators will be removed.

    >>> split_lang('sub/pagename.ja')       # suffixed explicitly
    ('sub/pagename', 'ja')
    >>> split_lang('sub/pagename.ja-jp')
    ('sub/pagename', 'ja-jp')
    >>> split_lang('sub/pagename')          # no suffix, negotiatable
    ('sub/pagename', None)
    >>> split_lang('sub/pagename', 'en')    # with default lang
    ('sub/pagename', 'en')
    >>> split_lang('sub/pagename.ja', 'en') # suffixed page with default
    ('sub/pagename', 'ja')
    >>> split_lang('sub/pagename.')         # default page without negotiation
    ('sub/pagename', '')
    >>> split_lang('sub/pagename..')        # same above with removing all dots
    ('sub/pagename', '')
    >>> split_lang('sub/pagename..ja')      # dots should be removed
    ('sub/pagename', 'ja')
    >>> split_lang('sub/pagename.ja.en')    # not valid, but parsable
    ('sub/pagename.ja', 'en')
    """
    m = _re_page.match(page)
    if m:
        return (m.group(1).rstrip('.'), m.group(2)) # with lang suffix
    elif page.endswith('.'):
        return (page.rstrip('.'), '')         # without lang suffix
    else:
        return (page.rstrip('.'), lang)         # without lang suffix


def make_page_name(base, lang=None):
    """Make wiki page name with specified language suffix.
    if `lang` is None, '' or 'default', return base page name wihtout suffix.
    Else add suffix to the base name.
    We do not care about whether `base` has suffix.

    >>> make_page_name('Foo')
    'Foo'
    >>> make_page_name('Foo', None)
    'Foo'
    >>> make_page_name('Foo', '')
    'Foo'
    >>> make_page_name('Foo', 'default')
    'Foo'
    >>> make_page_name('Foo', 'ja')
    'Foo.ja'
    >>> make_page_name('Foo.en')
    'Foo.en'
    >>> make_page_name('Foo.en', 'ja')
    'Foo.en.ja'
    """
    if not lang or lang == 'default':
        return base
    else:
        return '%s.%s' % (base, lang)

def get_preferred_langs(req, default_lang=''):
    """Get preferred lang names from http request.
    The languages are extracted from 'Accept-Language' in header.
    If session has value 'wiki_lang', its value is used as most
    preferred languge.

    >>> req = Req()
    >>> req.headers['accept-language'] = 'ja,en-us;q=0.8,en;q=0.2'
    >>> get_preferred_langs(req)
    ['ja', 'en-us', 'en']
    >>> req.session['wiki_lang'] = 'fr'         # selected lang
    >>> get_preferred_langs(req)                # it goes top of candidates
    ['fr', 'ja', 'en-us', 'en']
    >>> req.session['wiki_lang'] = 'en'         # selected lang is existing
    >>> get_preferred_langs(req)                # it goes top of candidates
    ['en', 'ja', 'en-us']
    >>> req.args['lang'] = 'de'                # selected lang in args
    >>> get_preferred_langs(req)               # it cause no other candidates
    ['de']

    Invalid lang values should be ignored
    
    >>> req.args['lang'] = '../../abc'          # insecure lang
    >>> get_preferred_langs(req)                # should be ignored
    []
    """
    # decide by language denotation in url parameter: '?lang=xx'
    if req.args.has_key('lang'):
        lang = req.args['lang']
        if _re_arg_lang.match(lang):
            req.session['wiki_lang'] = lang
            return [lang]
        else:
            # bad lang keyword should be ignored for security reason
            return []
    # otherwise, decide by http Accept-Language: header
    langs = _parse_langs(req.get_header('accept-language')
                         or default_lang)
    if default_lang and default_lang not in langs:
        langs.append(default_lang)              # fallback language
    selected = req.session.get('wiki_lang', None)
    if selected:
        if selected in langs:
            langs.remove(selected)
        langs.insert(0, req.session.get('wiki_lang'))
    return langs


def _parse_langs(al):
    """Make list of language tag in preferred order.
    For example,
    Accept-Language: ja,en-us;q=0.8,en;q=0.2
    or
    Accept-Language: en;q=0.2,en-us;q=0.8,ja
    results ['ja', 'en-us', 'en']

    >>> _parse_langs('ja,en-us;q=0.8,en;q=0.2')
    ['ja', 'en-us', 'en']
    >>> _parse_langs('en;q=0.2,en-us;q=0.8,ja')
    ['ja', 'en-us', 'en']
    """
    infos = []
    for item in al.split(','):
        m = _re_accept_lang.match(item.strip())
        if m:
            lang, q = m.groups()
            infos.append((lang, float(q or '1.0')))
    # sort by quality descendant
    infos.sort(lambda x,y: cmp(y[1], x[1]))
    return [info[0] for info in infos] # returns list of lang string


def make_lang_list(pages):
    """Make sorted list of lang suffixes from given page names.

    >>> make_lang_list(['Foo'])
    []
    >>> make_lang_list(['Foo', 'Foo.ja'])
    ['ja']
    >>> make_lang_list(['Foo', 'Foo.ja', 'Foo.en'])
    ['en', 'ja']
    >>> make_lang_list(['Foo', 'Foo.ja', 'Foo.en', 'Bar.en'])
    ['en', 'ja']
    >>> make_lang_list(['Foo', 'Foo.ja', 'Foo.en', 'Bar.en-us'])
    ['en', 'en-us', 'ja']
    >>> make_lang_list(['Foo', 'Foo.ja', 'Foo.en', 'Bar.bad-lang'])
    ['en', 'ja']
    """
    langs = []
    for page in pages:
        name, lang = split_lang(page)
        if lang and lang not in langs:
            langs.append(lang)
    langs.sort()
    return langs

def make_kvmap(items):
    """Make key:value map from given string items.
    Arugment ''items'' is a list of string and each item should have
    ''key''=''value'' format. The items is simply ignored if it does
    not have such a format.

    >>> make_kvmap(['a=b', 'c=d'])
    {'a': 'b', 'c': 'd'}
    >>> make_kvmap(['a=b', 'foo', 'c=d'])
    {'a': 'b', 'c': 'd'}
    >>> make_kvmap(['a=b', 'foo', 'c=d', 'e='])
    {'a': 'b', 'c': 'd', 'e': ''}
    >>> make_kvmap(['a=b', 'foo', 'c=d', 'e=f=g'])
    {'a': 'b', 'c': 'd', 'e': 'f=g'}
    """
    return dict(tuple([x.split('=', 1) for x in items if x.count('=')]))


# borrowed from trac 0.11
def parse_args(args, strict=True):
    """Utility for parsing macro "content" and splitting them into arguments.
    ** This function is copied from trac 0.11. **

    The content is split along commas, unless they are escaped with a
    backquote (like this: \,).
    
    :param args: macros arguments, as plain text
    :param strict: if `True`, only Python-like identifiers will be
                   recognized as keyword arguments 

    Example usage:

    >>> parse_args('')
    ([], {})
    >>> parse_args('Some text')
    (['Some text'], {})
    >>> parse_args('Some text, mode= 3, some other arg\, with a comma.')
    (['Some text', ' some other arg, with a comma.'], {'mode': ' 3'})
    >>> parse_args('milestone=milestone1,status!=closed', strict=False)
    ([], {'status!': 'closed', 'milestone': 'milestone1'})
    
    """    
    largs, kwargs = [], {}
    if args:
        for arg in re.split(r'(?<!\\),', args):
            arg = arg.replace(r'\,', ',')
            if strict:
                m = re.match(r'\s*[a-zA-Z_]\w+=', arg)
            else:
                m = re.match(r'\s*[^=]+=', arg)
            if m:
                kw = arg[:m.end()-1].strip()
                if strict:
                    kw = unicode(kw).encode('utf-8')
                kwargs[kw] = arg[m.end():]
            else:
                largs.append(arg)
    return largs, kwargs


# borrowed from trac 0.11
class py_groupby(object):
    def __init__(self, iterable, key=None):
        if key is None:
            key = lambda x: x
        self.keyfunc = key
        self.it = iter(iterable)
        self.tgtkey = self.currkey = self.currvalue = xrange(0)
    def __iter__(self):
        return self
    def next(self):
        while self.currkey == self.tgtkey:
            self.currvalue = self.it.next() # Exit on StopIteration
            self.currkey = self.keyfunc(self.currvalue)
        self.tgtkey = self.currkey
        return (self.currkey, self._grouper(self.tgtkey))
    def _grouper(self, tgtkey):
        while self.currkey == tgtkey:
            yield self.currvalue
            self.currvalue = self.it.next() # Exit on StopIteration
            self.currkey = self.keyfunc(self.currvalue)
try:
    from itertools import groupby
except ImportError:
    groupby = py_groupby


if __name__ == '__main__':
    import doctest
    class Req(object):                          # dummy req object
        def __init__(self):
            self.args = {}
            self.headers = {}
            self.session = {}
        def get_header(self, key):
            return self.headers.get(key, None)
    doctest.testmod()
