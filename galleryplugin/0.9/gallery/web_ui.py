# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2005 Bruce Christensen <trac@brucec.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Bruce Christensen <trac@brucec.net>

import re
import os

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.util import escape

from api import *

class GalleryModule(Component):
    implements(INavigationContributor, IRequestHandler, IPermissionRequestor,
               ITemplateProvider)

    def __init__(self):
        self._gallery = self.env[Gallery]
        self.env.log.debug("Gallery: '%s'" % self._gallery)

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'^/gallery(?:/(tag|image)(?:/(.*))?)?$', req.path_info)
        if match:
            req.args['type'] = match.group(1)
            req.args['path'] = match.group(2)
            return 1

    def process_request(self, req):
        maxwidth = self.config.get('gallery', 'thumb_width', 128)
        maxheight = self.config.get('gallery', 'thumb_height', 128)

        for source in self._gallery._sources:
            req.write(source.gallery_source_name() + "\n")
            req.write(str(source.get_tags()) + "\n")
            self.env.log.debug("Gallery now: '%s'" % self._gallery)
            for img in source.get_images(self._gallery):
                req.write(img.__class__)
                req.write(str(img) + "\n")
                img.thumb.generate(maxwidth, maxheight)
                req.write(str(img.thumb) + "\n")
        return

        parent_type = req.args.get('type')
        path = req.args.get('path')
        if not parent_type or not path:
            raise TracError('Bad request')
        if not parent_type in ['ticket', 'wiki']:
            raise TracError('Unknown attachment type')

        action = req.args.get('action', 'view')
        if action == 'new':
            attachment = Attachment(self.env, parent_type, path)
        else:
            segments = path.split('/')
            parent_id = '/'.join(segments[:-1])
            filename = segments[-1]
            if len(segments) == 1 or not filename:
                raise TracError('Bad request')            
            attachment = Attachment(self.env, parent_type, parent_id, filename)

        if req.method == 'POST':
            if action == 'new':
                self._do_save(req, attachment)
            elif action == 'delete':
                self._do_delete(req, attachment)
        elif action == 'delete':
            self._render_confirm(req, attachment)
        elif action == 'new':
            self._render_form(req, attachment)
        else:
            self._render_view(req, attachment)

        add_stylesheet(req, 'common/css/code.css')
        return 'test.cs', None

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'gallery'
                
    def get_navigation_items(self, req):
        # if not req.perm.has_permission('GALLERY_VIEW'):
        #     return
        yield 'mainnav', 'gallery', '<a href="%s" accesskey="g">Gallery</a>' \
            % escape(self.env.href.gallery())

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('gallery', resource_filename(__name__, 'htdocs'))]

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'GALLERY_VIEW'
