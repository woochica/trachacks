from trac.resource import Resource, ResourceNotFound
from trac.util import as_int
from trac.util.presentation import Paginator
from trac.util.text import to_unicode
from trac.web.chrome import Chrome, add_link, add_notice, add_warning
from trac.mimeview import Context
from trac.util.translation import _
import re
import copy
import time
from timer import Timer

class Droplet(object):
    """Generic class for a cloud resource that I'm calling a 'droplet'
    to distinguish it from Trac resources.  Droplets are controllers
    that coordinate trac, chef, and cloud behaviors."""
    
    @classmethod
    def new(cls, env, name, chefapi, cloudapi, field_handlers, boto_field_node_name, log):
        """Return a new droplet instance based on the class name defined
        in the droplet's trac.ini config section - e.g.,
        
          [cloud.instance]
          class = Ec2Instance
        
        where the name param = 'instance'.
        """
        section = 'cloud.%s' % name
        options = dict(env.config.options('cloud'))
        options.update(env.config.options(section))
        cls = globals()[options['class']]
        return cls(name, chefapi, cloudapi, field_handlers, boto_field_node_name, log, options)
    
    def __init__(self, name, chefapi, cloudapi, field_handlers, boto_field_node_name, log, options):
        """Convenience routines for parsing each droplet's config file section
        in trac.ini.  The format of each droplet section is as follows:
        
          [cloud.instance]
          class = Ec2Instance
          title = EC2 Instances
          order = 1
          label = Instance
          fields = name, ec2.instance_type as Instance Type, ohai_time, ..
          crud_resource = nodes
          crud_view = name, ec2.instance_type, ohai_time, ..
          crud_edit = roles
          grid_index = node
          grid_columns = name, ec2.instance_type, ohai_time, ..
          grid_sort = ohai_time
          grid_asc = 0
          grid_group = environment
        
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
        droplet item.  The remaining fields are for querying chef.
        
        The 'crud' option is the url prefix for creating, updating, and
        deleting individual chef resources.  The 'fields' options is used
        to specify display names and/or field handlers.  A dot notation
        can be used to specify nested attributes.  The 'as' notation
        permits defining a field's display name which are extracted into
        a new 'labels' option (a dict).  Field handlers can be used to
        format or convert a field.  For example:
        
          [cloud.instance]
          fields = .., ohai_time_ as Checkin < AgoEpochHandler, ..
          crud_view = .., ohai_time_, ..
        
        This will format the ohai_time attribute (an epoch value) into
        a string like this: "0:01:10 ago".  See handlers.py for all
        available handlers.  Most handlers require that the field name
        *not* be the exact name of an actual node attribute but instead
        be the same name but *suffixed* with one or more underscores
        such as 'ohai_time_' above.  These dynamic field names are the
        ones that should be used in the 'crud_view', 'grid_columns',
        and 'grid_sort' options - the first two being ordered lists of
        fields to display.
        
        The 'grid_index' option is used to search chef for a list of
        resources.  The 'grid_columns' option should list the fields to
        display in order and match those in the 'fields' option to use
        its labels and handlers.  The first column listed in 'columns'
        *must* be the resource's unique primary key.  The 'grid_sort',
        'grid_asc', and 'grid_group' options work as would be expected.
        
        All of the above options are added as attributes to the droplet
        object.
        """
        self.name = name
        self.chefapi = chefapi
        self.cloudapi = cloudapi
        self.boto_field_node_name = boto_field_node_name
        self.log = log
        
        for k,v in options.items():
            if k == 'fields':
                v,labels,handlers = self._extract_fields(v, field_handlers)
                setattr(self, 'labels', labels)
                setattr(self, 'handlers', handlers)
            elif k in ('crud_new','crud_edit'):
                v,readonly,opttype,options = self._extract_crud_config(v)
                setattr(self, k+'_readonly', readonly)
                setattr(self, k+'_opttype', opttype)
                setattr(self, k+'_options', options)
            elif k in ('crud_view','grid_columns'):
                v = [s.strip() for s in v.split(',')]
            setattr(self, k, v)
    
    def _extract_fields(self, s, field_handlers):
        """Convert a string into a three-tuple:
        
         1. a list of fields in defined order
         2. a dict of fields each mapped to its display name
         3. a dict of fields each mapped to its handler
        
        The format of the given string must look like this:
        
          name, created_by as Created By, checkin < OhaiTimeHandler
        
        The above string would return the following three-tuple:
        
         (['name',created_by'],
          {'name':'name','created_by':'Created By'},
          {'checkin':<instance of OhaiTimeHandler>})
        
        In general, the field names for handlers should not exist in
        the row in advance - i.e., create them as needed.
        """
        field_re = re.compile(r"([\w.\-]+)( as ([^,<]+))?( ?< ([^,]+))?")
        fields = []
        display_names = {}
        handlers = {}
        for field,as_,display_name,fh_,handler in field_re.findall(s):
            fields.append(field)
            display_names[field] = display_name.strip() or field
            if handler:
                for fh in field_handlers:
                    if fh.__class__.__name__ == handler:
                         handlers[field] = fh
                         break
        return fields,display_names,handlers
    
    def _extract_crud_config(self, s):
        """Convert a string into a two-tuple:
        
         1. a list of fields in defined order
         2. a list of fields that are marked read-only
        
        The format of the given string must look like this:
        
          name, created_by, created_at*
        
        The above string would return the following three-tuple:
        
         (['name',created_by','created_at'], ['created_at'])
        """
        crud_re = re.compile(r"([\w.\-]+)(\*)?(\|(\|)?([^,]*))?")
        fields = []
        readonly = []
        opttype = {}
        options = {}
        for field,ro,opt,multi,opts in crud_re.findall(s):
            if ro:
                readonly.append(field)
            if opt:
                opttype[field] = multi and 'multiselect' or 'select'
                options[field] = opts and [o.strip() for o in opts.split('|')] \
                                       or []
            fields.append(field)
        return fields,readonly,opttype,options
    
    def handle(self, req, item, fields):
        """Apply handlers to those field's values who have them."""
        for field in fields:
            if field in self.handlers:
                handler = self.handlers[field]
                item.set_dotted(field, handler.convert(req, field, item))
    
    def crud_item(self, req, fields, id=None):
        """Return a node overlaying any request params on top
        of any chef attributes for the given set of fields."""
        item = self.chefapi.create(self.crud_resource)
        if id:
            item = self.chefapi.resource(self.crud_resource, id)
        self.handle(req, item, fields)
        for field in fields:
            value = req.args.get(field,item.get(field,''))
            item.set_dotted(field, value)
        return item
    
    def render_grid(self, req):
        """Retrieve the droplets and pre-process them for rendering."""
        index = self.grid_index
        columns = self.grid_columns
        id_col = columns[0]
        
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
                'columns': self.grid_columns,
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
        for idx, col in enumerate(self.grid_columns):
            header = {
                'col': col,
                'title': self.labels.get(col,col),
                'hidden': False,
                'asc': None,
            }

            if col == sort:
                header['asc'] = asc

            header_group = header_groups[-1]
            header_group.append(header)
        
        # Structure the rows and cells:
        #  - group rows according to __group__ value, if defined
        #  - group cells the same way headers are grouped
        row_groups = []
        authorized_results = [] 
        prev_group_value = None
        for row_idx, result in enumerate(rows):
            col_idx = 0
            cell_groups = []
            row = {'cell_groups': cell_groups}
            for header_group in header_groups:
                cell_group = []
                for header in header_group:
                    col = header['col']
                    if col in self.handlers:
                        handler = self.handlers[col]
                        value = handler.convert(req, col, result)
                    else:
                        value = self._cell_value(result.get(col))
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
            authorized_results.append(result)
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
    
    def render_create(self, req):
        pass
    
    def render_view(self, req, id):
        req.perm.require('CLOUD_VIEW')
        item = self.chefapi.resource(self.crud_resource, id)
        self.handle(req, item, self.crud_view)
        
        data = {
            'title': _('%(label)s %(id)s', label=self.label, id=id),
            'action': 'view',
            'droplet_name': self.name,
            'id': id,
            'label': self.label,
            'fields': self.crud_view,
            'labels': self.labels,
            'item': item,
            'error': req.args.get('error')}
        
        return 'droplet_view.html', data, None
    
    def render_edit(self, req, id):
        data = {
            'droplet_name': self.name,
            'id': id,
            'label': self.label,
            'labels': self.labels,
            'item': self.crud_item(req, self.crud_new, id),
            'error': req.args.get('error')}
        
        # check if creating or editing
        if id:
            req.perm.require('CLOUD_MODIFY')
            data.update({
                'title': _('Edit  %(label)s %(id)s', label=self.label, id=id),
                'button': _('Save %(label)s', label=self.label),
                'action': 'edit',
                'fields': self.crud_edit,
                'readonly': self.crud_edit_readonly,
                'opttype': self.crud_edit_opttype,
                'options': self._get_options(self.crud_edit_options)})
        else:
            req.perm.require('CLOUD_CREATE')
            data.update({
                'title': _('Create New %(label)s', label=self.label),
                'button': _('Create %(label)s', label=self.label),
                'action': 'new',
                'fields': self.crud_new,
                'readonly': self.crud_new_readonly,
                'opttype': self.crud_new_opttype,
                'options': self._get_options(self.crud_new_options)})
        
        return 'droplet_edit.html', data, None
    
    def _get_options(self, crud_options):
        """.. data bag .."""
        options = {}
        for field,opts in crud_options.items():
            if not opts:
                try:
                    name = field.replace('.','_')
                    bag = self.chefapi.databag(name)
                    opts = [(rec['name'],rec['value']) for rec in bag]
                except:
                    self.log.debug("Could not access databag %s" % name)
            else:
                opts = [(v,v) for v in opts]
            options[field] = opts
        return options
    
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
    
    def _cell_value(self, v):
        """Normalize a cell value for display.
        >>> (cell_value(None), cell_value(0), cell_value(1), cell_value('v'))
        ('', '0', u'1', u'v')
        """
        return v is 0 and '0' or v and unicode(v) or ''
    

class Ec2Instance(Droplet):
    """An EC2 instance cloud droplet."""
    
    def render_edit(self, req, id):
        template, data, content_type = Droplet.render_edit(self, req, id)
        
        # handle run_lists as special case (they're not normal item attributes)
        if id:
            item = self.chefapi.resource(self.crud_resource, id)
            self.handle(req, item, self.crud_edit_options)
            item_roles = [r.strip() for r in item['run_list_'].split(',')]
            data['item']['run_list_'] = item_roles
        roles = self.chefapi.resource('roles')
        data['options']['run_list_'] = sorted([(r,r) for r in roles])
        return template, data, content_type
    
    def create(self, req):
        req.perm.require('CLOUD_CREATE')
        instance_data = self.chefapi.get_instance_data()
        
        # launch instance (and wait until running)
        now = time.time()
        instance = self.cloudapi.launch_instance(
            image_id = req.args.get('ec2.ami_id'),
            instance_type = req.args.get('ec2.instance_type'),
            placement = req.args.get('ec2.placement_availability_zone'),
            user_data = instance_data,
            timeout=300)
        if instance.state == 'pending':
            add_warning(req,
                _("%(label)s %(id)s was created but isn't (yet) running. " + \
                  "Please check in the AWS Management Console directly.",
                  label=self.label, id=instance.id))
            req.redirect(req.href.cloud(self.name))
        
        # The pre-installed chef-client config uses the instance id as the
        # node name - which is what we're assuming is being used here.
        # However, some chef setups allow for changing the node name post-
        # launch.  The boto_field_node_name option should be set to the
        # *final* expected chef node name.  If it's not set to the instance
        # id (the expected initial node name), then we'll do a little dance
        # to create the new node with the newly expected node name and
        # delete the old (instance id) node name from chef.
        if not self.boto_field_node_name or self.boto_field_node_name == 'id':
            add_notice(req, _('%(label)s %(id)s has been created.',
                          label=self.label, id=instance.id))
            req.redirect(req.href.cloud(self.name, instance.id))
        
        # start the dance of creating new node and deleting old one
        id = getattr(instance, self.boto_field_node_name)
        
        try:
            # create a new chef node
            node = self.chefapi.create(self.crud_resource, id)
            self.log.info("Added new chef node %s (id=%s)" % (id,instance.id))
        except chef.exceptions.ChefServerError, e:
            if e.code != 409:
                raise
            # node already exists so get it in finally block
        finally:
            timer = Timer(15) # 15 seconds
            while timer.running:
                try:
                    node = self.chefapi.resource(self.crud_resource, id)
                    break
                except chef.exceptions.ChefServerError, e:
                    if e.code != 404: # can take time for solr to be updated
                        raise
                finally:
                    time.sleep(1.0)
            else:
                add_warning(req,
                    _("Unable to save %(label)s %(id)s. " + \
                      "Please check in the AWS Management Console directly.",
                      label=self.label, id=id))
                req.redirect(req.href.cloud(self.name))
        
        # save the run_list and fields
        fields = set(self.crud_new + ['created_at','created_by'])
        req.args['created_at'] = now
        req.args['created_by'] = req.args.get('created_by',req.authname)
        self.save(req, id, list(fields), redirect=False)
        
        # now wait until the new node has checked in to chefserver
        timer = Timer(12 * 60) # 12 minutes
        while timer.running:
            try:
                node = self.chefapi.resource(self.crud_resource, id)
                if node.get('ec2.public_hostname'):
                    break # cool, this means that the node has checked in
            except chef.exceptions.ChefServerError, e:
                if e.code != 404: # can take time for solr to be updated
                    raise
            finally:
                time.sleep(2.0)
        
        # can now delete the old node (if it exists)
        try:
            node = self.chefapi.resource(self.crud_resource, instance.id)
            node.delete()
            self.log.info("Deleted old node %s" % instance.id)
        except:
            pass
        
        # show the view
        add_notice(req, _('%(label)s %(id)s has been created.',
                          label=self.label, id=instance.id))
        req.redirect(req.href.cloud(self.name, id))
    
    def save(self, req, id, fields=None, redirect=True):
        req.perm.require('CLOUD_MODIFY')
        node = self.chefapi.resource(self.crud_resource, id)
        
        # prepare fields; remove automatic and dynamic fields
        if fields is None:
            fields = self.crud_edit
        fields = [f for f in fields
                  if not f.startswith('ec2.') or f.endswith('_')]
        for field in fields:
            node.set_dotted(field, req.args.get(field,''))
        
        # special handle run_list_
        roles = req.args.get('run_list_','')
        run_list = ["role[%s]" % r.strip() for r in roles.split(',')]
        node.run_list = run_list
        node.save()
        
        if redirect:
            # show the view
            add_notice(req, _('%(label)s %(id)s has been saved.',
                              label=self.label, id=id))
            req.redirect(req.href.cloud(self.name, id))
        
    def delete(self, req, id):
        req.perm.require('CLOUD_DELETE')
        node = self.chefapi.resource(self.crud_resource, id)
        instance_id = node.get('ec2.instance_id')
        
        # delete ec2 instance
        try:
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
