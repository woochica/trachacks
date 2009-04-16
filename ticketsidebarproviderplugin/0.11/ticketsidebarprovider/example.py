"""
example of a TicketSidebarProvider
"""

from genshi.builder import tag
from interface import ITicketSidebarProvider
from trac.core import *

class SampleTicketSidebarProvider(Component):
    implements(ITicketSidebarProvider)

    def enabled(self, req, ticket):
        return True

    def content(self, req, ticket):
        return tag.b('hello world')
