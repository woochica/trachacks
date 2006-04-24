from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome

import os
import os.path
from pkg_resources import resource_filename
from tracistan import IStanRequestHandler, IStanRenderer
from nevow import tags as T

__all__ = ['StatusPage']

class StatusPage(Component):
    """
        Provides functions related to registration
    """

    implements(IStanRequestHandler, ITemplateProvider)

    def match_request(self, req):
        return req.path_info == '/aftracistan'

    def process_request(self, req):
        add_stylesheet(req, 'aftracistan/css/aftracistan.css')
        req.standata.update({ 'name': 'Pacopablo',
                 'message' : 'Hello vatos!',
                 'title' : 'Aftracistan',
                 'tidy'  : True,
                 'nav' : [{ 'link_name' : 'Front page',
                            'link_id'   : 'current',
                            'link_url'  : 'index.html', },
                          { 'link_name' : 'Alternative layout',
                            'link_id'   : None,
                            'link_url'  : 'alternative.html', },
                          { 'link_name' : 'Photo layout',
                            'link_id'   : None,
                            'link_url'  : 'photos.html', },
                          { 'link_name' : 'Styles',
                            'link_id'   : None,
                            'link_url'  : 'styles.html', },
                          { 'link_name' : 'Empty',
                            'link_id'   : None,
                            'link_url'  : 'empty.html', },
                         ]
               })
        return ('index.stan', None)

    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('aftracistan', resource_filename(__name__, 'htdocs'))]


class StatusRenderers(Component):
    implements(IStanRenderer)

    def get_renderers(self):
        """Map methods to method names"""
        return {
                'render_nav_row' : self._render_nav_row,
               }

    def _render_nav_row(self, context, data):
        return context.tag(id=data['link_id'])[T.a (href=data['link_url']) [ data['link_name'] ]]
