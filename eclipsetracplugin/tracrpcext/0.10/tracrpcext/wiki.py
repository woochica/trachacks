
import xmlrpclib

from trac.core import *
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from tracrpc.api import IXMLRPCHandler

class WikiExtRPC(Component):
    """ Additional Wiki XML-RPC API. """

    implements(IXMLRPCHandler)

    def __init__(self):
        self.wiki = WikiSystem(self.env)

    def xmlrpc_namespace(self):
        return 'wikiext'

    def xmlrpc_methods(self):
        yield ('WIKI_VIEW', ((list, str), ), self.getPageVersions)
        yield ('WIKI_VIEW', ((bool, str), ), self.hasChildren)
        yield ('WIKI_VIEW', ((list, str), ), self.getChildren)
        yield ('WIKI_VIEW', ((dict,), ), self.getMacros)

    def _page_info(self, name, time, author, version, comment=''):
        return dict(name=name, 
                    lastModified=xmlrpclib.DateTime(int(time)),
                    author=author, 
                    version=int(version), 
                    comment=(comment or '') )

    def getPage(self, req, pagename, version=None):
        """ Get the raw Wiki text of page, latest version. """
        page = WikiPage(self.env, pagename, version)
        if page.exists:
            return page.text
        else:
            msg = 'Wiki page "%s" does not exist' % pagename
            if version is not None:
                msg += ' at version %s' % version
            raise xmlrpclib.Fault(0, msg)
            
    def getPageVersions(self, req, pagename):
        '''Return an array of page versions info'''
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT version, author, comment, time FROM wiki'
                       ' WHERE name = %s ORDER BY version DESC', (pagename,))
        result = []
        for version, author, comment, time in cursor:
            result.append(self._page_info(pagename, time, author, version, comment))
        return result
    
    def hasChildren(self, req, pagename):
        """ Returns true if the page has children. """
        if pagename: pagename += '/'
        res = False
        for i in self.wiki.get_pages( pagename ):
            res = True
            break
        return res

    def getChildren(self, req, pagename):
        """ Returns a list of all pages. The result is an array of utf8 pagenames. """
        if pagename:
            pagename += '/'
        pages = list( self.wiki.get_pages( pagename ) )
        pages.sort()
        children = {}
        for page in pages:
            # print 'Complete name: "%s"' % page
            relname = page.replace( pagename, '' )
            # print 'RELNAME: "%s"' % relname
             
            if relname.find( '/' ) == -1:
                # We only look for direct children
                children[ page ] = { 'exists' : True,
                                     'hasChildren' : False }
            else:
                # The page does not really exists, but it does have
                # children, so we have to return it,
                name = pagename + relname.split( '/', 1 )[0]
                if not children.has_key( name ):
                    children[ name ] = { 'exists' : False, 
                                        'hasChildren' : True }
                else:
                    children[ name ][ 'hasChildren' ] = True
                    
        return children
    
    def getMacros(self, req):
        '''Return the list of registered wiki macros'''
        macros = {}
        for plugin in self.wiki.macro_providers:
            for macro in plugin.get_macros():
                desc = plugin.get_macro_description( macro )
                if not desc:
                    desc = ''
                macros[ macro ] = desc 
        return macros

