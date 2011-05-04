import re

KINDS = ('text','checkbox','select','multiselect')

class Fields(object):
    """Manages the data conversion of fields into and out of views from
    PyChef objects and web request objects.  Fields are configured in
    trac.ini."""
    
    def __init__(self, options, handlers, chefapi, log, prefix='field.'):
        """The Droplet class handles part of a droplet's configuration,
        and this Fields class handles the rest - namely, processing a
        chef resource's fields.  The trac.ini configuration below is
        passed into this init as a dict of options:
        
          [cloud.instance]
          ..
          field.name = text
          field.name.label = Name
          field.name.handler = NameHandler
          field.run_list = multiselect
          field.run_list.label = Roles
          field.run_list.databag = roles  # special token
          field.run_list.handler = RunListHandler
          field.ec2.placement_availability_zone = select
          field.ec2.placement_availability_zone.label = Availability Zone
          field.ec2.placement_availability_zone.options = \
            No preference|us-east-1a|us-east-1b|us-east-1c|us-east-1d
          field.ec2.placement_availability_zone.value = us-east-1c
          
          .. many more fields ..
        
        The field.* options are defined much like Trac custom fields
        and each should map exactly to its chef attribute name.  For
        example, 'ec2.placement_availability_zone' maps to the 'ec2'
        attribute namespace and the 'placement_availability_zone'
        attribute within that namespace.  In the example above, it's
        defined as a select field with a display label and several
        options separated by a pipe (|) just like Trac custom fields.
        There are some important differences to Trac custom fields,
        however:
        
         * A field can define a databag instead of options
         * A field can define a "field handler"
        
        DATA BAGS FOR OPTIONS
        ---------------------
        You may prefer to define a select (or multiselect) field's
        options by using a chef data bag instead of listing them in
        the trac.ini file.  For example, a field defined like this:
        
          [cloud.instance]
          ..
          field.ec2.ami_id = select
          field.ec2.ami_id.label = Image ID
          field.ec2.ami_id.databag = ec2_ami_id

        Will query for and use the 'ec2_ami_id' data bag items.  The
        individual data bag items should be formatted like this:
        
          {
            "id": "ami-xxxxxxxx",
            "value": "ami-xxxxxxxx",
            "name": "ami-xxxxxxxx (64-bit)",
            "order": 1
          }
        
        The 'name' will be used as the option's displayed name and
        the 'value' will be used as the option's value. If an 'order'
        field is provided, it will be used to order the options
        accordingly (much like custom field ordering).
        
        Specifying 'roles' as a databag has a special meaning - chef
        will be queried for the list of roles instead of a data bag.
        
        FIELD HAMDLERS
        --------------
        A field handler converts a raw chef attribute value into
        something more human-readable and vice-versa.  For example,
        the 'RunListHandler' defined above for the 'run_list' field
        extracts roles from a chef node's run_list and displays them
        in an easy-to-read way.  It also converts data the other
        direction - i.e., it converts the list of roles from a web
        form into the correct format to set the node's run_list.
        
        Other examples include displaying a url to a web site at a
        specific port, converting epoch's to dates and times, etc.
        See handlers.py for the full list of provided field handlers
        and defaults.py for examples of which fields they're used for
        by default
        
        VIEWS
        -----
        In addition to field definitions, you can define which fields
        should be viewed in which views, their order, and whether or
        not a field should be read-only in that view.  Example:
        
          [cloud.instance]
          ..
          crud_resource = nodes
          crud_view = name, ec2.instance_type, ohai_time, ..
          crud_new = roles, created_by, created_at, ..
          crud_edit = roles, created_by, created_at*, ..
          
          grid_index = node
          grid_columns = name, ec2.instance_type, ohai_time, ..
          grid_sort = ohai_time
          grid_asc = 0
        
        ("crud" stands for "create, read, update, delete".)
        
        The crud_resource option defines the chef resource for this
        droplet.  The grid_index option defines the chef search index
        for this droplet.  Refer to the Chef Server API documentation
        for the complete list:
        
        http://wiki.opscode.com/display/chef/Server+API#ServerAPI-Clients
        
        The crud_view, crud_new, crud_edit, and grid_columns options
        are lists of field names in the order to be displayed in their
        respective views.  An asterisk ('*') appended to a field name
        (only applicable for crud_new and crud_edit) indicates that
        the field should be read-only in that view.  All fields in
        the crud_new and crud_edit views will be used to set or update
        the chef resource item.
        
        The grid_sort and grid_asc are for default sorting in the grid
        view.
        """
        self._log = log
        self._fields = {}
        self._lists = {}
        
        # find all of the keys of fields
        keys = [o for o,v in options.items()
                if o.startswith(prefix) and v in KINDS]
        
        # create all name objects and populate
        for key in keys:
            name = key[len(prefix):]
            kind = options.get(key,'text')
            label = options.get(key+'.label',name)
            opts = options.get(key+'.options','')
            opts = opts and opts.split('|') or []
            databag = options.get(key+'.databag')
            default = options.get(key+'.value','')
            handler_name = options.get(key+'.handler','DefaultHandler')
            for h in handlers:
                if h.__class__.__name__ == handler_name:
                    handler = h
                    break
            else:
                raise Exception("Field handler '%s' not found" % handler_name)
            self._fields[name] = Field(
                name,kind,label,opts,databag,default,handler,chefapi,log)
    
    def __getitem__(self, field_name):
        return self._fields[field_name]
    
    def set_list(self, list_name, field_names):
        """Extract a list of fields from the field_names string and add it
        to the collection.  Field names postfixed with an asterisk (*) are
        tagged as read-only."""
        self._lists[list_name] = []
        for field_name in [f.strip() for f in field_names.split(',')]:
            if field_name.endswith('*'):
                field_name = field_name.rstrip('*')
                self._fields[field_name].add_readonly(list_name)
            self._lists[list_name].append(field_name)
    
    def get_list(self, list_name, filter=None):
        """Returns a list of fixed field objects for the given list_name.
        A filter regex can be provided to filter on the field's name."""
        fields = []
        for field_name in self._lists[list_name]:
            if filter and re.compile(filter).match(field_name):
                continue
            field = self._fields[field_name].fix(list_name)
            fields.append(field)
        return fields


class Field(object):
    
    def __init__(self,name,kind,label,opts,databag,default,handler,chefapi,log):
        self.name = name
        self.kind = kind
        self.label = label
        self._opts = opts
        self._databag = databag
        self._default = default
        self._handler = handler
        self._chefapi = chefapi
        self._log = log
        self._readonly = []
        self._list_name = None
    
    def add_readonly(self, list_name):
        """Adds the list list_name to the readonly list."""
        self._readonly.append(list_name)
    
    def is_readonly(self, list_name):
        return list_name in self._readonly
    
    def fix(self, list_name):
        """Returns a copy of this field fixed to a field list."""
        return FixedField(self, list_name)
    
    @property
    def options(self):
        """Return a list of (name,value) tuples of the field's list of
        options.  If an explicit list was provided in the config file,
        then that will be returned; else if a data bag was provided,
        its contents will be returned.  The special databags are:
        
         * roles - returns the roles as options
         * nodes - returns the nodes as options
        """
        if self._opts:
            return [(o,o) for o in self._opts]
        if not self._databag:
            self._log.debug("No options provided for field %s" % self.name)
            return []
        
        # get options from databag
        opts = []
        try:
            if self._databag.startswith('roles'):
                # handle special case
                roles = self._chefapi.resource('roles')
                opts = sorted([(r,r) for r in roles])
            elif self._databag.startswith('nodes'):
                # handle special case
                if ':' in self._databag:
                    name,value = self._databag.split(':')[1:3]
                else:
                    name = value = 'ec2.instance_id'
                nodes,u_total = self._chefapi.search('node')
                opts = [('','')]
                for node in nodes:
                    try:
                        opts.append( (node.attributes.get_dotted(name),
                                      node.attributes.get_dotted(value)) )
                    except KeyError:
                        pass # skip nodes with missing keys
                opts.sort()
            else:
                bag = self._chefapi.databag(self._databag)
                opts = [(rec['name'],rec['value']) for rec in bag]
        except Exception, e:
            self._log.debug("Could not access databag '%s'\n%s" % \
                            (self._databag,str(e)))
        return opts
    
    def get(self, item=None, req=None, default=None, raw=False):
        """Returns the given key's value from the given PyChef object
        using dotted notation.  If raw is False, then the defined field
        handler will be used to convert the raw value into a new format,
        else the raw value is returned.  If the key is not found in the
        item, then a default value is returned; if default is None, then
        the field's originally instantiated default value is used.  If
        the item is None, then data is extracted from only the request
        object."""
        def get_default():
            if default is None:
                return self._default
            else:
                return default
        
        try:
            if raw is False:
                v = self._handler.convert_item(self.name, item, req)
            else:
                if item:
                    if hasattr(item.attributes, 'get_dotted'):
                        v = item.attributes.get_dotted(self.name)
                    else:
                        v = item[self.name]
                else:
                    v = req.args.get(self.name,get_default())
        except (KeyError, AttributeError):
            v = get_default()
        return v is 0 and '0' or isinstance(v,str) and unicode(v) or v
    
    def set(self, item, req, default='', raw=False):
        """Sets the given key's value in the given PyChef object using
        dotted notation by extracting the same field name from the req
        param. If the key is not found in args, then the default value
        is used.  The 'run_list' field is handled as a special case."""
        if raw is False:
            v = self._handler.convert_req(self.name, req)
            
            # special handle run_list
            if self.name == 'run_list':
                item.run_list = v
                self._log.debug("Item %s field run_list set to %s" % (item,v))
                return
        else:
            v = req.args.get(self.name,default)
        if hasattr(item.attributes, 'set_dotted'):
            item.attributes.set_dotted(self.name, v)
        else:
            item[self.name] = v
        self._log.debug("Item %s field %s set to %s" % (item,self.name,v))
    
    def set_dict(self, d, req, default='', raw=False):
        """Sets the given key's value in the given dict object by
        extracting the same field name from the req param. If the key
        is not found in args, then the default value is used."""
        if raw is False:
            v = self._handler.convert_req(self.name, req)
        else:
            v = req.args.get(self.name,default)
        d[self.name] = v
    
    def __str__(self):
        return self.name


class FixedField(Field):
    """A field that is fixed to a specific list."""
    
    def __init__(self, field, list_name):
        self.name = field.name
        self.kind = field.kind
        self.label = field.label
        self._opts = field._opts
        self._databag = field._databag
        self._default = field._default
        self._handler = field._handler
        self._chefapi = field._chefapi
        self._log = field._log
        self._readonly = list_name in field._readonly
    
    @property
    def readonly(self):
        return self._readonly
    
    def add_readonly(self, list_name):
        raise Exception("Cannot add a list to a fixed field.")
    
    def is_readonly(self, list_name):
        raise Exception("Use readonly attribute instead.")
    
    def fix(self, list_name):
        raise Exception("Field is already fixed to a list.")
