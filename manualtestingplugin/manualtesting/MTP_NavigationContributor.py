# ManualTesting.MTP_NavigationContributor

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.util import escape, Markup

"""
Extension point interface for components that contribute items to the navigation."""
class MTP_NavigationContributor(Component):
    implements(INavigationContributor)

    """
    This method is only called for the `IRequestHandler` processing the request.
    It should return the name of the navigation item that should be
    highlighted as active/current.
    """
    def get_active_navigation_item(self, req):
        return 'testing'

    """
    Should return an iterable object over the list of navigation items to add,
    each being a tuple in the form (category, name, text).
    """
    def get_navigation_items(self, req):
        markupString = '<a href="%s">Testing</a>' % self.env.href.testing()
        yield 'mainnav', 'testing', Markup(markupString)