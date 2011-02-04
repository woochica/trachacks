import copy
import time
from trac.resource import Resource
from trac.util import as_int
from trac.util.presentation import Paginator
from trac.util.text import to_unicode
from trac.web.chrome import Chrome, add_link, add_notice, add_warning
from trac.mimeview import Context
from trac.util.translation import _
from fields import Fields
from defaults import droplet_defaults

class Droplet(object):
    """Generic class for a cloud resource that I'm calling a 'droplet'
    to distinguish it from Trac resources.  Droplets are controllers
    that coordinate trac, chef, and cloud behaviors."""
    
    @classmethod
    def new(cls, env, name, chefapi, cloudapi, field_handlers, log):
        """Return a new droplet instance based on the class name defined
        in the droplet's trac.ini config section - e.g.,
        
          [cloud.instance]
          class = Ec2Instance
        
        where the name param = 'instance'.  Default options for the
        droplet are overridden by those in the trac.ini file.
        """
        section = 'cloud.%s' % name
        options = copy.copy(droplet_defaults.get(name,{})) # defaults
        options.update(dict(env.config.options('cloud')))  # overrides
        options.update(env.config.options(section))        # overrides
        cls = globals()[options['class']]
        return cls(name, chefapi, cloudapi, field_handlers, log, options)
    
    def __init__(self, name, chefapi, cloudapi, field_handlers, log, options):
        """Parses the droplet's config file section in trac.ini.  Here's
        an example trac.ini droplet section:
        
          [cloud.instance]
          class = Ec2Instance
          title = EC2 Instances
          order = 1
          label = Instance
        
        The 'instance' in '[cloud.instance]' is the droplet name which is
        used to uniquely identify the class of cloud resources including in
        the trac url structure (e.g., /cloud/instance).
        
        The 'class' value must exactly match the python class name for the
        corresponding droplet.
        
        The 'title' and 'order' options are used for contextual navigation.
        The 'order' should start with 1.  If 'order' is omitted then the
        droplet will not be returned as a contextual navigation element
        (but would still be accessible by its url). The 'label' value is
        displayed in various buttons and forms for the name of a single
        droplet item.
        
        The remaining fields (not shown above) are for querying chef and
        are parsed by the Fields class.
        """
        self.name = name
        self.chefapi = chefapi
        self.cloudapi = cloudapi
        self.log = log
        
        prefix = 'field.'
        self.fields = Fields(options, field_handlers, chefapi, log, prefix)
        
        for k,v in options.items():
            if k.startswith(prefix):
                continue # handled by Fields class above
            if k in ('crud_view','crud_new','crud_edit','grid_columns'):
                self.fields.set_list(k,v)
                continue
            setattr(self, k, v)
    
    def render_grid(self, req):
        """Retrieve the droplets and pre-process them for rendering."""
        index = self.grid_index
        columns = self.fields.get_list('grid_columns')
        id_col = columns[0].name
        
        format = req.args.get('format')
        resource = Resource('cloud', self.name)
        context = Context.from_request(req, resource)

        page = int(req.args.get('page', '1'))
        default_max = {'rss': self.items_per_page_rss,
                       'csv': 0,
                       'tab': 0}.get(format, self.items_per_page)
        max = req.args.get('max')
        limit = as_int(max, default_max, min=0) # explicit max takes precedence
        offset = (page - 1) * limit
        
        # explicit sort takes precedence over config
        sort = req.args.get('sort', self.grid_sort)
        asc = req.args.get('asc', self.grid_asc)
        asc = bool(int(asc)) # string '0' or '1' to int/boolean
        
        def droplet_href(**kwargs):
            """Generate links to this cloud droplet preserving user
            variables, and sorting and paging variables.
            """
            params = {}
            if sort:
                params['sort'] = sort
            params['page'] = page
            if max:
                params['max'] = max
            params.update(kwargs)
            params['asc'] = params.get('asc', asc) and '1' or '0'            
            return req.href.cloud(self.name, params)
        
        data = {'action': 'view',
                'resource': resource,
                'context': context,
                'title': self.title,
                'description': self.description,
                'label': self.label,
                'columns': columns,
                'max': limit,
                'message': None,
                'paginator': None,
                'droplet_href': droplet_href,
                }
        
        try:
            sort_ = sort.strip('_') # handle dynamic attributes
            rows,total = self.chefapi.search(index, sort_, asc, limit, offset)
            numrows = len(rows)
        except Exception:
            import traceback;
            msg = "Oops...\n" + traceback.format_exc()+"\n"
            data['message'] = _(to_unicode(msg))
            return 'droplet_grid.html', data, None
        
        paginator = None
        if limit > 0:
            paginator = Paginator(rows, page - 1, limit, total)
            data['paginator'] = paginator
            if paginator.has_next_page:
                add_link(req, 'next', droplet_href(page=page + 1),
                         _('Next Page'))
            if paginator.has_previous_page:
                add_link(req, 'prev', droplet_href(page=page - 1),
                         _('Previous Page'))
            
            pagedata = []
            shown_pages = paginator.get_shown_pages(21)
            for p in shown_pages:
                pagedata.append([droplet_href(page=p), None, str(p),
                                 _('Page %(num)d', num=p)])
            fields = ['href', 'class', 'string', 'title']
            paginator.shown_pages = [dict(zip(fields, p)) for p in pagedata]
            paginator.current_page = {'href': None, 'class': 'current',
                                    'string': str(paginator.page + 1),
                                    'title': None}
            numrows = paginator.num_items
        
        # Place retrieved columns in groups, according to naming conventions
        #  * _col_ means fullrow, i.e. a group with one header
        #  * col_ means finish the current group and start a new one
        
        header_groups = [[]]
        for idx, field in enumerate(columns):
            header = {
                'col': field.name,
                'title': field.label,
                'hidden': False,
                'asc': None,
            }

            if field.name == sort:
                header['asc'] = asc

            header_group = header_groups[-1]
            header_group.append(header)
        
        # Structure the rows and cells:
        #  - group rows according to __group__ value, if defined
        #  - group cells the same way headers are grouped
        row_groups = []
        authorized_results = [] 
        prev_group_value = None
        for row_idx, item in enumerate(rows):
            col_idx = 0
            cell_groups = []
            row = {'cell_groups': cell_groups}
            for header_group in header_groups:
                cell_group = []
                for header in header_group:
                    col = header['col']
                    field = self.fields[col]
                    value = field.get(item, req)
                    cell = {'value': value, 'header': header, 'index': col_idx}
                    col_idx += 1
                    # Detect and create new group
                    if col == '__group__' and value != prev_group_value:
                        prev_group_value = value
                    # Other row properties
                    row['__idx__'] = row_idx
                    if col == id_col:
                        row['id'] = value
                    cell_group.append(cell)
                cell_groups.append(cell_group)
            resource = Resource('cloud', '%s/%s' %(self.name,row['id']))
            # FIXME: for now, we still need to hardcode the realm in the action
            if 'CLOUD_VIEW' not in req.perm(resource):
                continue
            authorized_results.append(item)
            row['resource'] = resource
            if row_groups:
                row_group = row_groups[-1][1]
            else:
                row_group = []
                row_groups = [(None, row_group)]
            row_group.append(row)
        
        data.update({'header_groups': header_groups,
                     'row_groups': row_groups,
                     'numrows': numrows,
                     'sorting_enabled': len(row_groups) == 1})
        
        if format == 'rss':
            data['email_map'] = Chrome(self.env).get_email_map()
            data['context'] = Context.from_request(req, report_resource,
                                                   absurls=True)
            return 'report.rss', data, 'application/rss+xml'
        elif format == 'csv':
            filename = id and 'report_%s.csv' % id or 'report.csv'
            self._send_csv(req, cols, authorized_results, mimetype='text/csv',
                           filename=filename)
        elif format == 'tab':
            filename = id and 'report_%s.tsv' % id or 'report.tsv'
            self._send_csv(req, cols, authorized_results, '\t',
                           mimetype='text/tab-separated-values',
                           filename=filename)
        else:
            p = max is not None and page or None
            add_link(req, 'alternate', droplet_href(format='rss', page=None),
                     _('RSS Feed'), 'application/rss+xml', 'rss')
            add_link(req, 'alternate', droplet_href(format='csv', page=p),
                     _('Comma-delimited Text'), 'text/plain')
            add_link(req, 'alternate', droplet_href(format='tab', page=p),
                     _('Tab-delimited Text'), 'text/plain')

            return 'droplet_grid.html', data, None
    
    def render_view(self, req, id):
        req.perm.require('CLOUD_VIEW')
        item = self.chefapi.resource(self.crud_resource, id)
        
        data = {
            'title': _('%(label)s %(id)s', label=self.label, id=id),
            'action': 'view',
            'droplet_name': self.name,
            'id': id,
            'label': self.label,
            'fields': self.fields.get_list('crud_view'),
            'item': item,
            'req': req,
            'error': req.args.get('error')}
        
        return 'droplet_view.html', data, None
    
    def render_edit(self, req, id):
        if id:
            item = self.chefapi.resource(self.crud_resource, id)
        else:
            item = None

        data = {
            'droplet_name': self.name,
            'id': id,
            'label': self.label,
            'item': item,
            'req': req,
            'error': req.args.get('error')}
        
        # check if creating or editing
        if id:
            req.perm.require('CLOUD_MODIFY')
            data.update({
                'title': _('Edit  %(label)s %(id)s', label=self.label, id=id),
                'button': _('Save %(label)s', label=self.label),
                'action': 'edit',
                'fields': self.fields.get_list('crud_edit')})
        else:
            req.perm.require('CLOUD_CREATE')
            data.update({
                'title': _('Create New %(label)s', label=self.label),
                'button': _('Create %(label)s', label=self.label),
                'action': 'new',
                'fields': self.fields.get_list('crud_new')})
        
        return 'droplet_edit.html', data, None
    
    def render_delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        data = {
            'title': _('Delete  %(label)s %(id)s', label=self.label, id=id),
            'button': _('Delete %(label)s', label=self.label),
            'droplet_name': self.name,
            'id': id,
            'label': self.label}
        return 'droplet_delete.html', data, None
    
    def create(self, req):
        pass
    
    def save(self, req):
        pass
    
    def delete(self, req, id):
        pass
    

class Ec2Instance(Droplet):
    """An EC2 instance cloud droplet."""
    
    def create(self, req):
        req.perm.require('CLOUD_CREATE')
        
        # launch instance (and wait until running)
        now = time.time()
        placement = req.args.get('ec2.placement_availability_zone','')
        if placement in ('No preference',''):
            placement = None
        instance = self.cloudapi.launch_instance(
            image_id = req.args.get('ec2.ami_id'),
            instance_type = req.args.get('ec2.instance_type'),
            placement = placement, timeout = 300)
        if instance.state != 'running':
            add_warning(req,
                _("%(label)s %(id)s was created but isn't running (yet). " + \
                  "Please check in the AWS Management Console directly.",
                  label=self.label, id=instance.id))
            req.redirect(req.href.cloud(self.name))
        
        # bootstrap the new instance
        id = instance.private_dns_name
        public_hostname = instance.public_dns_name
        node = self.chefapi.bootstrap(id, public_hostname, timeout=300)
        if node is None:
            add_warning(req,
                _("%(label)s %(id)s is running but not bootstrapped (yet). " + \
                  "Please login to %(hostname)s to investigate.",
                  label=self.label, id=instance.id,
                  hostname=instance.public_dns_name))
            req.redirect(req.href.cloud(self.name))
        
        # save the new fields (filter out run_list and automatic)
        fields = self.fields.get_list('crud_new', filter=r"ec2\..*")
        self.save(req, id, fields, redirect=False)
        
        # show the view
        add_notice(req, _('%(label)s %(id)s has been created.',
                          label=self.label, id=instance.id))
        req.redirect(req.href.cloud(self.name, id))
    
    def save(self, req, id, fields=None, redirect=True):
        req.perm.require('CLOUD_MODIFY')
        node = self.chefapi.resource(self.crud_resource, id)
        
        # prepare fields; remove automatic (ec2) fields
        if fields is None:
            fields = self.fields.get_list('crud_edit', filter=r"ec2\..*")
        for field in fields:
            field.set(node, req)
        node.save()
        
        if redirect:
            # show the view
            add_notice(req, _('%(label)s %(id)s has been saved.',
                              label=self.label, id=id))
            req.redirect(req.href.cloud(self.name, id))
        
    def delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        node = self.chefapi.resource(self.crud_resource, id)
        
        # delete the ec2 instance
        instance_id = 'undefined'
        try:
            instance_id = node.attributes.get_dotted('ec2.instance_id')
            terminated = self.cloudapi.terminate_instance(instance_id)
        except:
            terminated = False
        
        # delete node from chef
        node.delete()
        
        # wait for chef solr to catch-up to avoid a search failure
        time.sleep(15.0)
        
        # show the grid
        if terminated:
            add_notice(req, _('%(label)s %(id)s has been deleted.',
                              label=self.label, id=instance_id))
        else:
            add_warning(req,
                _("%(label)s %(id)s (id=%(instance_id)s) was not " + \
                  "terminated as expected, but its chef node was deleted. " + \
                  "Please check in the AWS Management Console directly.",
                  label=self.label, id=id, instance_id=instance_id))
        req.redirect(req.href.cloud(self.name))
