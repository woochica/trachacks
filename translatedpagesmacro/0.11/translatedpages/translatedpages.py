# -*- coding: utf-8 -*-

""" Macro to show the translated pages list. """

__author__ = 'Zhang Cong (ftofficer)'
__version__ = '1.0'

from genshi.builder import tag

from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import ITemplateProvider
from trac.wiki.api import IWikiMacroProvider
from cStringIO import StringIO
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.api import WikiSystem

class TranslatedPagesMacro(Component):
    """
    Macro to show the translated pages list.
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield u'TranslatedPages'

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return to_unicode(inspect.getdoc(self.__class__))

    def parse_macro(self, parser, name, content):
        raise NotImplementedError

    # --

    TRAC_LANGUAGES_PAGE = u'TracLanguages'
    BASE_LANG = u'en'

    def __init__(self):
        self.languages_page_version = 0
        self._update_languages()

    def _parse_languages_list(self, text):
        """
        Parses the list of languages in form
         * <language code> <language name>
         * <language code> <language name>
        ...
        """
        langs = {}
        for line in text.split(u'\r\n'):
            if not line.startswith(u' * '):
                self.env.log.warn(
                    u"Wrong line syntax while parsing languages list: %s" % line)
                continue
            if ' ' not in line[3:]:
                self.env.log.warn(
                    u"Wrong line syntax: missing language name: %s" % line)
                continue
            (code, name) = line[3:].split(None, 1)
            self.env.log.debug("Adding language %s -> %s" % (code, name))
            langs[code] = name
        return langs

    def _update_languages(self):
        languages_page = WikiPage(self.env, self.TRAC_LANGUAGES_PAGE)
        if not languages_page.exists:
            self.env.log.warn(u"Can't find page %s" % self.TRAC_LANGUAGES_PAGE)
            self.languages = {}
            self.languages_page_version = 0
        else:
            if languages_page.version > self.languages_page_version:
                self.languages = self._parse_languages_list(languages_page.text)
                self.languages_page_version = languages_page.version

    def _get_language_name(self, lang_code):
        self._update_languages()
        return self.languages.get(lang_code, lang_code)

    def _seems_like_lang_code(self, lang_code):
        return len(lang_code) in (2,3) \
            and lang_code.islower() \
            and lang_code.isalpha()

    def _get_translated_page(self, name, lang_code):
        if lang_code == self.BASE_LANG:
            return name
        else:
            return name + u'/' + lang_code

    def _get_page_info(self, page_name):
        parts = page_name.rsplit(u'/', 1)
        if len(parts) < 2:
            return (page_name, self.BASE_LANG)
        (prefix, suffix) = parts
        if self._seems_like_lang_code(suffix):
            return (prefix, suffix)
        else:
            retrun (page_name, self.BASE_LANG)

    def _get_translations(self, base_page_name):
        (base_page, page_lang) = self._get_page_info(base_page_name)
        for subpage in sorted(WikiSystem(self.env).get_pages(base_page_name)):
            (subpage_base_page, subpage_lang) = self._get_page_info(subpage)
            if base_page == subpage_base_page:
                yield subpage_lang

    def _get_lang_link(self, base_name, lang_code):
        page_name = self._get_translated_page(base_name, lang_code)
        return u"  * [wiki:%s %s]" % (page_name, self._get_language_name(lang_code))

    def _get_current_lang_link(self, lang_code):
        return u"  * '''%s'''" % self._get_language_name(lang_code)

    def expand_macro(self, formatter, name, args):
        """
        Return a list of translated pages with the native language names.
        The list of languages supported can be configured by adding new
        entries to TracLanguages page. Refer to ISO 639-1 for more information.
        """

        page_name = formatter.context.resource.id
        (base_page_name, lang_code) = self._get_page_info(page_name)

        lang_link_list = []
        for translation in self._get_translations(base_page_name):
            if translation != lang_code:
                lang_link_list.append(self._get_lang_link(base_page_name, translation))
            else:
                lang_link_list.append(self._get_current_lang_link(lang_code))

        out = StringIO()
        Formatter(self.env, formatter.context).format(u'\n'.join(lang_link_list), out)

        return u"""
<div class="wiki-toc trac-nav" style="clear:both">
<h4>Translations:</h4>
%s
</div>""" % out.getvalue()

