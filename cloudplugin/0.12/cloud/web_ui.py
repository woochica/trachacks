import csv
import re
from StringIO import StringIO

from genshi.builder import tag

from trac.config import Option, IntOption, ChoiceOption, ListOption
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.resource import Resource, ResourceNotFound
from trac.util.datefmt import format_datetime, format_time, from_utimestamp
from trac.util.translation import _
from trac.web.api import IRequestHandler, RequestDone
from trac.web.chrome import Chrome, add_ctxtnav, add_link, add_notice, \
                            add_script, add_stylesheet, add_warning, \
                            INavigationContributor, ITemplateProvider
from handlers import IFieldHandler
from droplets import Droplet
from chefapi import ChefApi
from awsapi import AwsApi


class CloudModule(Component):
    """Orchestrates AWS cloud resources via Chef.  Leans heavily on boto
    and PyChef and borrowed much from the built-in report component."""

    implements(ITemplateProvider, INavigationContributor, IPermissionRequestor,
               IRequestHandler)
    
    # trac.ini options
    label = Option('cloud', 'label', _('Cloud'), _("Top nav label."))
    
    aws_key = Option('cloud', 'aws_key', '', _("AWS/S3 access key."))
    
    aws_secret = Option('cloud', 'aws_secret', '', _("AWS/S3 secret."))
    
    aws_keypair = Option('cloud', 'aws_keypair', '', _("AWS/EC2 keypair name."))
    
    chef_instancedata_file = Option('cloud', 'chef_instancedata_file', '',
        _("File containing instance data for new ec2 instances."))
    
    chef_base_path = Option('cloud', 'chef_base_path', '',
        _("Directory where .chef configs can be found (mostly used for dev)."))
    
    boto_field_node_name = Option('cloud', 'boto_field_node_name', '',
        _("The boto field whose value is expected as the chef node name."))
    
    default_droplet = Option('cloud', 'default_droplet', '',
        _("Name of droplet to show if not provided in url."))
    
    items_per_page = IntOption('cloud', 'items_per_page', 100,
        _("Number of items displayed per page in cloud reports by default"))
    
    items_per_page_rss = IntOption('cloud', 'items_per_page_rss', 0,
        _("Number of items displayed in the rss feeds for cloud reports"))
    
    # NOTE: Each droplet's [cloud.*] config is retrieved during its init.
    
    
    field_handlers = ExtensionPoint(IFieldHandler)
    
        
    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('cloud', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'cloud'

    def get_navigation_items(self, req):
        if 'CLOUD_VIEW' in req.perm:
            yield ('mainnav', 'cloud', tag.a(self.label, href=req.href.cloud()))
    
    
    # IPermissionRequestor methods  
    
    def get_permission_actions(self):  
        actions = ['CLOUD_CREATE','CLOUD_DELETE','CLOUD_MODIFY','CLOUD_VIEW']  
        return actions + [('CLOUD_ADMIN',actions)]  
    
    
    # IRequestHandler methods
    
    def match_request(self, req):
        match = re.match(r'/cloud(?:/([^/]+)(?:/([\w.\-]+))?)?$', req.path_info)
        if match:
            if match.group(1):
                req.args['droplet_name'] = match.group(1)
            if match.group(2):
                req.args['id'] = match.group(2)
            return True

    def process_request(self, req):
        req.perm.require('CLOUD_VIEW')
        
        # setup cloud droplets
        if not hasattr(self, 'droplets'):
            # setup chefapi and cloudapi
            chefapi = ChefApi(self.chef_instancedata_file,
                              self.chef_base_path,
                              self.log)
            
            cloudapi = AwsApi(self.aws_key,
                              self.aws_secret,
                              self.aws_keypair,
                              self.log)
            
            # instantiate each droplet (singletons)
            self.droplets = {}
            self.titles = self._get_droplet_titles()
            for order,droplet_name,title in self.titles:
                self.droplets[droplet_name] = Droplet.new(self.env,
                    droplet_name, chefapi, cloudapi,
                    self.field_handlers,
                    self.boto_field_node_name, self.log)
        
        droplet_name = req.args.get('droplet_name', '')
        id = req.args.get('id', '')
        action = req.args.get('action', 'view')
        
        if droplet_name == '':
            req.redirect(req.href.cloud(self.default_droplet))
        
        # check for valid kind
        if droplet_name not in self.droplets:
            raise ResourceNotFound(
                _("Cloud resource '%(droplet_name)s' does not exist.",
                  droplet_name=droplet_name),
                _('Invalid Cloud Resource'))
            
        # retrieve the droplet
        droplet = self.droplets[droplet_name]
        
        # route the request
        if req.method == 'POST':
            if 'cancel' in req.args:
                req.redirect(req.href.cloud(droplet_name,id))
            elif action == 'new':
                droplet.create(req)
            elif action == 'delete':
                droplet.delete(req, id)
            elif action == 'edit':
                droplet.save(req, id)
        else: # req.method == 'GET':
            if action in ('edit', 'new'):
                template, data, content_type = droplet.render_edit(req, id)
                Chrome(self.env).add_wiki_toolbars(req)
            elif action == 'delete':
                template, data, content_type = droplet.render_delete(req, id)
            elif id == '':
                template, data, content_type = droplet.render_grid(req)
                if content_type: # i.e. alternate format
                    return template, data, content_type
            else:
                template, data, content_type = droplet.render_view(req, id)
                if content_type: # i.e. alternate format
                    return template, data, content_type
        
        # add contextual nav
        for order,droplet_name,title in self.titles:
            add_ctxtnav(req, title, href=req.href.cloud(droplet_name))
        
        add_stylesheet(req, 'common/css/report.css') # reuse css
        return template, data, None
    
    
    # Internal methods
    
    def _get_droplet_titles(self):
        """Return an ordered list of tuples of the droplet's name and title.
        The order is based on an 'order' config option (if provided)."""
        titles = []
        for section in self.env.config.sections():
            if not section.startswith('cloud.'):
                continue
            droplet_name = section.replace('cloud.','',1)
            order = int(self.env.config.get(section,'order',99))
            title = self.env.config.get(section,'title',droplet_name)
            titles.append( (order,droplet_name,title) )
        return sorted(titles)
