# -*- coding: utf-8 -*-

import re
from urlparse import urlparse
from trac.core import Component, implements
from trac.wiki import WikiSystem
from trac.wiki.web_ui import WikiModule
from trac.web.api import IRequestFilter
from trac.config import Option
from macros import MultiLangTitleIndex

class WikiNegotiator(Component):

    _re_page = re.compile(r'(.*)(?:\.([a-z][a-z](?:-[a-z][a-z])?))$')

    _re_lang = re.compile(r'^(?P<lang>[a-z]{1,8}(?:-[a-z]{1,8})?|\*)'
                         +'(?:;\s*q=(?P<q>[0-9.]+))?$')

    _default_lang = Option('wiki', 'default_lang', 'en',
                          doc="""Language for non-suffixed page.""")


    implements(IRequestFilter)

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
                _, lang = self._split_lang(page)
                req.send_header('Content-Language',
                                lang or self._default_lang)
            # always send Vary header to tell language negitiation is
            # available
            req.send_header('Vary', 'Accept-Language')
        return handler

    def post_process_request(self, req, template, content_type):
        # nothing to do
        return template, content_type


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

        # No negotiation to display edited page after commit.
        # 'Referrer' header can be used to detect this case
        # by checking 'action=edit' parameter.
        # ex. "Referer: http://host/wiki/WikiStart?action=edit"
        referer = req.get_header('Referer')
        if referer and referer.startswith(req.base_url) and \
                'action=edit' in urlparse(referer)[4].split('&'):
            self.env.log.debug('disable negotiation for edited page.')
            return orig

        # Use requested page itself if the page name has language
        # suffix. As special case, if the name ends with period '.',
        # use non-suffixed page is used.
        if orig.endswith('.'):
            return orig[:-1]                    # force un suffixed page

        page, lang = self._split_lang(orig)
        if lang:
            #debug('case 1 : requested page name has lang suffix')
            return orig
        page = page or 'WikiStart'

        # At this point, page name does not have language suffix.

        # List preffered language codes from http request.
        # Check language suffixed page existance in order of preffered
        # language codes in http request and use it if exist.
        wiki = WikiSystem(self.env)
        for lang in self._get_preferred_langs(req):
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

    def _split_lang(self, page, lang=None):
        """Split page body name and suffixed language code from
        requested page name.
        ex. 'sub/pagename.ja' => ('sub/pagename', 'ja')
            'sub/pagename.ja-jp' => ('sub/pagename', 'ja-jp')
        """
        m = self._re_page.match(page)
        if m:
            return (m.group(1), m.group(2))         # with lang suffix
        else:
            return (page, lang)                     # without lang suffix


    def _get_preferred_langs(self, req):
        # decide by language denotation in url parameter: '?lang=xx'
        if req.args.has_key('lang'):
            return [req.args.get('lang')]
        # otherwise, decide by http Accept-Language: header
        langs = self._parse_langs(req.get_header('accept-language')
                                  or self._default_lang)
        if self._default_lang not in langs:
            langs += [self._default_lang]                 # fallback language
        return langs


    def _parse_langs(self, al):
        """Make list of language tag in preferred order.
        For example,
        Accept-Language: ja,en-us;q=0.8,en;q=0.2
        or
        Accept-Language: en;q=0.2,en-us;q=0.8,ja
        results ['ja', 'en-us', 'en']
        """
        infos = []
        for item in al.split(','):
            m = self._re_lang.match(item.strip())
            if m:
                lang, q = m.groups()
                infos.append((lang, float(q or '1.0')))
        # sort by quality descendant
        infos.sort(lambda x,y: cmp(y[1], x[1]))
        return [info[0] for info in infos] # returns list of lang string
