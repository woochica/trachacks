# ManualTesting.MTP_NavigationContributor

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.util import escape, Markup

class MTP_NavigationContributor(Component):
    implements(INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'testing'

    def get_navigation_items(self, req):
        markupString = '<a href="%s">Testing</a>' % self.env.href.testing()
        yield 'mainnav', 'testing', Markup(markupString)