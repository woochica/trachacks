# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2006 Ricardo Salveti <rsalveti@gmail.com>
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
# This plugin is based on the WebAdmin plugin, made by Jonas Borgström <jonas@edgewall.com>
#
# Author: Ricardo Salveti <rsalveti@gmail.com>

import re

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util import Markup
from trac.web import IRequestHandler
from trac.web.chrome import add_stylesheet, INavigationContributor, \
                            ITemplateProvider
from trac.web.href import Href

__all__ = ['IProjManagerPageProvider']


class IProjManagerPageProvider(Interface):
    """
    Extendion point interface for adding pages to the projmanager module.
    """

    def get_projmanager_pages(self, req):
        """
        Return a list of available projmanager pages. The pages returned by
        this function must be a tuple of the form
        (category, category_label, page, page_label).
        """

    def process_projmanager_request(self, req, category, page, path_info):
        """
        Process the request for the projmanager `page`. This function should
        return a tuple of the form (template_name, content_type) where
        a content_type of `None` is assumed to be "text/html".
        """


class ProjManagerModule(Component):
    """The module itself, were get and return all the necessary data"""

    implements(IPermissionRequestor, INavigationContributor, IRequestHandler, ITemplateProvider)
    page_providers = ExtensionPoint(IProjManagerPageProvider)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['PROJECT_MANAGER']


    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        if req.perm.has_permission('PROJECT_MANAGER'):
            return 'projmanager'

    def get_navigation_items(self, req):
        """The 'Proj Manager' navigation item is only visible if at least one
           projmanager page is available and if the user has the permission."""
        pages, providers = self._get_pages(req)
        if req.perm.has_permission('PROJECT_MANAGER') and pages:
            yield 'mainnav', 'projmanager', Markup('<a href="%s">Proj Management</a>',
                                             self.env.href.projmanager())

    # Defined method

    def _get_pages(self, req):
        """Return a list of available projmanager pages."""
        pages = []
        providers = {}
        for provider in self.page_providers:
            p = list(provider.get_projmanager_pages(req))
            for page in p:
                providers[(page[0], page[2])] = provider
            pages += p
        pages.sort()
        return pages, providers

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match('/projmanager(?:/([^/]+))?(?:/([^/]+))?(?:/(.*)$)?', req.path_info)
        if match:
            req.args['cat_id'] = match.group(1)
            req.args['page_id'] = match.group(2)
            req.args['path_info'] = match.group(3)
            return True

    def process_request(self, req):
        if not req.perm.has_permission('PROJECT_MANAGER'):
            raise TracError('Need PROJECT_MANAGER permission')
        pages, providers = self._get_pages(req)
        if not pages:
            raise TracError('No projmanager pages available')
        cat_id = req.args.get('cat_id') or pages[0][0]
        page_id = req.args.get('page_id')
        path_info = req.args.get('path_info')
        if not page_id:
            page_id = filter(lambda page: page[0] == cat_id, pages)[0][2]
        
        provider = providers.get((cat_id, page_id), None)
        if not provider:
            raise TracError('Unknown Proj Manager Page')
        
        # Do the action
        template, content_type = provider.process_projmanager_request(req, cat_id,
                                                                page_id,
                                                                path_info)
        # Get the list of pages
        req.hdf['projmanager.pages'] = [{'cat_id': page[0],
                                   'cat_label': page[1],
                                   'page_id': page[2],
                                   'page_label': page[3],
                                   'href': self.env.href.projmanager(page[0], page[2])
                                   } for page in pages]
        req.hdf['projmanager.active_cat'] = cat_id
        req.hdf['projmanager.active_page'] = page_id
        req.hdf['projmanager.page_template'] = template
        add_stylesheet(req, 'projmanager/css/projmanager.css')
        return 'projmanager.cs', content_type

    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('projmanager', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
