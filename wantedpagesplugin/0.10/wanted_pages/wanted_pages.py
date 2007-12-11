from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from time import clock
import re

CAMEL     = r"!?(?<!/|\?)\b[A-Z][a-z]+(?:[A-Z][a-z]*[a-z/])+" + \
             "(?:#[A-Za-z0-9]+)?(?=\Z|\s|[.,;:!?\)}\]])"
FANCY     = r"(\[wiki:([^\] ]+) *.*?\])"
EXCLUDE   = r"(?s)(`[^`]*`)|(\[.*?\])|({{{.*?}}})"

camel_re = re.compile(CAMEL)
fancy_re = re.compile(FANCY)
exclude_re = re.compile(EXCLUDE)

wiki_sql = "SELECT name, text FROM wiki ORDER BY version DESC"
ticket_sql= """SELECT id, description FROM ticket 
    UNION 
    SELECT ticket, newvalue FROM ticket_change WHERE field='comment'        
"""

def exec_wiki_sql(db):
    cursor = db.cursor()
    cursor.execute(wiki_sql)
    rs = [(name, text) for name, text in cursor]
    cursor.close()
    return rs

def exec_ticket_sql(db):
    cursor = db.cursor()
    cursor.execute(ticket_sql)
    rs = [(id, text) for id, text in cursor]
    cursor.close()
    return rs

class WantedPagesMacro(Component):
    implements(IWikiMacroProvider)

    index = {}

    def get_macros(self):
        return ['wantedPages', 'WantedPages']

    def get_macro_description(self, name):
        return 'Lists all wiki pages that are linked to but not created in '+ \
         'wikis, ticket descriptions and ticket comments. Use `[[WantedPages(show_referrers)]]` ' +\
         'to show referring pages.'

    def render_macro(self, req, name, content):
        showReferrers = False
        if content and 'show_referrers' in content:
            showReferrers = True
        return wiki_to_html(self.buildWikiText(showReferrers), self.env, req)
    
    def buildWikiText(self, showReferrers=False):
        texts = [] # list of referrer link, wiki-able text tuples
        wantedPages = {} # referrers indexed by page
        wikiPages = [] # list of wikiPages seen
        db = self.env.get_db_cnx()

        for name, text in exec_wiki_sql(db): # query is ordered by latest version first
            if name not in wikiPages:
                wikiPages.append(name)
                self.index[name] = name
                texts.append(('[wiki:%s]' % name, text))

        for id, text in exec_ticket_sql(db):
            texts.append(('#%s' % id, text))
        
        for referrer, text in texts:
            for link in self.findBrokenLinks(text):
                if link not in wantedPages:
                    wantedPages[link] = []
                wantedPages[link].append(referrer)

        wikiList = ''
        for page in sorted(wantedPages.keys()):
            ref = ''
            if showReferrers:
                ref = ' (Linked from %s)' % ', '.join(wantedPages[page])
            wikiList = '%s  * [wiki:%s]%s\n' % (wikiList, page, ref)    

        return wikiList

    def findBrokenLinks(self, text):
        wantedPages = []
        
        text = self.removeBlocks(text) # regex does not work well for nested blocks
        matches = exclude_re.findall(text)
        for pre, bracket, block in matches:
            text = text.replace(pre, '')
            text = text.replace(block, '')
            if not bracket.startswith('[wiki:'):
                text = text.replace(bracket, '')

        matches = fancy_re.findall(text)
        for fullLink, page in matches:
            if page.find('#') != -1:
                page = page[:page.find('#')]

            if not self.index.has_key(page) and page[0] != '!':
                wantedPages.append(page)

            text = text.replace(fullLink, '') # remove so no CamelCase detected below

        matches = camel_re.findall(text)
        for page in matches:
            if page.find('#') != -1:
                page = page[:page.find('#')]

            if not self.index.has_key(page) and page[0] != '!':
                wantedPages.append(page)
                
        return wantedPages

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
