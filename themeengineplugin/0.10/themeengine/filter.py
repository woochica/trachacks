# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.config import Option, BoolOption
from trac.web.chrome import ITemplateProvider, add_link
from trac.web.api import IRequestFilter, IRequestHandler
from trac.util.html import Markup

import os
from pkg_resources import resource_filename
try:
    set = set
except NameError:
    from sets import Set as set


from api import IThemeProvider

__all__ = ['ThemeFilterModule']

class ThemeFilterModule(Component):
    """A filter to inject style information."""
    
    theme_name = Option('theme', 'theme', default='',
                   doc='The theme to use to style this Trac.')
                   
    override_logo = BoolOption('theme', 'override_logo', default=True,
                               doc='Allow themes to override your header_logo.')
                   
    def theme(self):
        if self.theme_name in self.info:
            return self.info[self.theme_name]
        elif self.theme_name == '':
            return None
        else:
            raise TracError('Unknown theme %s'%self.theme_name)
    theme = property(theme)

    providers = ExtensionPoint(IThemeProvider)
    
    implements(IRequestFilter, IRequestHandler, ITemplateProvider)
    
    def __init__(self):
        # This can safely go in here because the data can only change on a restart anyway
        self.info = {}
        for provider in self.providers:
            for name in provider.get_theme_names():
                theme = provider.get_theme_info(name)
                theme['provider'] = provider
                theme['module'] = provider.__class__.__module__
                
                folders = set()
                for t in ('header', 'footer', 'css'):
                    if t in theme:
                        dir, file = os.path.split(resource_filename(theme['module'], theme[t]))
                        folders.add(dir)
                        theme[t] = file
                self.log.debug('ThemeEngine: folders are %s', ', '.join(folders))
                theme['folders'] = list(folders)
                
                self.info[name] = theme

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        theme = self.theme
        if not theme:
            return template, content_type # No theme, early bail out

        self._alter_loadpaths(req.hdf, theme['folders'])
        #self._alter_loadpaths(req.hdf, resource_filename(__name__, 'templates'))
        if 'header' in theme and theme['header'] != 'header.cs':
            self._alter_loadpaths(req.hdf, resource_filename(__name__, 'templates/header'))
        if 'footer' in theme and theme['footer'] != 'footer.cs':
            self._alter_loadpaths(req.hdf, resource_filename(__name__, 'templates/footer'))
        if 'css' in theme:
            add_link(req, 'stylesheet', req.href.themeengine('theme.css'), mimetype='text/css')
        if 'header_logo' in theme and self.override_logo:
            for k,v in theme['header_logo'].iteritems():
                req.hdf['chrome.logo.'+k] = v

        req.hdf['themeengine'] = theme
                        
        return template, content_type

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/themeengine')
        
    def process_request(self, req):
        path_info = req.path_info[12:]
        
        if path_info == '/theme.css':
            self._alter_loadpaths(req.hdf, self.theme['folders'])
            return self.theme['css'], 'text/css'
        elif path_info.startswith('/screenshot'):
            name = path_info[12:]
            if name in self.info and 'screenshot' in self.info[name]:
                req.send_file(resource_filename(self.info[name]['module'], self.info[name]['screenshot']))
            else:
                req.send_file(resource_filename(__name__, 'htdocs/default.png'))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        #from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        #return []
        
    def get_htdocs_dirs(self):
        yield ('themeengine', resource_filename(__name__, 'htdocs'))
        if self.theme and 'htdocs' in self.theme: 
            yield ('theme', resource_filename(self.theme['module'], self.theme['htdocs']))

    # Internal methods
    def _alter_loadpaths(self, hdf, paths, prepend=True):
        if not isinstance(paths, (tuple, list)):
            paths = [paths]

        old_paths = []        
        node = hdf.getObj('hdf.loadpaths').child()
        while node:
            old_paths.append(node.value())
            node = node.next()
        if prepend:
            paths = paths + old_paths
        hdf.removeTree('hdf.loadpaths')
        hdf['hdf.loadpaths'] = paths
        return old_paths

    def _do_template(self, req, name):
        if name in self.theme:
            dir, file = os.path.split(resource_filename(self.theme['module'], self.theme[name]))
            old_paths = self._alter_loadpaths(req.hdf, dir)
            output = req.hdf.render(file)
            self._alter_loadpaths(req.hdf, old_paths, False)
            self._alter_loadpaths(req.hdf, resource_filename(__name__, 'templates/'+name))
            req.hdf['themeengine.'+name] = Markup(output)

