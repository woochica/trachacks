# Created by Noah Kantrowitz on 2007-04-11.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.util.html import html as tag

class TracForgeClientNavModule(Component):
    """ """

    implements(INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'backtoindex'

    def get_navigation_items(self, req):
        if 'tracforge_master_link' in req.environ and req.perm.has_permission('PROJECT_LIST'):
            yield 'metanav', ' backtoindex', tag.a('Back to Index', href=req.environ['tracforge_master_link'])