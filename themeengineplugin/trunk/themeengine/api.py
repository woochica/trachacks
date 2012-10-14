# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os.path
import inspect

from trac.core import *
from trac.config import Option

class ThemeNotFound(TracError):
    """The requested theme isn't found."""
    
    def __init__(self, name):
        self.theme_name = name
        super(TracError, self).__init__('Unknown theme %s'%self.theme_name)

class IThemeProvider(Interface):
    """An interface to provide style information."""
    
    def get_theme_names():
        """Return an iterable of names."""
        
    def get_theme_info(name):
        """Return a dict containing 0 or more of the following pairs:
        
         description::
           A breif description of the theme.
         template::
           The name of the theme template file. 
         css::
           The filename of the CSS file.
         disable_trac_css::
           A boolean indicating if the core Trac CSS should be diabled.
         htdocs::
           The folder containg the static content.
         screenshot::
           The name of the screenshot file.
         colors::
           A list of (name, css-property, selector) tuples.
         schemes::
           A list of (name, {color-name: value, ...}) tuples.
        """

class ThemeEngineSystem(Component):
    """Central functionality for the theme system."""
    
    theme_name = Option('theme', 'theme', default='default',
                   doc='The theme to use to style this Trac.')
    
    implements(IThemeProvider)
                   
    def theme(self):
        if self.theme_name.lower() == 'default' or self.theme_name == '':
            return None
        elif self.theme_name.lower() in self.info:
            return self.info[self.theme_name.lower()]
        else:
            raise ThemeNotFound(self.theme_name)
    theme = property(theme)

    providers = ExtensionPoint(IThemeProvider)
    
    def __init__(self):
        # This can safely go in here because the data can only change on a restart anyway
        self.info = {}
        for provider in self.providers:
            for name in provider.get_theme_names():
                theme = provider.get_theme_info(name)
                theme['provider'] = provider
                theme['module'] = provider.__class__.__module__
                theme['name'] = name
                self.info[name.lower()] = theme
                
    # IThemeProvider methods
    def get_theme_names(self):
        yield 'default'
        
    def get_theme_info(self, name):
        return {
            'description': 'The default Trac theme.',
            'screenshot': 'htdocs/default_screenshot.png',
            'colors': [
                ('text', 'color', 'body, .milestone .info h2 *:link, .milestone .info h2 *:visited'),
                ('background', 'background-color', 'body'),
                ('link', 'color', '*:link, *:visited, #tabs *:link, #tabs *:visited, .milestone .info h2 em'),
                ('link_hover', 'color', '*:link:hover, *:visited:hover, #tabs *:link:hover, #tabs *:visited:hover'),
                ('mainnav', 'background-color', '#mainnav'),
                ('mainnav_active', 'background-color', '#mainnav .active *:link, #mainnav .active *:visited'),
                ('mainnav_hover', 'background-color', '#mainnav *:link:hover, #mainnav *:visited:hover'),
            ],
            'schemes': [
                ('default', {
                    'text': '#000000',
                    'background': '#ffffff',
                    'link': '#bb0000',
                    'link_hover': '#555555',
                    'mainnav': '#ffffff',
                    'mainnav_active': '#000000',
                    'mainnav_hover': '#cccccc',
                }),
                ('omgponies', {
                    'text': '#A42D8D',
                    'background': '#FECDE3',
                    'link': '#E600BC',
                    'link_hover': '#8C366C',
                    'mainnav': '#FB88C3',
                    'mainnav_active': '#EB009B',
                    'mainnav_hover': '#c15c9f',
                }),
            ],
        }

class ThemeBase(Component):
    """A base class for themes."""
    
    abstract = True
    
    implements(IThemeProvider)
    
    # Defaults
    theme = css = htdocs = screenshot = False
    colors = schemes = disable_trac_css = False

    # IThemeProviderMethods
    def get_theme_names(self):
        name = self.__class__.__name__
        if name.endswith('Theme'):
            name = name[:-5]
        yield name
        
    def get_theme_info(self, name):
        info = {}
        
        info['description'] = inspect.getdoc(self.__class__)
        self._set_info(info, 'template', os.path.join('templates', self.get_theme_names().next().lower()+'_theme.html'))
        self._set_info(info, 'css', self.get_theme_names().next().lower()+'.css')
        self._set_info(info, 'htdocs', 'htdocs')
        self._set_info(info, 'screenshot', 'htdocs/screenshot.png')
        self._set_info(info, 'colors', ())
        self._set_info(info, 'schemes', ())
        self._set_info(info, 'disable_trac_css', True)
        
        return info
            
    # Internal methods
    def _set_info(self, info, attr, default):
        if not hasattr(self, attr):
            return # This should never happen, but better to be safe
        
        val = getattr(self, attr)
        if val:
            if val is True:
                info[attr] = default
            elif val is not False:
                info[attr] = val
           

