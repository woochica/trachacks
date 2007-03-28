# -*- coding: utf-8 -*-
import re
from trac.core import *
from trac.config import Option, ListOption, BoolOption
from trac.util import sorted
from trac.wiki import WikiSystem, html
from trac.wiki.macros import WikiMacroBase

## macro

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

    def render_macro(self, req, name, content):
        # get system pages which is author=trac at version 1
        env = self.env
        db = env.get_db_cnx()
        curs = db.cursor()
        # Pick pages whose author is 'trac' in some version.  This means
        # that the system page modified by user is grouped as 'system
        # page'.
        curs.execute("select name,author from wiki")
        system_pages = []                   # pages marked as system's
        lang_map = {}                       # language list for each page
        re_lang = re.compile('^(.*)\.([a-z]{2}(?:-[a-z]{2})?)$')
        for page, author in curs:
            # note: language varie is not stored in system_pages.
            m = re_lang.match(page)
            if m:
                p, l = m.groups()
                langs = lang_map.get(p,[])
                if l not in langs:
                    lang_map[p] = langs + [l]
            elif author == 'trac' and page not in system_pages:
                system_pages.append(page)
        if not hasattr(env, 'get_cnx_pool'):
            # without db connection pool, we should close db.
            curs.close()
            db.close()
        # Exclude some pages to be grouped in user page.
        for page in self._explicit_user_pages:
            if page in system_pages:
                system_pages.remove(page)
        # Pick user pages. Specially for language variation pages,
        # translated page of system page is also grouped as system page as
        # if author is not 'trac'. This is for shrinked view.
        re_sys = re.compile('^(?:' + '|'.join(system_pages) +
                            '(?:\.[a-z]{2}(?:-[a-z]{2})?)?)')
        prefix = content or None
        wiki = WikiSystem(env)
        user_pages = []                       # pages marked as user's
        for page in sorted(wiki.get_pages(prefix)):
            if re_lang.match(page):
                continue
            if not re_sys.match(page):
                user_pages.append(page)
        ## should be langu sub item'ed
        tr = html.TR(valign='top')
        for title, pages in (('Project', user_pages),
                             ('System Provided', system_pages)):
            if 0 < len(pages):
                td = html.TD
                tr.append(td)
                if not prefix:
                    td.append(html.B(title + ' Pages'))
                ul = html.UL()
                td.append(ul)
                for page in sorted(pages):
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
