# -*- coding: utf-8 -*-
"""
TracPastePlugin: code required for web interface handling
"""

import re
from genshi.builder import tag
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.resource import Resource, IResourceManager
from trac.config import BoolOption, IntOption, ListOption
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_stylesheet, add_link, Chrome
from trac.web.main import IRequestHandler
from trac.timeline.api import ITimelineEventProvider
from trac.util.datefmt import http_date
from trac.util.translation import _
from trac.mimeview.pygments import get_all_lexers

# import modules from this package
from model import Paste, get_pastes


class TracpastePlugin(Component):
    implements(INavigationContributor, ITemplateProvider, IRequestHandler, \
               IPermissionRequestor, ITimelineEventProvider)

    _url_re = re.compile(r'^/pastebin(?:/(\d+))?/?$')

    max_recent = IntOption('pastebin', 'max_recent', '10',
        """The maximum number of recent pastes to display on the
           index page. Default is 10.""")

    enable_other_formats = BoolOption('pastebin', 'enable_other_formats', 'true',
        """Whether pastes should be made available via the \"Download in
        other formats\" functionality. Enabled by default.""")

    filter_other_formats = ListOption('pastebin', 'filter_other_formats', '',
        """List of MIME types for which the \"Download in other formats\"
        functionality is disabled. Leave this option empty to allow
        download for all MIME types, otherwise set it to a comma-separated
        list of MIME types to filter (these are glob patterns, i.e. \"*\"
        can be used as a wild card).""")

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'pastebin'

    def get_navigation_items(self, req):
        if req.perm('pastebin').has_permission('PASTEBIN_VIEW'):
            yield ('mainnav', 'pastebin',
                  tag.a(_('Pastebin'), href=req.href.pastebin()) )

    # IPermissionRequestor methods
    def get_permission_actions(self):
        """ Permissions supported by the plugin. """
        return ['PASTEBIN_VIEW',
                ('PASTEBIN_CREATE', ['PASTEBIN_VIEW']),
                ('PASTEBIN_DELETE', ['PASTEBIN_VIEW']),
                ('PASTEBIN_ADMIN', ['PASTEBIN_CREATE', 'PASTEBIN_DELETE']),
               ]

    # IRequestHandler methods
    def match_request(self, req):
        m = self._url_re.search(req.path_info)
        if m is None:
            return False
        paste_id = m.group(1)
        if paste_id:
            req.args['paste_id'] = int(paste_id)
            req.args['new_paste'] = False
        else:
            req.args['paste_id'] = None
            req.args['new_paste'] = True
        return True

    def process_request(self, req):
        req.perm('pastebin').assert_permission('PASTEBIN_VIEW')
        add_stylesheet(req, 'pastebin/css/pastebin.css')
        add_stylesheet(req, 'common/css/code.css')

        if (not req.args):
            req.redirect(req.href.pastebin())
        
        # new post
        if req.args['new_paste']:
            title = req.args.get('title', 'untitled')
            author = req.args.get('author', req.authname)
            mimetype = req.args.get('mimetype', 'text/plain')
            data = req.args.get('data', '')
            error = False

            # check if we reply to a paste
            if 'reply' in req.args and req.args['reply'].isdigit():
                replyto = req.args['reply']
                paste = Paste(self.env, id=replyto)
                if paste:
                    title = paste.title
                    if not title.startswith('Re:'):
                        title = 'Re: ' + title
                    data = paste.data
                    mimetype = paste.mimetype
            else:
                replyto = '0'

            if 'delete' in req.args and req.args['delete'].isdigit():
                req.perm('pastebin').assert_permission('PASTEBIN_DELETE')
                delete = req.args['delete']
                paste = Paste(self.env, id=delete)
                if paste:
                    paste.delete()
                    data = {
                        'mode':         'delete',
                        'paste':        paste,
                    }
                    return 'pastebin.html', data, None

            if req.method == 'POST':
                req.perm('pastebin').assert_permission('PASTEBIN_CREATE')
                if not data.strip():
                    error = True
                else:
                    paste = Paste(self.env,
                        title=title,
                        author=author,
                        mimetype=mimetype,
                        data=data
                    )
                    paste.save()
                    req.redirect(req.href.pastebin(paste.id))

            data = {
                'mode':             'new',
                'replyto':          replyto,
                'mimetypes':        self._get_mimetypes(),
                'mimetype':         mimetype,
                'title':            title,
                'author':           author,
                'error':            error,
                'data':             data,
                'recent':           get_pastes(env=self.env, number=self.max_recent)
            }

        # show post
        else:
            req.perm('pastebin').assert_permission('PASTEBIN_VIEW')

            paste = Paste(self.env, req.args['paste_id'])

            # text format
            if req.args.get('format') in ('txt', 'raw') and self.enable_other_formats:
                if req.args['format'] == 'txt':
                    mimetype = 'text/plain'
                else:
                    mimetype = paste.mimetype

                if self._download_allowed(mimetype):
                    self.env.log.info("*** serving download")
                    content = paste.data
                    req.send_response(200)
                    req.send_header('Content-Type', mimetype)
                    req.send_header('Content-Length', len(content))
                    req.send_header('Last-Modified', http_date(paste.time))
                    req.end_headers()
                    if isinstance(content, unicode):
                        content = content.encode('utf-8')
                    req.write(content)
                    return
                else:
                    self.env.log.info("*** download denied")

            data = {
                'mode':             'show',
                'paste':            paste,
                'highlighter':      self._get_highlighter(paste.mimetype),
            }

            if self.enable_other_formats:
                if self._download_allowed(paste.mimetype):
                    # add link for original format
                    raw_href = req.href.pastebin(paste.id, format='raw')
                    add_link(req, 'alternate', raw_href, _('Original Format'), paste.mimetype)

                if paste.mimetype != 'text/plain' and self._download_allowed('text/plain'):
                    # add link for text format
                    plain_href = req.href.pastebin(paste.id, format='txt')
                    add_link(req, 'alternate', plain_href, _('Plain Text'), 'text/plain')

        return 'pastebin.html', data, None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('pastebin', resource_filename(__name__, 'htdocs'))]

    # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        if req.perm('pastebin').has_permission('PASTEBIN_VIEW'):
            yield('pastebin', _('Pastebin changes'))

    def get_timeline_events(self, req, start, stop, filters):
        if 'pastebin' in filters:
            pb_realm = Resource('pastebin')
            if not req.perm(pb_realm).has_permission('PASTEBIN_VIEW'):
                return
            add_stylesheet(req, 'pastebin/css/timeline.css')
            pastes = get_pastes(env=self.env, from_dt=start, to_dt=stop)
            for p in pastes:
                if req.perm(pb_realm(id=p["id"])).has_permission('PASTEBIN_VIEW'):
                    yield('pastebin', p["time"], p["author"], (p["id"],
                          p["title"]))
        return

    def render_timeline_event(self, context, field, event):
        p_id, p_title = event[3]
        if field == 'url':
            return context.href.pastebin(p_id)
        elif field == 'title':
            return tag(_('Pastebin: '), tag.em(p_title), _(' pasted'))

    # IResourceManager
    def get_resource_realm(self):
        yield 'pastebin'

    def get_resource_url(self, resource, href, **kwargs):
        return href.pastebin(resource.id)

    def get_resource_description(self, resource, format=None, context=None,
                                 **kwargs):
        p = Paste(self.env, resource.id)
        if context:
            return tag.a(_('Pastebin: ') + p.title,
                         href=context.href.pastebin(resource.id))
        else:
            return _('Pastebin: ') + p.title

    # private methods
    def _get_mimetypes(self):
        result = []
        for name, _, _, mimetypes in get_all_lexers():
            if mimetypes:
                result.append((mimetypes[0], name))
        result.sort(lambda a, b: cmp(a[1].lower(), b[1].lower()))
        return result

    def _get_highlighter(self, mimetype):
        if not mimetype:
            return _('unknown')

        mimetypes = self._get_mimetypes()
        for m, name in mimetypes:
            if m == mimetype:
                return name
        return _('unknown')

    def _download_allowed(self, mimetype):
        from fnmatch import fnmatchcase

        if not self.enable_other_formats:
            return False

        if not self.filter_other_formats:
            return True

        patterns = self.config['pastebin'].getlist('filter_other_formats')
        if filter(None, [fnmatchcase(mimetype, p) for p in patterns]):
            return False
        else:
            return True

