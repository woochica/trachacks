# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import os
from datetime import datetime

from trac.attachment import Attachment
from trac.core import *
from trac.mimeview import Context
from trac.resource import Resource, ResourceNotFound
from trac.wiki.api import WikiSystem, IWikiPageManipulator
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html, format_to_html

from tracrpc.api import IXMLRPCHandler, expose_rpc, Binary
from tracrpc.util import StringIO, to_utimestamp, from_utimestamp

__all__ = ['WikiRPC']

class WikiRPC(Component):
    """Superset of the
    [http://www.jspwiki.org/Wiki.jsp?page=WikiRPCInterface2 WikiRPC API]. """

    implements(IXMLRPCHandler)

    manipulators = ExtensionPoint(IWikiPageManipulator)

    def __init__(self):
        self.wiki = WikiSystem(self.env)

    def xmlrpc_namespace(self):
        return 'wiki'

    def xmlrpc_methods(self):
        yield (None, ((dict, datetime),), self.getRecentChanges)
        yield ('WIKI_VIEW', ((int,),), self.getRPCVersionSupported)
        yield (None, ((str, str), (str, str, int),), self.getPage)
        yield (None, ((str, str, int),), self.getPage, 'getPageVersion')
        yield (None, ((str, str), (str, str, int)), self.getPageHTML)
        yield (None, ((str, str), (str, str, int)), self.getPageHTML, 'getPageHTMLVersion')
        yield (None, ((list,),), self.getAllPages)
        yield (None, ((dict, str), (dict, str, int)), self.getPageInfo)
        yield (None, ((dict, str, int),), self.getPageInfo, 'getPageInfoVersion')
        yield (None, ((bool, str, str, dict),), self.putPage)
        yield (None, ((list, str),), self.listAttachments)
        yield (None, ((Binary, str),), self.getAttachment)
        yield (None, ((bool, str, Binary),), self.putAttachment)
        yield (None, ((bool, str, str, str, Binary),
                               (bool, str, str, str, Binary, bool)),
                               self.putAttachmentEx)
        yield (None, ((bool, str),(bool, str, int)), self.deletePage)
        yield (None, ((bool, str),), self.deleteAttachment)
        yield ('WIKI_VIEW', ((list, str),), self.listLinks)
        yield ('WIKI_VIEW', ((str, str),), self.wikiToHtml)

    def _fetch_page(self, req, pagename, version=None):
        # Helper for getting the WikiPage that performs basic checks
        page = WikiPage(self.env, pagename, version)
        req.perm(page.resource).require('WIKI_VIEW')
        if page.exists:
            return page
        else:
            msg = 'Wiki page "%s" does not exist' % pagename
            if version is not None:
                msg += ' at version %s' % version
            raise ResourceNotFound(msg)

    def _page_info(self, name, when, author, version, comment):
        return dict(name=name, lastModified=when,
                    author=author, version=int(version), comment=comment)

    def getRecentChanges(self, req, since):
        """ Get list of changed pages since timestamp """
        since = to_utimestamp(since)
        wiki_realm = Resource('wiki')
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, time, author, version, comment '
                       'FROM wiki w1 '
                       'WHERE time >= %s '
                       'AND version = (SELECT MAX(version) '
                       '               FROM wiki w2 '
                       '               WHERE w2.name=w1.name) '
                       'ORDER BY time DESC', (since,))
        result = []
        for name, when, author, version, comment in cursor:
            if 'WIKI_VIEW' in req.perm(wiki_realm(id=name, version=version)):
                result.append(
                    self._page_info(name, from_utimestamp(when),
                                    author, version, comment))
        return result

    def getRPCVersionSupported(self, req):
        """ Returns 2 with this version of the Trac API. """
        return 2

    def getPage(self, req, pagename, version=None):
        """ Get the raw Wiki text of page, latest version. """
        page = self._fetch_page(req, pagename, version)
        return page.text

    def getPageHTML(self, req, pagename, version=None):
        """ Return latest version of page as rendered HTML, utf8 encoded. """
        page = self._fetch_page(req, pagename, version)
        fields = {'text': page.text}
        for manipulator in self.manipulators:
            manipulator.prepare_wiki_page(req, page, fields)
        context = Context.from_request(req, page.resource, absurls=True)
        html = format_to_html(self.env, context, fields['text'])
        return '<html><body>%s</body></html>' % html.encode('utf-8')

    def getAllPages(self, req):
        """ Returns a list of all pages. The result is an array of utf8 pagenames. """
        pages = []
        for page in self.wiki.get_pages():
            if 'WIKI_VIEW' in req.perm(Resource('wiki', page)):
                pages.append(page)
        return pages

    def getPageInfo(self, req, pagename, version=None):
        """ Returns information about the given page. """
        page = WikiPage(self.env, pagename, version)
        req.perm(page.resource).require('WIKI_VIEW')
        if page.exists:
            last_update = page.get_history().next()
            return self._page_info(page.name, last_update[1],
                                   last_update[2], page.version, page.comment)

    def putPage(self, req, pagename, content, attributes):
        """ writes the content of the page. """
        page = WikiPage(self.env, pagename)
        if page.readonly:
            req.perm(page.resource).require('WIKI_ADMIN')
        elif not page.exists:
            req.perm(page.resource).require('WIKI_CREATE')
        else:
            req.perm(page.resource).require('WIKI_MODIFY')

        page.text = content
        if req.perm(page.resource).has_permission('WIKI_ADMIN'):
            page.readonly = attributes.get('readonly') and 1 or 0

        page.save(attributes.get('author', req.authname),
                  attributes.get('comment'), req.remote_addr)
        return True

    def deletePage(self, req, name, version=None):
        """Delete a Wiki page (all versions) or a specific version by
        including an optional version number. Attachments will also be
        deleted if page no longer exists. Returns True for success."""
        wp = WikiPage(self.env, name, version)
        req.perm(wp.resource).require('WIKI_DELETE')
        try:
            wp.delete(version)
            return True
        except:
            return False

    def listAttachments(self, req, pagename):
        """ Lists attachments on a given page. """
        for a in Attachment.select(self.env, 'wiki', pagename):
            if 'ATTACHMENT_VIEW' in req.perm(a.resource):
                yield pagename + '/' + a.filename

    def getAttachment(self, req, path):
        """ returns the content of an attachment. """
        pagename, filename = os.path.split(path)
        attachment = Attachment(self.env, 'wiki', pagename, filename)
        req.perm(attachment.resource).require('ATTACHMENT_VIEW')
        return Binary(attachment.open().read())

    def putAttachment(self, req, path, data):
        """ (over)writes an attachment. Returns True if successful.
        
        This method is compatible with WikiRPC.  `putAttachmentEx` has a more
        extensive set of (Trac-specific) features. """
        pagename, filename = os.path.split(path)
        self.putAttachmentEx(req, pagename, filename, None, data)
        return True

    def putAttachmentEx(self, req, pagename, filename, description, data, replace=True):
        """ Attach a file to a Wiki page. Returns the (possibly transformed)
        filename of the attachment.
        
        Use this method if you don't care about WikiRPC compatibility. """
        if not WikiPage(self.env, pagename).exists:
            raise ResourceNotFound, 'Wiki page "%s" does not exist' % pagename
        if replace:
            try:
                attachment = Attachment(self.env, 'wiki', pagename, filename)
                req.perm(attachment.resource).require('ATTACHMENT_DELETE')
                attachment.delete()
            except TracError:
                pass
        attachment = Attachment(self.env, 'wiki', pagename)
        req.perm(attachment.resource).require('ATTACHMENT_CREATE')
        attachment.author = req.authname
        attachment.description = description
        attachment.insert(filename, StringIO(data.data), len(data.data))
        return attachment.filename

    def deleteAttachment(self, req, path):
        """ Delete an attachment. """
        pagename, filename = os.path.split(path)
        if not WikiPage(self.env, pagename).exists:
            raise ResourceNotFound, 'Wiki page "%s" does not exist' % pagename
        attachment = Attachment(self.env, 'wiki', pagename, filename)
        req.perm(attachment.resource).require('ATTACHMENT_DELETE')
        attachment.delete()
        return True

    def listLinks(self, req, pagename):
        """ ''Not implemented'' """
        return []

    def wikiToHtml(self, req, text):
        """ Render arbitrary Wiki text as HTML. """
        return unicode(wiki_to_html(text, self.env, req, absurls=1))
