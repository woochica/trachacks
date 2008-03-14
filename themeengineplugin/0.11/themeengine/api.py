# Created by Noah Kantrowitz on 2007-07-16.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import os.path
import inspect

from trac.core import *
from trac.config import Option

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
         htdocs::
           The folder containg the static content.
         screenshot::
           The name of the screenshot file.
        """

class ThemeEngineSystem(Component):
    """Central functionality for the theme system."""
    
    theme_name = Option('theme', 'theme', default='default',
                   doc='The theme to use to style this Trac.')
    
    implements(IThemeProvider)
                   
    def theme(self):
        if self.theme_name == 'default' or self.theme_name == '':
            return None
        elif self.theme_name in self.info:
            return self.info[self.theme_name]
        else:
            raise TracError('Unknown theme %s'%self.theme_name)
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
                self.info[name] = theme
                
    # IThemeProvider methods
    def get_theme_names(self):
        yield 'default'
        
    def get_theme_info(self, name):
        return {
            'description': 'The default Trac theme.',
            'screenshot': 'htdocs/default_screenshot.png'
        }

class ThemeBase(Component):
    """A base class for themes."""
    
    abstract = True
    
    implements(IThemeProvider)
    
    # Defaults
    theme = css = htdocs = screenshot = False

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
           

