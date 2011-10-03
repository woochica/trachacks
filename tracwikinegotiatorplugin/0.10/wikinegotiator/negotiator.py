# -*- coding: utf-8 -*-

import re
from urlparse import urlparse
from trac.core import Component, implements
from trac.wiki import WikiSystem
from trac.wiki.web_ui import WikiModule
from trac.wiki.api import IWikiChangeListener
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.config import Option, BoolOption, ListOption
from pkg_resources import resource_filename

try:
    from trac.web.clearsilver import HDFWrapper
    from trac.util.html import html as tag
    with_hdf = True                             # means on Trac 0.10.x
except:
    from genshi.builder import tag
    with_hdf = False

from wikinegotiator import util

class WikiNegotiator(Component):

    implements(IRequestFilter, IWikiChangeListener, ITemplateProvider)

    # options
    _default_lang = Option('wiki', 'default_lang', 'en',
                          doc="""Language for non-suffixed page.""")


    _lang_names = ListOption('wiki-negotiator', 'lang_names', '',
                            doc="""List of language names for suffixes.
Specify comma separated ''lang''=''name'' items.
''lang'' is language code to be used as suffix like `en` or `ja`,
''name'' is display string for the language.
If ''name'' is omitted or language is not listed here,
lang code itself is displayed in menu.

For example, if you specified {{{'en=English, fr, ja=Japanese'}}},
language menu goes like this:
{{{
"Language: English | fr | Japanese | default"
}}}

In this case, en and ja is named but fr is not.

Displayed languages are listed from existing wiki pages automatically.
""")

    _menu_style = Option('wiki-negotiator', 'menu_style', 'simple',
                         doc="""Style type of language menu.
                         Specify one of `simple`, `ctxnav`, `button`,
                         `tab` and `none`.
                         `simple` is a solid independent menu bar bellow
                         the main navigation menu.
                         `ctxnav` is like a `simple` but displayed in the
                         context menu. `button` is button faced menu bar.
                         `tab` is like a tabbed page selecter.
                         `none` is for hiding language menu.
""")

    _default_in_menu = BoolOption('wiki-negotiator', 'default_in_menu',
                                  'false',
                                  doc="""Always show 'default' pseudo language in menu bar.
If this options is false, non-suffixed page is treated like suffixed page
for default lang. """)
    _invalid_suffixes = ListOption('wiki-negotiator', 'invalid_suffixes', 'py',
                                   doc="""List of suffix not shown as language menu.
Languages in this option are never shown in language menu.
This option is usefull for the case of having lang suffix like extension
like "test.py".
""")


    # -- implementation of IRequestFilter --

    def pre_process_request(self, req, handler):
        """Replace requested wiki page name by content negotiation.
        Nothing changed for non-wiki request.
        """
        if isinstance(handler, WikiModule):
            orig = req.args.get('page', 'WikiStart')
            # set altered page name
            page = self._decide_page(req)
            if page != orig:
                req.args['page'] = page
                self.env.log.debug('Negotiated: %s' % page)
                # Set Content-Language only when language specific
                # page is selected.
                # TODO: I don't know we should set default language
                #       for base page.
                _, lang = util.split_lang(page)
                req.send_header('Content-Language',
                                lang or self._default_lang)
            # always send Vary header to tell language negitiation is
            # available
            req.send_header('Vary', 'Accept-Language')
        return handler

    def post_process_request(self, req, template, content_type):
        # make menubar if trac 0.10
        if with_hdf and template == 'wiki.cs' and not req.args.get('action'):
            # As gimic for Trac 0.10, place our template directory on
            # the top of HDF loadpath to use our modified 'header.cs'.
            hdf = getattr(req, 'hdf', None)
            paths = [resource_filename('wikinegotiator', 'templates')]
            path_fmt = 'hdf.loadpaths.%d'
            i = 0
            while hdf.hdf.getObj(path_fmt % i):
                paths.append(hdf[path_fmt % i])
                i += 1
            hdf['hdf.loadpaths'] = paths
            # set menu bar data into HDF (renderd as nav macro).
            idx = 0
            for item, cls in self.make_menu_bar(req):
                hdf['chrome.nav.langmenu.%d' % idx] = item
                if 'active' in cls:
                    hdf['chrome.nav.langmenu.%d.active' % idx] = 1
                idx += 1
        return template, content_type

    # -- implementation of IWikiChangeListener --

    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added."""
        self.available_langs = None             # forget to refresh

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called when a page has been modified."""
        pass                                    # nothing to do

    def wiki_page_deleted(self, page):
        """Called when a page has been deleted."""
        self.available_langs = None             # forget to refresh

    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted."""
        pass                                    # nothing to do

    def wiki_page_renamed(self, page, old_name):
        """Called when a page has been renamed."""
        self.available_langs = None             # forget to refresh

    # ITemplateProvider
    def get_htdocs_dirs(self):
        dir = resource_filename('wikinegotiator', 'htdocs')
        return [('wikinegotiator', dir)]
    
    def get_templates_dirs(self):
        return []

    # 
    def make_menu_bar(self, req):
        langs = self._get_available_langs()
        if not langs:
            return []                   # no need for lang menu
        
        dflt = None                            # default language
        if not self._default_in_menu:
            dflt = self._default_lang
            # add default lang for the mean of default lang page
            if self._default_lang not in langs:
                langs.append(self._default_lang)
                langs.sort()
        
        page = req.args.get('page', 'WikiStart')
        thisname, thislang = util.split_lang(page, 'default')
        selected = req.session.get('wiki_lang', 'default') # selected lang
        css = 'wikinegotiator/css/langmenu-%s.css' % self._menu_style
        add_stylesheet(req, css)
        lang_name_map = util.make_kvmap(self._lang_names)
        
        # add selected lang if need
        if selected not in langs:
            langs.append(selected)
        # Move 'default' to tail in menu bar if option is set or having
        # default_lang page other than default page.
        if 'default' in langs:
            langs.remove('default')
        if self._default_in_menu:
            langs.append('default')             # always
        elif dflt and self._has_page(thisname, dflt) and self._has_page(thisname):
            # both default_lang and default page are exist.
            langs.append('default')

        # make list of menu item
        result = [(tag.span('Language:',
                            title='Select a language of wiki content'),
                   'first')]
        for i, lang in enumerate(langs):
            cls = ''
            acls = ''
            title = ''
            if lang == selected:
                acls += 'selected'
                title = 'selected language'
            if lang == thislang or (lang == dflt and thislang == 'default'
                                    and 'default' not in langs):
                cls += ' active'
                title = 'displaying language (default)'
            if lang == selected  == thislang:
                title = 'selected and displaying language'
            if (lang == dflt and 'default' not in langs) or lang == 'default':
                # map default lang to default page
                suffix = ''
            else:
                suffix = lang
            if not self._has_page(thisname, suffix):
                acls += ' notexist'
                title += ' (not available)'
            if i == len(langs)-1:
                cls += ' last'
            a = tag.a(lang_name_map.get(lang, lang),
                      href=req.href.wiki('%s.%s' % (thisname, suffix)),
                      class_=acls,
                      title=title.strip())
            result.append((a, cls))
        return result


    # local methods

    def _decide_page(self, req):
        """decide page name to use regarding client language.
        This function is called from hook with self as WikiModule instance.
        Returns page name to be displayed.
        """
        orig = req.args.get('page', 'WikiStart')

        # This negotiation is only for viewing.
        # If without this rule, you may edit 'SomePage.en' by edit
        # button on 'SomePage.' page.
        if req.args.get('action', None):
            return orig

        # Get language from session to keep selected language if possible.
        lang = req.session.get('wiki_lang', None)
        
        # Use requested page itself if the page name has language
        # suffix. As special case, if the name ends with period '.',
        # use non-suffixed page is used.
        # This action means user choose the language.
        if orig.endswith('.'):
            req.session['wiki_lang'] = 'default'
            return orig[:-1]                    # force un suffixed page

        page, lang = util.split_lang(orig)
        if lang:
            #debug('case 1 : requested page name has lang suffix')
            req.session['wiki_lang'] = lang
            return orig
        page = page or 'WikiStart'

        # At this point, page name does not have language suffix.

        # List preffered language codes from http request.
        # Check language suffixed page existance in order of preffered
        # language codes in http request and use it if exist.
        wiki = WikiSystem(self.env)
        for lang in util.get_preferred_langs(req):
            if lang in ['default', 'other']:
                lpage = page
            else:
                lpage = '%s.%s' % (page, lang)
            if wiki.has_page(lpage):
                #debug('case 2 : have suffixed page: %s' % lpage)
                return lpage
            # Consideration of default_lang setting.
            # This is required not access to lower ordered
            # language page. For example,
            #   preferred language:  ja, en, fr
            #   default_lang: en
            #   existing pages:  'page', 'page.fr'
            # We should search page in order:
            #   'page.ja', 'page.en', 'page', 'page.fr'
            if lang == self._default_lang and wiki.has_page(page):
                return page

        # No page matched with preffered language.
        # Use requested page.
        #debug('case 3 : no page for preffered lang')
        return orig


    def _get_available_langs(self):
        """Get language suffixes from existing wiki pages.
        Not that this list does not contains 'default' pseudo lang.
        This function also cache page names for later existing check.
        """
        langs = getattr(self, 'available_langs', None)
        pages = []
        if langs is None:
            # list up langs from existing pages.
            pages = list(WikiSystem(self.env).get_pages())
            langs = util.make_lang_list(pages)
            # remove invalid suffixes
            langs = [x for x in langs if x not in self._invalid_suffixes]
            self.available_langs = langs        # cache
            self.available_pages = pages        # cache
        return list(langs)                      # return copied list

    def _has_page(self, base, lang=None):
        return util.make_page_name(base, lang) in self.available_pages


# trying to install stream filter to make menu bar on Trac 0.11.
try:
    from trac.web.api import ITemplateStreamFilter
    from genshi.filters.transform import Transformer

    class WikiNegotiatorMenuBar(Component):
        """Additional interface for wiki page
        NOTE: Trac 0.11 or later is required."""
        implements(ITemplateStreamFilter)

        _menu_location = Option('wiki-negotiator', 'menu_location',
                                  '//div[@id="main"]',
                                  doc="""Location of menu bar block to be inserted before.
The value should be valid XPATH locator string.
Default value is '//div[@id="main"]' and inserted after main menubar.
""")
        
        # implementation of ITemplateStreamFilter
        def filter_stream(self, req, method, filename, stream, data):
            if filename != 'wiki_view.html':
                return stream
            items = WikiNegotiator(self.env).make_menu_bar(req)
            if not items or len(items) <= 1:
                return stream
            li = []
            for content, cls in items:
                li.append(tag.li(content, class_=cls))
            insert = tag.div(tag.ul(li), id='langmenu')
            return stream | Transformer(self._menu_location).before(insert)

except Exception, exc:
    pass
