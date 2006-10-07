from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from time import clock
import re

CAMEL     = r"!?(?<!/|\?)\b[A-Z][a-z]+(?:[A-Z][a-z]*[a-z/])+" + \
             "(?:#[A-Za-z0-9]+)?(?=\Z|\s|[.,;:!?\)}\]])"
FANCY     = r"(\[wiki:([^\] ]+) *.*?\])"
EXCLUDE   = r"(?s)(`[^`]*`)|(\[.*?\])|({{{.*?}}})"


class WantedPagesMacro(Component):
    implements(IWikiMacroProvider)

    index = {}

    def get_macros(self):
        return ['wantedPages']

    def get_macro_description(self, name):
        return 'Lists all wiki pages that are linked to but not created in '+ \
         'wikis, ticket descriptions and ticket comments.'

    def render_macro(self, req, name, content):
        texts = None

        wikiTexts = {}
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name, text FROM wiki ORDER BY version")
        for (name, text) in cursor:
            wikiTexts[name] = text
            self.index[name] = name
        texts = wikiTexts.values()

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT description FROM ticket")
        for (text,) in cursor:
            texts.append(text)

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT newvalue FROM ticket_change WHERE field='comment'")
        for (text,) in cursor:
            texts.append(text)

        pages = self.findBrokenLinks(texts, req).values()

        wikiList = ''
        pages.sort()
        for page in pages:
            wikiList += ('  * %s\n' % page)

        return wiki_to_html(wikiList, self.env, req)

    def findBrokenLinks(self, texts, req):
        camel = re.compile(CAMEL)
        fancy = re.compile(FANCY)
        exclude = re.compile(EXCLUDE)
        wantedIndex = {}

        for text in texts:
            text = self.removeBlocks(text) # regex does not work well for nested blocks
            matches = exclude.findall(text)
            for pre, bracket, block in matches:
                text = text.replace(pre, '')
                text = text.replace(block, '')
                if not bracket.startswith('[wiki:'):
                    text = text.replace(bracket, '')

            matches = fancy.findall(text)
            for fullLink, page in matches:
                if page.find('#') != -1:
                    page = page[:page.find('#')]

                if not self.index.has_key(page) and page[0] is not '!':
                    wantedIndex[page] = fullLink
                text = text.replace(fullLink, '') # remove so no CamelCase detected below

            matches = camel.findall(text)
            for page in matches:
                if page.find('#') != -1:
                    page = page[:page.find('#')]

                if not self.index.has_key(page) and page[0] is not '!':
                    wantedIndex[page] = page

        return wantedIndex

    def removeBlocks(self, text):
        while text.find('{{{') >= 0:
            clear, rem = text.split('{{{', 1)            
            rem = self._extractBlock(rem)
            text = clear + rem

        return text

    def _extractBlock(self, s):
        cleaned = ''
        if s.find('{{{') >= 0 and s.find('{{{') < s.find('}}}'):
            first, second = s.split('{{{', 1)
            s = self._extractBlock(second)

        if s.find('}}}') >= 0:
            inside, outside = s.split('}}}', 1)
            cleaned = outside
        else:
            cleaned = s # no closing braces
        return cleaned
