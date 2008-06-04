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
from trac.util import sorted, embedded_numbers

from genshi.builder import tag

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
    implements(IPermissionRequestor, IRequestHandler, IHTMLPreviewAnnotator)

    # ITextAnnotator methods
    def get_annotation_type(self):
    	return 'lineno', 'Line', 'Line numbers'

    def get_annotation_data(self, context):
        return None

    def annotate_row(self, context, row, lineno, line, data):
        row.append(tag.th(id='L%s' % lineno)(
            tag.a(lineno, href='javascript:setLineNum(%s)' % lineno)
        ))
    
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

        data = {}
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
        context = Context.from_request(req, 'source', path, node.created_rev)

        path_links = self.get_path_links_CRB(self.env.href, path, rev)
        if len(path_links) > 1:
            add_link(req, 'up', path_links[-2]['href'], 'Parent directory')

        data = {
            'path': path, 'rev': node.rev, 'stickyrev': rev,
            'revision': rev or repos.youngest_rev,
            'props': dict([(util.escape(name), util.escape(value))
                           for name, value in node.get_properties().items()
                           if not name in hidden_properties]),
            'log_href': util.escape(self.env.href.log(path, rev=rev or None)),
            'path_links': path_links,
            'dir': node.isdir and self._render_directory(req, repos, node, rev),
            'file': node.isfile and self._render_file(req, context, repos, node, rev) 
        }

        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/code.css')
        
	return 'peerReviewBrowser.html', data, None

    # Internal methods

    def get_path_links_CRB(self, href, fullpath, rev):

        path = '/'
        links = [{'name': 'root',
                  'href': href.peerReviewBrowser(path, rev=rev)}]

        for part in [p for p in fullpath.split('/') if p]:
            path += part + '/'
            links.append({
                'name': part,
                'href': href.peerReviewBrowser(path, rev=rev)
                })
        return links

    def _render_directory(self, req, repos, node, rev=None):
        req.perm.assert_permission('BROWSER_VIEW')

        order = req.args.get('order', 'name').lower()
        desc = req.args.has_key('desc')

        # Entries metadata
        class entry(object):
            __slots__ = 'name rev kind isdir path content_length'.split()
            def __init__(self, node):
                for f in entry.__slots__:
                    setattr(self, f, getattr(n, f))
            def display(self):
                result = ''
                for f in entry.__slots__:
                    result = "%s slot: %s, value: %s;" % (result, f, getattr(n, f))

                return result


        info = []

        if order == 'date':
            def file_order(a):
                return changes[a.rev].date
        elif order == 'size':
            def file_order(a):
                return (a.content_length,
                        embedded_numbers(a.name.lower()))
        else:
            def file_order(a):
                return embedded_numbers(a.name.lower())

        dir_order = desc and 1 or -1

        def browse_order(a):
            return a.isdir and dir_order or 0, file_order(a)

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
        changes = get_changes(repos, [i['rev'] for i in info])

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

        return {'order': order, 'desc': desc and 1 or None,
                'items': info, 'changes': changes }

    def _render_file(self, req, context, repos, node, rev=None):
        req.perm(context.resource).require('FILE_VIEW')

        changeset = repos.get_changeset(node.rev)

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

        content = node.get_content()
        chunk = content.read(CHUNK_SIZE)

        format = req.args.get('format')
        if format in ('raw', 'txt'):
            req.send_response(200)
            req.send_header('Content-Type',
                            format == 'txt' and 'text/plain' or mime_type)
            req.send_header('Content-Length', node.content_length)
            req.send_header('Last-Modified', util.http_date(node.last_modified))
            req.end_headers()

            while 1:
                if not chunk:
                    raise RequestDone
                req.write(chunk)
                chunk = content.read(CHUNK_SIZE)
        else:
            # Generate HTML preview
            mimeview = Mimeview(self.env)

            # The changeset corresponding to the last change on `node`
            # is more interesting than the `rev` changeset.
            changeset = repos.get_changeset(node.rev)

            # add ''Plain Text'' alternate link if needed
            if not is_binary(chunk) and mime_type != 'text/plain':
                plain_href = req.href.browser(node.path, rev=rev, format='txt')
                add_link(req, 'alternate', plain_href, 'Plain Text',
                         'text/plain')

            add_stylesheet(req, 'common/css/code.css')

            raw_href = self.env.href.peerReviewBrowser(node.path, rev=rev and node.rev,
                                             format='raw')
            preview_data = mimeview.preview_data(context, node.get_content(),
                                                    node.get_content_length(),
                                                    mime_type, node.created_path,
                                                    raw_href,
                                                    annotations=['lineno'])

            add_link(req, 'alternate', raw_href, 'Original Format', mime_type)

            return {
                'changeset': changeset,
                'size': node.content_length,
                'preview': preview_data['rendered'],
                'annotate': False,
                'rev': node.rev,
                'changeset_href': util.escape(self.env.href.changeset(node.rev)),
                'date': util.format_datetime(changeset.date),
                'age': util.pretty_timedelta(changeset.date),
                'author': changeset.author or 'anonymous',
                'message': wiki_to_html(changeset.message or '--', self.env, req,
                                        escape_newlines=True)
                }

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
