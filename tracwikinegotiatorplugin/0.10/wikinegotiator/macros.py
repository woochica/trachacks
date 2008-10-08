# -*- coding: utf-8 -*-
import os, re
from trac import __version__ as version
from trac.core import *
from trac.config import Option, ListOption
from trac.wiki import WikiSystem, html
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
try:
    # for trac 0.10 or 0.11
    from trac.util import sorted
except ImportError:
    # for trac 0.11.x or later
    from trac.util.compat import sorted

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
    WikiStart (en, fr, ja, other)
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
    
    def render_macro(self, req, name, content):
        env = self.env
        wiki = WikiSystem(env)
        # process explicit user pages
        system_pages, exc = _exclude(self._wiki_default_pages,
                                     self._explicit_user_pages)
        # Pick all wiki pages and make list of master pages and also
        # make list of language variations for each master page.
        # The name of master page should not have language suffix.
        # And make list of user pages (non system page).
        user_pages = []                       # pages marked as user's
        lang_map = {}                       # language list for each page
        re_lang = re.compile('^(.*)\.([a-z]{2}(?:-[a-z]{2})?)?$')
        for page in wiki.get_pages():
            # note: language variant is not stored in system_pages.
            m = re_lang.match(page)
            if m:
                p, l = m.groups()
            else:
                p, l = page, None
            langs = lang_map.get(p,[])
            if l and l not in langs:
                lang_map[p] = langs + [l]
            if p not in system_pages and p not in user_pages:
                user_pages.append(p)
        # process explicit system pages
        user_pages, exc = _exclude(user_pages, self._explicit_system_pages)
        system_pages += exc
        # generate output        
        prefix = content
        tr = html.TR(valign='top')
        for title, pages in (('Project', user_pages),
                             ('System Provided', system_pages)):
            if 0 < len(pages):
                td = html.TD
                tr.append(td)
                td.append(html.B(title + ' Pages'))
                ul = html.UL()
                td.append(ul)
                for page in sorted(pages):
                    if prefix and not page.startswith(prefix):
                        continue
                    item = [html.A(wiki.format_page_name(page),
                                   href=env.href.wiki(page))]
                    if lang_map.has_key(page):
                        item.append(' (')
                        langs = lang_map[page]
                        for lang in sorted(langs) + ['other']:
                            p = '%s.%s' % (page, lang)
                            item.append(html.A(lang,
                                               href=env.href.wiki(page) + '?lang='+lang,
                                               style='color:#833'
                                               ))
                            item.append(', ')
                        item.pop()
                        item.append(')')
                    ul.append(html.LI(item))
        return html.TABLE(tr)



# alternative TOC macro

try:
    # For delived new NTOC macro, require trac 0.11 and tractoc enabled.
    # Renamed as BaseTOCMacro since we may redefine TOCMacro.
    from tractoc.macro import TOCMacro as BaseTOCMacro
    import wikinegotiator.negotiator

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
            args, kw = parse_args(args)

            wiki = WikiSystem(self.env)
            nego = wikinegotiator.negotiator.WikiNegotiator(self.env)
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
                        name, lang = nego._split_lang(page)
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
                bname, blang = nego._split_lang(parent)
                # get body name and lang from given page name.
                name, lang = nego._split_lang(page_resource.id)
                wiki = WikiSystem(self.env)
                if lang is None:
                    # When no lang suffix is in given page name,
                    # find localized page for lang of parent page,
                    # then preferred language.
                    langs = [blang or nego._default_lang]
                    langs += nego._get_preferred_langs(req)
                    for lang in langs:
                        dname = '%s.%s' % (name, lang)
                        if wiki.has_page(dname):
                            name = dname
                else:
                    # with suffix, exact page is used
                    name = page_resource.id
                page = WikiPage(self.env, name)
                # update resource id to highlight current page.
                page_resource.id = name
                return (page.text, page.exists)

except:
   # TOCMacro load fail
   pass

## Bonus Wild TIPS:
## Uncomment following two lines if you want to override TOC macro itself.
## It means, you can use TOC macro in a page as before with NTOC feature.
## NOTE: After uncomment, 'class' should not have any preceding space.
#class TOCMacro(NTOCMacro):
#     pass
