# -*- coding: utf-8 -*-
import os, re
from trac import __version__ as version
from trac.core import *
from trac.config import Option, ListOption
from trac.wiki import WikiSystem
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

try:
    # for trac 0.10 or 0.11
    from trac.util import sorted
except ImportError:
    # for trac 0.11.x or later
    from trac.util.compat import sorted

try:
    from trac.util.html import html as tag
except:
    from genshi.builder import tag
    
import util

groupby = util.groupby

## alternative TitleIndex macro

def _list_wiki_default_pages():
    """List wiki page files in 'wiki-default' directory.
    This is aimed to know page names to be categorized as 'system'.
    """
    # get wiki-default directory
    try:
        # try for 0.10.x
        from trac.config import default_dir
        dir = default_dir('wiki')
    except:
        # try for 0.11.x (with setup tools)
        import pkg_resources
        dir = pkg_resources.resource_filename('trac.wiki', 'default-pages')
    if not os.path.isdir(dir):
        return []
    pages = []
    # list wiki default pages. No need to include lang variations here.
    re_wiki_page = re.compile(r'[A-Z][a-zA-Z0-9]+')
    for f in os.listdir(dir):
        if re_wiki_page.match(f):
            pages.append(f)
    return pages

def _exclude(pages, excludes):
    if not excludes:
        return pages, []                        # nothing excluded
    items = []
    for item in excludes:
        if item.endswith('*'):
            # prefix
            items.append(re.escape(item[:-1]) + '.*')
        else:
            # exact
            items.append(re.escape(item))
    re_exclude = re.compile('|'.join(items))
    filtered = []
    excluded = []
    for page in pages:
        if re_exclude.match(page):
            excluded.append(page)
        else:
            filtered.append(page)
    return filtered, excluded

class MultiLangTitleIndex(WikiMacroBase):
    """Inserts an alphabetic list of all wiki pages cosidering suffixes.

    This macro is similar to TitleIndex macro but differ in two points.
     * All the variants are displayed in one line.
     * Displayed in two columns. One is for the pages made for the project.
       One is for the pages provided by Trac. `WikiStart` and `SandBox`
       are grouped in project pages as default. This is configurable
       via `_explicit_user_pages` option.

    One entry displayed by this macro has a format like this:
    {{{
    WikiStart (en, fr, ja, default)
    }}}

    Left most page name is for usual access with negotiation.
    Items in paren are existing language variants for the page.

    System pages are decided by listing files in wiki-default
    directory. As described before, you can exclude some pages as user
    page by spcifying `_explicit_user_pages`. Likewise, you can
    specify the system pages via `_explicit_system_pages` option.
    
    These two options are list of page names separated by comma. If
    the page name ends with '*' character, it works as prefix for
    matching. For exmaple, 'Trac*' means "page names staring with
    'Trac'".
    
    """
    _explicit_user_pages = ListOption('multi-lang-title-index',
                                      'explicit_user_pages',
                                      'WikiStart, SandBox',
                                      doc="List of page names to be grouped"
                                      " in user page. If the name ends"
                                      " with '*', it works as prefix.")

    _explicit_system_pages = ListOption('multi-lang-title-index',
                                        'explicit_system_pages',
                                        '', #'GraphViz*',
                                        doc="List of page names to be grouped"
                                        " in system page. If the name ends"
                                        " with '*', it works as prefix.")

    _wiki_default_pages = _list_wiki_default_pages()

    SPLIT_RE = re.compile(r"( |/|[0-9])")
    PAGE_SPLIT_RE = re.compile(r"([a-z])([A-Z])(?=[a-z])")

    # macro entry point for Trac 0.11
    def expand_macro(self, formatter, name, content):
        args, kw = util.parse_args(content)
        prefix = args and args[0] or None
        format = kw.get('format', '')
        minsize = max(int(kw.get('min', 2)), 2)
        depth = int(kw.get('depth', -1))
        start = prefix and prefix.count('/') or 0

        wiki = formatter.wiki
        pages = sorted([page for page in wiki.get_pages(prefix) \
                        if 'WIKI_VIEW' in formatter.perm('wiki', page)])
        pagelangs = {}
        for page in pages:
            name, lang = util.split_lang(page, '')
            langs = pagelangs.get(name, [])
            if lang not in langs:
                langs.append(lang)
            pagelangs[name] = langs
        pages = sorted(pagelangs.keys()) # collection of default pages

        upages, spages = self.split_pages(pages)

        def format_page_name(page, split=False):
            try:
                # for trac 0.11                
                return wiki.format_page_name(page, split=split)
            except:
                # for trac 0.10
                if split:
                    return self.PAGE_SPLIT_RE.sub(r"\1 \2", page)
                return page
        def split(page):
            if format != 'group':
                return [format_page_name(page)]
            else:
                return self.SPLIT_RE.split(format_page_name(page, split=True))
        
        # Group by Wiki word and/or Wiki hierarchy
        upages, spages = [[(split(page), page) for page in pages
                           if depth < 0 or depth >= page.count('/') - start]
                          for pages in (upages, spages)]
                          
        def split_in_groups(group):
            """Return list of pagename or (key, sublist) elements"""
            groups = []
            for key, subgrp in groupby(group, lambda (k,p): k and k[0] or ''):
                subgrp = [(k[1:],p) for k,p in subgrp]
                if key and len(subgrp) >= minsize:
                    sublist = split_in_groups(sorted(subgrp))
                    if len(sublist) == 1:
                        elt = (key+sublist[0][0], sublist[0][1])
                    else:
                        elt = (key, sublist)
                    groups.append(elt)
                else:
                    for elt in subgrp:
                        groups.append(elt[1])
            return groups

        def render_one(page, langs):
            result = [tag.a(wiki.format_page_name(page),
                            href=formatter.href.wiki(page))]
            if langs:
                for lang in sorted(langs):
                    result.append(', ')
                    p = '%s.%s' % (page, lang)
                    result.append(tag.a(lang or 'default',
                                        style='color:#833',
                                        href=formatter.href.wiki(p)))
                result[1] = ' ('
                result.append(')')
            return result

        def render_groups(groups):
            return tag.ul(
                [tag.li(isinstance(elt, tuple) and 
                        tag(tag.strong(elt[0]), render_groups(elt[1])) or
                        render_one(elt, pagelangs.get(elt)))
                 for elt in groups])
        #return render_groups(split_in_groups(pages))
        return tag.table(tag.tr([tag.td([tag.b(title + ' pages:'),
                                         render_groups(split_in_groups(pages))])
                                 for title, pages in [('User', upages),
                                                      ('System', spages)]],
                                valign='top'))

    def split_pages(self, pages):
        system_pages, exc = _exclude(self._wiki_default_pages,
                                     self._explicit_user_pages)
        # Pick all wiki pages and make list of master pages and also
        # make list of language variations for each master page.
        # The name of master page should not have language suffix.
        # And make list of user pages (non system page).
        user_pages = []                       # pages marked as user's
        lang_map = {}                       # language list for each page
        for page in pages:
            # note: language variant is not stored in system_pages.
            p, l = util.split_lang(page)
            if p not in system_pages and p not in user_pages:
                user_pages.append(p)
        # process explicit system pages
        user_pages, exc = _exclude(user_pages, self._explicit_system_pages)
        system_pages += exc
        system_pages = sorted(system_pages)
        return user_pages, system_pages
        
    
    # macro entry point for Trac 0.10
    def render_macro(self, req, name, content):
        from trac.wiki.formatter import Formatter
        formatter = Formatter(self.env, req)
        def getparm(category, target):
            return req.perm.perms
        formatter.perm = getparm
        return self.expand_macro(formatter, name, content)

class TitleIndexMacro(MultiLangTitleIndex):
    """This is placeholder macro to override with `MultiLangTitleIndex` macro.
    By enabling wikinegotiator plugin, original `TitleIndexMacro` is
    replaced by `MultiLangTitleIndex` by this definition.
    To use original, disable this macro in the admin panel or add following
    line in your `trac.ini`:
    {{{
    wikinegotiator.macros.titleindexmacro = disabled
    }}}
    """
    pass

# bonus: alternative TOC macro

try:
    # define delived TOC macro. Requires trac 0.11 and tractoc enabled.
    # Renamed as BaseTOCMacro since we may redefine TOCMacro.
    from tractoc.macro import TOCMacro as BaseTOCMacro
    import wikinegotiator

    # require tractoc macro for 0.11 or later which has get_page_text()
    # method.
    if not hasattr(BaseTOCMacro, 'get_page_text'):
        raise Exception('NTOC macro needs tractoc macro for 0.11 (or later).')
    
    class NTOCMacro(BaseTOCMacro):
        """Language-aware version of TOC Macro.

        === Dependency ===
         * trac 0.11 or later
         * tractoc macro for trac 0.11

        === Description ===
        This macro is an alternative of TOC macro (written by
        coderanger) extending to use content of localized page if
        exist. You can write TOC macro entry by normal page name
        wihtout lang suffix.

        For example, if you specify the page '!SubPage' in argument on
        the Japanese localized page '!BasePage.ja', find '!SubPage.ja'
        first and return it's content if exist.  Or find localized
        page regarding preferred languages from browser's
        Accept-Language: header.  Or, finally, exact given page name
        is used.

        If you specify the page with lang suffix, that page is used.

        === LIMITATION ===
        
        TOC macro accepts wildcard like `Trac*` to list multiple pages
        but NTOC macro cannot hook it. In such case, all the variants
        will match and be used. It'd be better not to use wildcard
        with NTOC macro.
        """

        def expand_macro(self, formatter, name, args):
            """Expand wildcard page spec to non-suffixed page names.
            """
            args, kw = util.parse_args(args)

            wiki = WikiSystem(self.env)
            newargs = []
            for arg in args:
                newargs.append(arg)
                arg = arg.strip()
                if arg.endswith('*'):
                    newargs.pop()
                    # expand wildcard as indivisual pages with removing
                    # suffixed pages.
                    prefix = arg[:-1]
                    pages = []
                    for page in wiki.get_pages(prefix):
                        name, lang = util.split_lang(page)
                        if name not in pages:
                            pages.append(name)
                    newargs += pages
            # reconstruct 'args' argument and call ancestor
            args = ','.join(newargs + ['%s=%s' % pair for pair in kw.items()])
            return BaseTOCMacro.expand_macro(self, formatter, name, args)
        
        def get_page_text(self, *args):
            """Return a tuple of `(text, exists)` for the given page (resource).
            The page is altered if lang suffix is not exist in page name
            like wiki page negotiation. 
            """
            # Since TracTOC macro r4366, 'formatter' argument is added
            # as 2nd argument.
            if len(args) == 1:
                # old code
                formatter = self.formatter
                page_resource = args[0]
            else:
                formatter, page_resource = args
            if page_resource.id == formatter.context.resource.id:
                return (formatter.source, True)
            else:
                req = formatter.context(page_resource).req
                nego = wikinegotiator.negotiator.WikiNegotiator(self.env)
                # know lang of parent page where this macro is on.
                parent = req.args.get('page', 'WikiStart')
                bname, blang = util.split_lang(parent, 'default')
                # get body name and lang from given page name.
                name, lang = util.split_lang(page_resource.id)
                wiki = WikiSystem(self.env)
                if lang is None:
                    # When no lang suffix is in given page name,
                    # find localized page for lang of parent page,
                    # then preferred language.
                    langs = [blang] + util.get_preferred_langs(req)
                    for lang in langs:
                        dname = util.make_page_name(name, lang)
                        if wiki.has_page(dname):
                            name = dname
                            break # from for
                else:
                    # with suffix, exact page is used
                    name = page_resource.id
                page = WikiPage(self.env, name)
                # update resource id to highlight current page.
                page_resource.id = name
                return (page.text, page.exists)

    class TOCMacro(NTOCMacro):
        """This is placeholder macro to override with `NTOC` macro.
        By enabling wikinegotiator plugin, original `TOCMacro` is
        replaced by `NTOCMacro` by this definition.
        To use original, disable this macro in the admin panel or
        add following line in your `trac.ini`:
        {{{
        wikinegotiator.macros.tocmacro = disabled
        }}}
        If you cannot get expected result, you may disable original
        macro.
        """
        pass
    
except Exception, exc:
    # TOCMacro load fail or not acceptable version.
    pass
