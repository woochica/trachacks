# -*- coding: utf-8 -*-

""" Macro to show the translated pages list. """

__author__ = 'Zhang Cong (ftofficer)'
__version__ = '1.0'

from genshi.builder import tag

from trac.wiki.macros import WikiMacroBase
from StringIO import StringIO
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage

class TranslatedPagesMacro(WikiMacroBase):
    """Macro to show the translated pages list."""

    SUPPORT_LANGUAGES = {
        'en' : u'English',
        'ru' : u'Русский',
        'be' : u'Беларуская мова',
        'da' : u'dansk',
        'es' : u'español',
        'nl' : u'Nederlands',
        'sv' : u'Svenska',
        'zh' : u'中文',
        }

    def __init__(self):
        self.supported_languages = TranslatedPagesMacro.SUPPORT_LANGUAGES.keys()
        self.supported_languages.sort()

    def _get_language_name(self, lang_code):
        if TranslatedPagesMacro.SUPPORT_LANGUAGES.has_key(lang_code):
            return TranslatedPagesMacro.SUPPORT_LANGUAGES[lang_code]
        else:
            return lang_code
            
    def _seems_like_lang_code(self, lang_code):
        if len(lang_code) != 2 : return False
        if not lang_code.islower() : return False
        return lang_code.isalpha()
        
    def _get_wiki_info(self, wiki_id):
        wiki_lang_code = 'en'
        wiki_base_name = wiki_id
        
        wiki_lang_code_start = wiki_id.rfind('/')
        if wiki_lang_code_start != -1:
            wiki_lang_code = wiki_id[wiki_lang_code_start+1:]
            wiki_base_name = wiki_id[:wiki_lang_code_start]
        
        if wiki_lang_code not in TranslatedPagesMacro.SUPPORT_LANGUAGES.keys(): # Unknown wiki language.
            if not self._seems_like_lang_code(wiki_lang_code): # seems don't like a language code.
                wiki_lang_code = 'en'
                wiki_base_name = wiki_id

        return (wiki_base_name, wiki_lang_code)
    
    def _is_translated_wiki_exists(self, wiki_base_name, lang_code):
        if lang_code == 'en':
            wiki_id = wiki_base_name
        else:
            wiki_id = '%s/%s' % (wiki_base_name, lang_code)
    
        wiki_page = WikiPage(self.env, wiki_id)
        return wiki_page.exists
        
    def _get_lang_link(self, wiki_base_name, lang_code, formatter):
        if lang_code != 'en':
            wiki_id = u'%s/%s' % (wiki_base_name, lang_code)
        else:
            wiki_id = wiki_base_name
        
        text = u'  * [wiki:%s %s]' % (wiki_id, self._get_language_name(lang_code))
        
        return text
    
    def expand_macro(self, formatter, name, args):
        """Return a list of translated pages with the native language names.
        The list of languages supported can be configured by the SUPPORT_LANGUAGES
        class member. Refer to iso639.1 for more information.
        """

        wiki_id = formatter.context.resource.id
        
        (wiki_base_name, wiki_lang_code) = self._get_wiki_info(wiki_id)

        lang_link_list = []

        for lang_code in self.supported_languages:
            if self._is_translated_wiki_exists(wiki_base_name, lang_code):
                if lang_code != wiki_lang_code:
                    lang_link_list.append(self._get_lang_link(wiki_base_name, lang_code, formatter))

        text = '\n'.join(lang_link_list)
                    
        out = StringIO()
        Formatter(self.env, formatter.context).format(text, out)

        return '<div class="wiki-toc trac-nav"><h4>Other Languages:</h4>' + out.getvalue() + '</div>'