import chef
import json
import os
import time
from timer import Timer

class ChefApi(object):
    """Wraps pychef with several conveniences including:
    
      * search params and result conversion
      * data bag item ordering
      * generalized resource querying
      * generalized resource creation
      * instance data support
    """
    
    def __init__(self, instancedata_file, base_path, log):
        self.instancedata_file = instancedata_file
        self.base_path = base_path or None
        self.chef = chef.autoconfigure(self.base_path)
        self.log = log
        
    def search(self, index, sort=None, asc=1, limit=0, offset=0, q='*:*'):
        """Search the chefserver and return a list of dict items."""
        # setup the params
        if not sort:
            sort = 'X_CHEF_id_CHEF_X'
        sort += asc and ' asc' or ' desc'
        search = chef.search.Search(index, q, sort, limit, offset, self.chef)
        
        # convert rows to resource objects (e.g., nodes)
        rows = []
        for result in search:
            rows.append(result.object)
        return rows, search.total
    
    def resource(self, resource, id=None):
        """Query chef for a resource and return the result as a dict (or
        dict-like) record.  A dict-like record is returned for 'nodes'
        and 'roles' resources which lazy-loads its value."""
        self.log.debug("Querying chef api resource '%s'" % resource)
        if resource == 'nodes':
            if id:
                return chef.node.Node(id, self.chef)
            return chef.node.Node.list(self.chef)
        if resource == 'roles':
            if id:
                return chef.role.Role(id, self.chef)
            return chef.role.Role.list(self.chef)
        if resource == 'data':
            if id:
                return chef.data_bag.DataBag(id, self.chef)
            return chef.data_bag.DataBag.list(self.chef)
#        if resource == 'client':
#            if id:
#                return chef.api_request('GET', '/client/%s' % id)
#            return chef.data_bag.DataBag.list(self.chef)
        raise Exception("Unknown resource '%s'" % resource)
    
    def create(self, resource, id=None):
        """Creates the given chef resource.  If dummy is True, then returns
        a dict with extra 'set_dotted' methods to make compatible with pychef
        classes."""
        class Resource(dict):
            def __init__(self, name):
                self.name = name
            def set_dotted(self, key, value):
                self[key] = value
        if not id:
            return Resource(resource)
        
        if resource == 'nodes':
            return chef.node.Node.create(id, self.chef)
        if resource == 'roles':
            return chef.role.Role.create(id, self.chef)
        if resource == 'data':
            return chef.data_bag.DataBag.create(id, self.chef)
        raise Exception("Unknown resource '%s'" % resource)
    
    def databag(self, bag, id=None):
        """If id is provided, then the specific data bag is returned.
        Else a list of all data items (dicts) in the given data bag
        will be returned.  If a data item has an 'order' field,
        it will be used to order the returned list."""
        databag = chef.data_bag.DataBag(bag, self.chef)
        ids = id and [id] or databag
        
        items = []
        for id in ids:
            # XXX: add a bag.py class to pychef
            item = chef.data_bag.DataBagItem(id, self.chef, parent=databag)
            items.append( (item.get('order',99),item) )
        return [item for (order,item) in sorted(items)]
    
    def get_instance_data(self):
        """Return the instance data for chef-managed instances."""
        f = open(self.instancedata_file,'r')
        data = json.loads(f.read())
        f.close()
        
        # override with ones from chefapi's base path (e.g., for dev)
        if self.base_path:
            # override chef server url
            data['chef_server'] = self.chef.url

            # override validation key
            path = os.path.join(self.base_path,'.chef','validation.pem')
            if os.path.exists(path):
                f = open(path,'r')
                pem = f.read()
                f.close()
                data['validation_key'] = pem
        
        return json.dumps(data)
