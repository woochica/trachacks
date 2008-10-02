# -*- coding: utf-8 -*-
import os, re
from trac.core import *
from trac.config import Option, ListOption, BoolOption
from trac.util import sorted
from trac.wiki import WikiSystem, html
from trac.wiki.macros import WikiMacroBase



## macro

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
    
    """
    _explicit_user_pages = ListOption('multi-lang-title-index',
                                      'explicit_user_pages',
                                      'WikiStart, SandBox',
                                      doc="List of page names to be grouped"
                                      " in user page.")

    _wiki_default_pages = _list_wiki_default_pages()
    
    def render_macro(self, req, name, content):
        env = self.env
        wiki = WikiSystem(env)
        # Get system provided pages excluding some.
        system_pages = list(self._wiki_default_pages) # pages provided by trac
        for page in self._explicit_user_pages:
            if page in system_pages:
                system_pages.remove(page)
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
                        for lang in sorted(langs):
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
