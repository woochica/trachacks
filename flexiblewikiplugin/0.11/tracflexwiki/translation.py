# -*- coding: utf-8 -*-

from trac.core import *
from trac.util.translation import gettext_noop
from trac.web.api import IRequestFilter

translations = None

def gettext(string, **kwargs):
    global translations
    if translations:
        trans = translations.ugettext(string)
    else:
        trans = string
    return kwargs and trans % kwargs or trans

_ = gettext
    
class TracFlexWikiTranslation(Component):
    """Flexible wiki translation.
    """
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        locale = getattr(req, 'locale', None)
        if locale:
            global translations
            try:
                from babel.support import Translations
                from pkg_resources import resource_filename
            except ImportError:
                return handler
            translations = Translations.load(resource_filename(__name__, 'locale'), locale)
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
