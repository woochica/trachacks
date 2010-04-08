# -*- coding: utf-8 -*-
from trac.core import *
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup

from genshi.core import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer 

from clients import model
from StringIO import StringIO

class JobModule(Component):
    implements(ITemplateProvider)
    

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('jobs', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    
