try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import xmlrpclib
import posixpath

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html
from trac.attachment import Attachment
from tracrpc.api import IXMLRPCHandler, expose_rpc
from tracrpc.util import to_timestamp

class WikiRPC(Component):
    """ Implementation of the [http://www.jspwiki.org/Wiki.jsp?page=WikiRPCInterface2 WikiRPC API]. """

    implements(IXMLRPCHandler)

    def __init__(self):
        self.wiki = WikiSystem(self.env)

    def xmlrpc_namespace(self):
        return 'wiki'

    def xmlrpc_methods(self):
        yield ('WIKI_VIEW', ((dict, xmlrpclib.DateTime),), self.getRecentChanges)
        yield ('WIKI_VIEW', ((int,),), self.getRPCVersionSupported)
        yield ('WIKI_VIEW', ((str, str), (str, str, int),), self.getPage)
        yield ('WIKI_VIEW', ((str, str, int),), self.getPage, 'getPageVersion')
        yield ('WIKI_VIEW', ((str, str), (str, str, int)), self.getPageHTML)
        yield ('WIKI_VIEW', ((str, str), (str, str, int)), self.getPageHTML, 'getPageHTMLVersion')
        yield ('WIKI_VIEW', ((list,),), self.getAllPages)
        yield ('WIKI_VIEW', ((dict, str), (dict, str, int)), self.getPageInfo)
        yield ('WIKI_VIEW', ((dict, str, int),), self.getPageInfo, 'getPageInfoVersion')
        yield ('WIKI_CREATE', ((bool, str, str, dict),), self.putPage)
        yield ('WIKI_VIEW', ((list, str),), self.listAttachments)
        yield ('WIKI_VIEW', ((xmlrpclib.Binary, str),), self.getAttachment)
        yield ('WIKI_MODIFY', ((bool, str, xmlrpclib.Binary),), self.putAttachment)
        yield ('WIKI_MODIFY', ((bool, str, str, str, xmlrpclib.Binary),
                               (bool, str, str, str, xmlrpclib.Binary, bool)),
                               self.putAttachmentEx)
        yield ('WIKI_DELETE', ((bool, str),), self.deleteAttachment)
        yield ('WIKI_VIEW', ((list, str),), self.listLinks)
        yield ('WIKI_VIEW', ((str, str),), self.wikiToHtml)

    def _page_info(self, name, time, author, version):
        return dict(name=name, lastModified=xmlrpclib.DateTime(int(time)),
                    author=author, version=int(version))

    def getRecentChanges(self, req, since):
        """ Get list of changed pages since timestamp """
        since = to_timestamp(since)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, max(time), author, version FROM wiki'
                       ' WHERE time >= %s GROUP BY name ORDER BY max(time) DESC', (since,))
        result = []
        for name, time, author, version in cursor:
            result.append(self._page_info(name, time, author, version))
        return result

    def getRPCVersionSupported(self, req):
        """ Returns 2 with this version of the Trac API. """
        return 2

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

    def getPageHTML(self, req, pagename, version=None):
        """ Return page in rendered HTML, latest version. """
        text = self.getPage(req, pagename, version)
        html = wiki_to_html(text, self.env, req, absurls=1)
        return '<html><body>%s</body></html>' % html

    def getAllPages(self, req):
        """ Returns a list of all pages. The result is an array of utf8 pagenames. """
        return list(self.wiki.get_pages())

    def getPageInfo(self, req, pagename, version=None):
        """ Returns information about the given page. """
        page = WikiPage(self.env, pagename, version)
        if page.exists:
            last_update = page.get_history().next()
            return self._page_info(page.name, last_update[1], last_update[2],
                                   page.version)

    def putPage(self, req, pagename, content, attributes):
        """ writes the content of the page. """
        page = WikiPage(self.env, pagename)
        if page.readonly:
            req.perm.assert_permission('WIKI_ADMIN')
        elif not page.exists:
            req.perm.assert_permission('WIKI_CREATE')
        else:
            req.perm.assert_permission('WIKI_MODIFY')

        page.text = content
        if req.perm.has_permission('WIKI_ADMIN'):
            page.readonly = attributes.get('readonly') and 1 or 0

        page.save(attributes.get('author', req.authname),
                  attributes.get('comment'),
                  req.remote_addr)
        return True

    def listAttachments(self, req, pagename):
        """ Lists attachments on a given page. """
        return [pagename + '/' + a.filename for a in Attachment.select(self.env, 'wiki', pagename)]

    def getAttachment(self, req, path):
        """ returns the content of an attachment. """
        pagename, filename = posixpath.split(path)
        attachment = Attachment(self.env, 'wiki', pagename, filename)
        return xmlrpclib.Binary(attachment.open().read())

    def putAttachment(self, req, path, data):
        """ (over)writes an attachment. Returns True if successful.
        
        This method is compatible with WikiRPC.  `putAttachmentEx` has a more
        extensive set of (Trac-specific) features. """
        pagename, filename = posixpath.split(path)
        self.putAttachmentEx(req, pagename, filename, None, data)
        return True

    def putAttachmentEx(self, req, pagename, filename, description, data, replace=True):
        """ Attach a file to a Wiki page. Returns the (possibly transformed)
        filename of the attachment.
        
        Use this method if you don't care about WikiRPC compatibility. """
        if not WikiPage(self.env, pagename).exists:
            raise TracError, 'Wiki page "%s" does not exist' % pagename
        if replace:
            try:
                attachment = Attachment(self.env, 'wiki', pagename, filename)
                attachment.delete()
            except TracError:
                pass
        attachment = Attachment(self.env, 'wiki', pagename)
        attachment.author = req.authname or 'anonymous'
        attachment.description = description
        attachment.insert(filename, StringIO(data.data), len(data.data))
        return attachment.filename

    def deleteAttachment(self, req, path):
        """ Delete an attachment. """
        pagename, filename = posixpath.split(path)
        if not WikiPage(self.env, pagename).exists:
            raise TracError, 'Wiki page "%s" does not exist' % pagename
        attachment = Attachment(self.env, 'wiki', pagename, filename)
        attachment.delete()
        return True

    def listLinks(self, req, pagename):
        """ ''Not implemented'' """
        return []

    def wikiToHtml(self, req, text):
        """ Render arbitrary Wiki text as HTML. """
        return unicode(wiki_to_html(text, self.env, req, absurls=1))
