#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

from __future__ import generators
import re
import urllib

from trac import util
from trac.core import *
from trac.mimeview import *
from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider
from trac.web import IRequestHandler, RequestDone
from trac.web.chrome import add_link, add_stylesheet
from trac.wiki import wiki_to_html, wiki_to_oneliner, IWikiSyntaxProvider
from trac.versioncontrol.web_ui.util import *

IMG_RE = re.compile(r"\.(gif|jpg|jpeg|png)(\?.*)?$", re.IGNORECASE)

CHUNK_SIZE = 4096

DIGITS = re.compile(r'[0-9]+')
def _natural_order(x, y):
    """Comparison function for natural order sorting based on
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/214202."""
    nx = ny = 0
    while True:
        a = DIGITS.search(x, nx)
        b = DIGITS.search(y, ny)
        if None in (a, b):
            return cmp(x[nx:], y[ny:])
        r = (cmp(x[nx:a.start()], y[ny:b.start()]) or
             cmp(int(x[a.start():a.end()]), int(y[b.start():b.end()])))
        if r:
            return r
        nx, ny = a.end(), b.end()


class peerReviewBrowser(Component):
    implements(IPermissionRequestor, IRequestHandler, IWikiSyntaxProvider, IHTMLPreviewAnnotator)

    # ITextAnnotator methods
    def get_annotation_type(self):
    	return 'addFileNums', 'Line', 'Line numbers'
    
    def annotate_line(self, number, content):
    	return '<th id="L%s"><a href="javascript:setLineNum(%s)">%s</a></th>' % (number, number, number)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['BROWSER_VIEW', 'FILE_VIEW']

    # IRequestHandler methods

    def match_request(self, req):
        import re
        match = re.match(r'/(peerReviewBrowser|file)(?:(/.*))?', req.path_info)
        if match:
            req.args['path'] = match.group(2) or '/'
            if match.group(1) == 'file':
                # FIXME: This should be a permanent redirect
                req.redirect(self.env.href.peerReviewBrowser(req.args.get('path'),
                                                   rev=req.args.get('rev'),
                                                   format=req.args.get('format')))
            return True

    def process_request(self, req):
        path = req.args.get('path', '/')
        rev = req.args.get('rev')

        repos = self.env.get_repository(req.authname)

        try:
            node = get_existing_node(self.env, repos, path, rev)
        except:
            rev = repos.youngest_rev
            node = get_existing_node(self.env, repos, path, rev)
       
        hidden_properties = [p.strip() for p
                             in self.config.get('browser', 'hide_properties',
                                                'svk:merge').split(',')]
        req.hdf['title'] = path
        req.hdf['browser'] = {
            'path': path,
            'revision': rev or repos.youngest_rev,
            'props': dict([(util.escape(name), util.escape(value))
                           for name, value in node.get_properties().items()
                           if not name in hidden_properties]),
            'href': util.escape(self.env.href.peerReviewBrowser(path, rev=rev or
                                                      repos.youngest_rev)),
            'log_href': util.escape(self.env.href.log(path, rev=rev or None))
        }

        path_links = self.get_path_links_CRB(self.env.href, path, rev)
        if len(path_links) > 1:
            add_link(req, 'up', path_links[-2]['href'], 'Parent directory')
        req.hdf['browser.path'] = path_links

        if node.isdir:
            req.hdf['browser.is_dir'] = True
            self._render_directory(req, repos, node, rev)
        else:
            self._render_file(req, repos, node, rev)

        add_stylesheet(req, 'common/css/browser.css')
        return 'peerReviewBrowser.cs', None

    # Internal methods

    def get_path_links_CRB(self, href, path, rev):
        links = []
        parts = path.split('/')
        if not parts[-1]:
            parts.pop()
        path = '/'
        for part in parts:
            path = path + part + '/'
            links.append({
                'name': part or 'root',
                'href': util.escape(href.peerReviewBrowser(path, rev=rev))
            })
        return links

    def _render_directory(self, req, repos, node, rev=None):
        req.perm.assert_permission('BROWSER_VIEW')

        order = req.args.get('order', 'name').lower()
        req.hdf['browser.order'] = order
        desc = req.args.has_key('desc')
        req.hdf['browser.desc'] = desc and 1 or 0

        info = []
        for entry in node.get_entries():
            entry_rev = rev and entry.rev
            info.append({
                'name': entry.name,
                'fullpath': entry.path,
                'is_dir': int(entry.isdir),
                'content_length': entry.content_length,
                'size': util.pretty_size(entry.content_length),
                'rev': entry.rev,
                'permission': 1, # FIXME
                'log_href': util.escape(self.env.href.log(entry.path, rev=rev)),
                'browser_href': util.escape(self.env.href.peerReviewBrowser(entry.path,
                                                                  rev=rev))
            })
        changes = get_changes(self.env, repos, [i['rev'] for i in info])

        def cmp_func(a, b):
            dir_cmp = (a['is_dir'] and -1 or 0) + (b['is_dir'] and 1 or 0)
            if dir_cmp:
                return dir_cmp
            neg = desc and -1 or 1
            if order == 'date':
                return neg * cmp(changes[b['rev']]['date_seconds'],
                                 changes[a['rev']]['date_seconds'])
            elif order == 'size':
                return neg * cmp(a['content_length'], b['content_length'])
            else:
                return neg * _natural_order(a['name'].lower(),
                                            b['name'].lower())
        info.sort(cmp_func)

        req.hdf['browser.items'] = info
        req.hdf['browser.changes'] = changes

    def _render_file(self, req, repos, node, rev=None):
        req.perm.assert_permission('FILE_VIEW')

        changeset = repos.get_changeset(node.rev)  
        req.hdf['file'] = {  
            'rev': node.rev,  
            'changeset_href': util.escape(self.env.href.changeset(node.rev)),
            'date': util.format_datetime(changeset.date),
            'age': util.pretty_timedelta(changeset.date),
            'author': changeset.author or 'anonymous',
            'message': wiki_to_html(changeset.message or '--', self.env, req,
                                    escape_newlines=True)
        } 
        mime_type = node.content_type
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = get_mimetype(node.name) or mime_type or 'text/plain'

        # We don't have to guess if the charset is specified in the
        # svn:mime-type property
        ctpos = mime_type.find('charset=')
        if ctpos >= 0:
            charset = mime_type[ctpos + 8:]
        else:
            charset = None

        format = req.args.get('format')
        if format in ['raw', 'txt']:
            req.send_response(200)
            req.send_header('Content-Type',
                            format == 'txt' and 'text/plain' or mime_type)
            req.send_header('Content-Length', node.content_length)
            req.send_header('Last-Modified', util.http_date(node.last_modified))
            req.end_headers()

            content = node.get_content()
            while 1:
                chunk = content.read(CHUNK_SIZE)
                if not chunk:
                    raise RequestDone
                req.write(chunk)
        else:
            # Generate HTML preview
            mimeview = Mimeview(self.env)
            content = node.get_content().read(mimeview.max_preview_size)
            if not is_binary(content):
                if mime_type != 'text/plain':
                    plain_href = self.env.href.peerReviewBrowser(node.path,
                                                       rev=rev and node.rev,
                                                       format='txt')
                    add_link(req, 'alternate', plain_href, 'Plain Text',
                             'text/plain')

            raw_href = self.env.href.peerReviewBrowser(node.path, rev=rev and node.rev,
                                             format='raw')
            req.hdf['file'] = mimeview.preview_to_hdf(req, content, len(content),
                                                      mime_type, node.created_path,
                                                      raw_href, annotations=['addFileNums'])

            add_link(req, 'alternate', raw_href, 'Original Format', mime_type)

            add_stylesheet(req, 'common/css/code.css')

    # IWikiSyntaxProvider methods
    
    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        return [('repos', self._format_link),
                ('source', self._format_link),
                ('browser', self._format_link)]

    def _format_link(self, formatter, ns, path, label):
        match = IMG_RE.search(path)
        if formatter.flavor != 'oneliner' and match:
            return '<img src="%s" alt="%s" />' % \
                   (formatter.href.file(path, format='raw'), label)
        path, rev, line = get_path_rev_line(path)
        if line is not None:
            anchor = '#L%d' % line
        else:
            anchor = ''
        label = urllib.unquote(label)
        return '<a class="source" href="%s%s">%s</a>' \
               % (util.escape(formatter.href.peerReviewBrowser(path, rev=rev)), anchor,
                  label)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]
