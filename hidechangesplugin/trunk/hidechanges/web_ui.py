from trac.core import *
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.config import Option

class HideChangesModule(Component):
    """Hides/shows ticket changes using JS based on configurable rules."""
    
    show_button_name = Option('hidechanges', 'show_button_name',
            default='Show changes', doc="Name of button to show changes.")
    hide_button_name = Option('hidechanges', 'hide_button_name',
            default='Hide changes', doc="Name of button to hide changes.")
    
    implements(IRequestFilter, IRequestHandler, ITemplateProvider)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket') \
          and req.perm.has_permission('TICKET_VIEW'):
            add_script(req, '/hidechanges/hidechanges.js')
        return template, data, content_type
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/hidechanges')

    def process_request(self, req):
        data = {'rules': self._get_rules(),
                'show_button_name': self.show_button_name,
                'hide_button_name': self.hide_button_name}
        return 'hidechanges.html', {'data':data},'text/javascript' 
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # private methods
    def _get_rules(self):
        """Return a list of JS rules from config specified in this format:
        
          [hidechanges]
          rule.commentless = !changediv.find('div.comment').children().length
          
        This example hides any change whose comment node is empty.  You
        can have as many rules as you want in the form "rule.<name>"
        using jQuery or straight JS.  The <name> portion must be unique
        (but is otherwise unused).  "changediv" contains the "div.change"
        node.  Make your rule return True or False.  If True, the change
        div will be hidden."""
        rules = []
        for key,val in self.env.config.options('hidechanges'):
            if key.startswith('rule.'):
                rules.append(val)
        return rules
