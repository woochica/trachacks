"""
ContactInfo: 
contact information for a Trac project
a view for Trac
http://trac.edgewall.org
"""

from genshi.builder import tag
from pkg_resources import resource_filename

from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import add_notice
from trac.web.chrome import add_warning
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import INavigationContributor

class ContactInfo(Component):

    implements(ITemplateProvider, IRequestHandler, INavigationContributor)

    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [ ]

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [resource_filename(__name__, 'templates')]

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info.strip('/') == 'contact'

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """

        # process POST request
        if req.method == 'POST':
            req.perm.require('TRAC_ADMIN')
            
            # set manager
            if 'manager' in req.args:
                if '@' in req.args['manager']:
                    # set via email address
                    self.env.config.set('project', 'admin', req.args['manager'])
                    self.env.config.save()
                    add_notice(req, "%s is now manager of this project" % req.args['manager'])
                else:
                    # set via user name
                    users = [i for i in self.env.get_known_users()
                             if i[0] == req.args['manager']]
                    if not users:
                        add_warning(req, "%s not a known user")
                    elif not users[0][2]:
                        add_warning(req, "%s has not set their email address")
                    else:
                        self.env.config.set('project', 'admin', users[0][2])
                        self.env.config.save()
                        
                        add_notice(req, "%s is now manager of this project" % req.args['manager'])


        # data for genshi template
        data = {}

        # manager
        admin_email = self.env.config.get('project', 'admin')
        if admin_email:
            data['manager'] = { 'email': admin_email }
            admin = [ i for i in self.env.get_known_users()
                      if i[2] == admin_email ]
            if admin:
                # take first matching user
                data['manager']['username'] = admin[0][0]
                if admin[0][1]:
                    data['manager']['name'] = admin[0][1]
        else:
            data['manager'] = None

        # email
        data['email'] = self.env.get.('mail', 'address') or self.env.config.get('notification', 'smtp_replyto')


        return ("contactinfo.html", data, 'text/html')

    ### methods for INavigationContributor

    """Extension point interface for components that contribute items to the
    navigation.
    """

    def get_active_navigation_item(self, req):
        """This method is only called for the `IRequestHandler` processing the
        request.
        
        It should return the name of the navigation item that should be
        highlighted as active/current.
        """
        return 'contactinfo'

    def get_navigation_items(self, req):
        """Should return an iterable object over the list of navigation items to
        add, each being a tuple in the form (category, name, text).
        """
        yield ('metanav', 'contactinfo', tag.a('Contact', href=req.href('contact')))
        

