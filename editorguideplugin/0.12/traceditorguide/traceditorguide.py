from trac.core import implements, Component
from trac.util.html import html
from trac.web.chrome import INavigationContributor
from translation import _


class EditorGuideItem(Component):
    """
    Adds special navigation item to metanav: link to editor's guide wiki page.
    This item visible only for users who has 'WIKI_MODIFY' permission.
    
    Name of wiki page can be changed in trac.ini:
    
    [editorguide]
    page = MyEditorGuide
    """
    
    implements(INavigationContributor)
    
    # INavigationContributor methods
    
    def get_active_navigation_item(self, req):
        return 'editorguide'
    
    def get_navigation_items(self, req):
        if 'WIKI_MODIFY' in req.perm('wiki'):
            page = self.env.config.get('editorguide', 'page', 'EditorGuide')
            yield ('metanav', 'editorguide',
                html.a(_('Editor\'s Guide'), href=req.href.wiki(page)))

