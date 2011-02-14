from subprocess import Popen, STDOUT, PIPE
import os
import chef

class ChefApi(object):
    """Wraps pychef with several conveniences including:
    
      * search params and result conversion
      * data bag item ordering
      * generalized resource querying
      * generalized resource creation
      * ec2 instance bootstrapping
    """
    
    def __init__(self, base_path, keypair_pem, user, boot_run_list, sudo, log):
        self.base_path = os.path.abspath(base_path)
        self.keypair_pem = keypair_pem
        self.user = user
        self.boot_run_list = boot_run_list
        self.sudo = sudo
        self.log = log
        self.chef = chef.autoconfigure(self.base_path)
        
    def search(self, index, sort=None, asc=1, limit=0, offset=0, q='*:*'):
        """Search the chefserver and return a list of dict items."""
        # setup the params
        if not sort:
            sort = 'X_CHEF_id_CHEF_X'
        sort += asc and ' asc' or ' desc'
        search = chef.search.Search(index, q, sort, limit, offset, self.chef)
        self.log.debug("About to query chef at %s" % search.url)
        
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
        if resource == 'clients':
            if id:
                return chef.client.Client(id, self.chef)
            return chef.client.Client.list(self.chef)
        raise Exception("Unknown resource '%s'" % resource)
    
    def create(self, resource, id):
        """Creates the given chef resource."""
        if resource == 'nodes':
            return chef.node.Node.create(id, self.chef)
        if resource == 'roles':
            return chef.role.Role.create(id, self.chef)
        if resource == 'data':
            return chef.data_bag.DataBag.create(id, self.chef)
        if resource == 'clients':
            return chef.client.Client.create(id, self.chef)
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
            item = chef.data_bag.DataBagItem(bag, id, self.chef)
            items.append( (item.get('order',99),item) )
        return [item for (order,item) in sorted(items)]
    
    def bootstrap(self, id, hostname, timeout=300):
        """Bootstraps an ec2 instance by calling out to "knife bootstrap".
        The result should be that the ec2 instance connects with the
        chefserver.  Any run_list provided will get run upon the initial
        bootstrap."""
        cmd = '/usr/bin/knife bootstrap %s' % hostname
        cmd += ' -c %s' % os.path.join(self.base_path,'knife.rb')
        cmd += ' -x %s' % self.user
        if self.keypair_pem:
            cmd += ' -i %s' % self.keypair_pem
        if self.boot_run_list:
            cmd += ' -r %s' % ','.join(r for r in self.boot_run_list)
        if self.sudo:
            cmd += ' --sudo'
        self.log.debug('Bootstrapping %s with command: %s' % (id,cmd))
        p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
        # TODO: handle/add timeout
        out = unicode(p.communicate()[0], 'utf-8', 'ignore')
        
        if p.returncode != 0:
            self.log.info('Error bootstrapping ec2 instance %s:\n%s' % (id,out))
            return None
        
        self.log.info('Bootstrapped %s (id=%s):\n%s' % (hostname,id,out))
        return chef.node.Node(id, self.chef)
