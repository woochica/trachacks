from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
import re

REGEX = r" !?(?<![/?])\b[A-Z][a-z]+(?:[A-Z][a-z]*[a-z/])+" + \
         "(?:#[A-Za-z0-9]+)?(?=\Z|\s|[.,;:!?\)}\]])[ !\.?:)]"

class WantedPagesMacro(Component):
    implements(IWikiMacroProvider)

    index = {}
    wantedIndex = {}

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

        regex = re.compile(REGEX)
        excludedRegex = re.compile(r"`[^`]*`|\[.*?\]|=.*?=")
        excludedMultiline = re.compile(r"{{{.*?}}}", re.S)
        for text in texts:
            excludes = excludedRegex.findall(text)
            for s in excludes:
                if not s.startswith('[wiki:'):
                    text = text.replace(s, '')
            excludes = excludedMultiline.findall(text)
            for s in excludes:                
                text = text.replace(s, '')
                    
            matches = regex.findall(text)
            for match in matches:
                page = match[:len(match) - 1].strip() #strip trailing char            
                if page.find('#') != -1:
                    page = page[:page.find('#')]                

                if not self.index.has_key(page) and page[0] is not '!':
                    self.wantedIndex[page] = page

        wikiList = ''
        pages = self.wantedIndex.values()
        pages.sort()
        for page in pages:
            wikiList += ('  * %s\n' % page)

        return wiki_to_html(wikiList, self.env, req)
