# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *

import inspect

class IThemeProvider(Interface):
    """An interface to provide style information."""
    
    def get_theme_names(self):
        """Return an iterable of names."""
        pass
        
    def get_theme_info(self, name):
        """Return a dict containing 0 or more of the following pairs:
         description::
           A breif description of the theme.
         header::
           The filename of the replacement header file.
         footer::
           The filename of the replacement footer file.
         css::
           The filename of the CSS template file.
         htdocs::
           The folder containg the static content.
         screenshot::
           The name of the screenshot file.
         header_logo::
           A dict containing the same data as the [header_logo] section.
        """
        pass

class ThemeBase(Component):
    """A base class for themes."""
    
    abstract = True
    
    implements(IThemeProvider)
    
    # Defaults
    header = footer = css = htdocs = screenshot = header_logo = False

    # IThemeProviderMethods
    def get_theme_names(self):
        name = self.__class__.__name__
        if name.endswith('Theme'):
            name = name[:-5]
        yield name
        
    def get_theme_info(self, name):
        info = {}
        
        info['description'] = inspect.getdoc(self.__class__)
        self._set_info(info, 'header', 'templates/header.cs')
        self._set_info(info, 'footer', 'templates/footer.cs')
        self._set_info(info, 'css', 'templates/css.cs')
        self._set_info(info, 'htdocs', 'htdocs')
        self._set_info(info, 'screenshot', 'htdocs/screenshot.png')
        self._set_info(info, 'header_logo', {})
        
        return info
            
    # Internal methods
    def _set_info(self, info, attr, default):
        if not hasattr(self, attr):
            return # This should never happen, but better to be safe
        
        val = getattr(self, attr)
        if val:
            if val is True:
                info[attr] = default
            else:
                info[attr] = val
           

