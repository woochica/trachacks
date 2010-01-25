import re
from trac.config import ListOption
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util import Markup
from trac.web import IRequestHandler
from trac.web.chrome import add_stylesheet, INavigationContributor, \
                            ITemplateProvider
from trac.web.href import Href

class tractab(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    tab_names_options = ListOption('tractab', 'names', '', doc='List of names that should create tabs (Whitespace Sensitive)')
    tab_url_options = ListOption('tractab', 'urls', '', doc='List of urls that relate to tabs')
    tab_url_options = ListOption('tractab', 'perms', '', doc='List of perm required to view')


    def init_config(self):
        names = self.config.get('tractab', 'names', 'None')
        names = names.split(",");
        print names
        urls = self.config.get('tractab', 'urls', 'None')
        urls = urls.split(",");
        print urls
        urlhash = {}
        for i in range(len(names)):
            urlhash[names[i]]=urls[i]

        print urlhash
        self.last_config_time = self.config._lastmtime
        self.names = names
        self.urls = urls
        self.urlhash = urlhash
    
    def __init__(self):
        self.init_config();

    def join_list(self, list):
        s = ''
        for i in list:
            s += str(i);
        return s


    def check_perms (self, req, idx) :
        perms = self.config.get('tractab', 'perms', 'None')
        perm = None
        
        #if we dont specify permissions, the tabs are only for TRAC_ADMIN
        if perms:
            perms = perms.split(",")
            if len(perms) > idx :
                perm = perms[idx].strip()
                
        if not perm:
            perm = "TRAC_ADMIN"

        
        return req.perm.has_permission(perm)
            
        
    
    def make_trac_tab(self, url, name):
        return '<a href="%s/%s">%s</a>' % ( url, name, name)
         
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        match = re.match('/tractab(?:/([^/]+))?', req.path_info)
        if match:
            return match.group(1)

    def get_navigation_items(self, req):        
        for idx in range(len(self.names)):
            if self.names[idx] is not 'None' and self.check_perms( req, idx ):
                name = self.names[idx]
                yield 'mainnav', name, Markup(self.make_trac_tab(self.env.href.tractab(), name))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match('/tractab(?:/([^/]+))?', req.path_info)
        if match:
            req.args['title'] = match.group(1)
            return True

    def process_request(self, req):
        if(self.last_config_time < self.config._lastmtime):
            self.init_config()
        match = re.match('/tractab(?:/([^/]+))?', req.path_info)
        data = {'url': ""}
        if match:
            name = match.group(1)
            data['title'] = name
            try:
                idx = self.names.index(name)
                if self.check_perms( req, idx ):
                    data['url'] = self.urlhash[name]
            except ValueException:
                idx = None
        return 'tractab.html', {'tractab': data }, 'text/html'
        
    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('tractab', resource_filename(__name__, 'templates'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
